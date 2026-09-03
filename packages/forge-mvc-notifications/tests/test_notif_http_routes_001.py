"""`NOTIF-HTTP-ROUTES-001` — les notifications s'exposent en HTTP.

Le paquet savait écrire une notification et la relire depuis Python. Il
n'exposait **aucune route**, là où `forge-mvc-video` livre
`register_video_routes` et `forge-mvc-iot` livre `register_iot_routes`.

Chaque application devait donc écrire son contrôleur, sa sérialisation et son
compteur de non-lus avant d'afficher quoi que ce soit. Mesuré sur une
application réelle : elle appelait `notify()` depuis des mois et n'avait jamais
affiché une seule notification, ayant buté sur cette marche manquante.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

pytest.importorskip("forge_mvc_notifications")

from forge_mvc_notifications.errors import NotificationError  # noqa: E402
from forge_mvc_notifications.http import (  # noqa: E402
    DEFAULT_PAGE_SIZE,
    ROUTE_LIST,
    ROUTE_MARK_ALL_READ,
    ROUTE_MARK_READ,
    ROUTE_UNREAD_COUNT,
    NotificationHttpController,
    register_notification_routes,
    serialize_notification,
)
from forge_mvc_notifications.store import (  # noqa: E402
    Notification,
    _mark_read_sql,
    mark_read,
)


class _Db:
    """Magasin en mémoire, aux mêmes requêtes que le vrai."""

    def __init__(self, lignes: "list[dict[str, Any]] | None" = None) -> None:
        self.lignes: "list[dict[str, Any]]" = lignes if lignes is not None else [
            {"id": 1, "recipient": "professeur.42", "type": "copie_a_corriger",
             "message": "Durand a rendu une copie", "data": "{}", "read_at": None,
             "created_at": "2026-09-03", "target_url": None},
            {"id": 2, "recipient": "professeur.7", "type": "info",
             "message": "notification d'un autre", "data": "{}", "read_at": None,
             "created_at": "2026-09-03", "target_url": None},
        ]

    def fetch_all(self, sql: str, params: Any) -> "list[dict[str, Any]]":
        return [dict(l) for l in self.lignes if l["recipient"] == params[0]]

    def fetch_one(self, sql: str, params: Any) -> "dict[str, Any]":
        return {"n": sum(
            1 for l in self.lignes
            if l["recipient"] == params[0] and l["read_at"] is None
        )}

    def execute(self, sql: str, params: Any) -> int:
        touchees = 0
        for ligne in self.lignes:
            if ligne["read_at"] is not None:
                continue
            if "recipient = ?" in sql and "id = ?" in sql:
                if ligne["id"] == params[0] and ligne["recipient"] == params[1]:
                    ligne["read_at"] = "lu"
                    touchees += 1
            elif "id = ?" in sql:
                if ligne["id"] == params[0]:
                    ligne["read_at"] = "lu"
                    touchees += 1
            elif ligne["recipient"] == params[0]:
                ligne["read_at"] = "lu"
                touchees += 1
        return touchees


class _Req:
    def __init__(self, **kw: Any) -> None:
        self._kw = kw

    def query(self, nom: str, defaut: Any = None) -> Any:
        return self._kw.get(nom, defaut)

    def route(self, nom: str) -> Any:
        return self._kw.get(nom)


@pytest.fixture
def db() -> _Db:
    return _Db()


@pytest.fixture
def prof42(db: _Db) -> NotificationHttpController:
    return NotificationHttpController(lambda r: "professeur.42", db=db)


def _corps(reponse: Any) -> "dict[str, Any]":
    return json.loads(reponse.body)


# ─────────────────────────────────────────────────────────────────────────────
# Le destinataire vient de la session, jamais de la requête
# ─────────────────────────────────────────────────────────────────────────────


class TestResolveurObligatoire:

    def test_sans_resolveur_l_enregistrement_leve(self) -> None:
        """Une application qui monte ces routes sans résolveur a fait une
        erreur de câblage, et la découvrir au démarrage vaut mieux qu'en
        production."""
        class _Router:
            def add(self, *a: Any, **k: Any) -> None:
                raise AssertionError("aucune route ne doit être posée")

        with pytest.raises(NotificationError, match="recipient_of"):
            register_notification_routes(_Router())

    def test_le_message_dit_pourquoi(self) -> None:
        class _Router:
            def add(self, *a: Any, **k: Any) -> None: ...

        with pytest.raises(NotificationError, match="n'importe qui"):
            register_notification_routes(_Router())

    def test_aucune_route_ne_lit_un_destinataire_en_parametre(self) -> None:
        """Accepter `?recipient=professeur.7` donnerait à quiconque les
        notifications de n'importe qui. C'est la première chose qu'on écrit
        quand on veut aller vite."""
        import inspect

        from forge_mvc_notifications import http as module

        source = inspect.getsource(module.NotificationHttpController)

        assert 'query(request, "recipient"' not in source
        assert '"recipient"' not in source.split("def _recipient")[1].split("def ")[1]


class TestSessionAbsenteOuCassee:

    def test_sans_session_c_est_401(self, db: _Db) -> None:
        anonyme = NotificationHttpController(lambda r: None, db=db)

        assert anonyme.unread_count(_Req()).status == 401
        assert anonyme.list(_Req()).status == 401
        assert anonyme.mark_read(_Req(id="1")).status == 401
        assert anonyme.mark_all_read(_Req()).status == 401

    def test_un_destinataire_vide_vaut_absence(self, db: _Db) -> None:
        vide = NotificationHttpController(lambda r: "   ", db=db)

        assert vide.unread_count(_Req()).status == 401

    def test_un_resolveur_qui_leve_refuse(self, db: _Db) -> None:
        """Une session mal formée ne doit pas rendre 500, et surtout ne doit
        pas ouvrir l'accès."""
        def _casse(request: Any) -> str:
            raise RuntimeError("session illisible")

        casse = NotificationHttpController(_casse, db=db)

        assert casse.unread_count(_Req()).status == 401

    def test_un_resolveur_qui_rend_autre_chose_qu_une_chaine_refuse(
        self, db: _Db
    ) -> None:
        bizarre = NotificationHttpController(lambda r: 42, db=db)  # type: ignore[arg-type,return-value]

        assert bizarre.unread_count(_Req()).status == 401


# ─────────────────────────────────────────────────────────────────────────────
# Isolation entre destinataires
# ─────────────────────────────────────────────────────────────────────────────


class TestIsolation:

    def test_on_ne_lit_que_les_siennes(
        self, prof42: NotificationHttpController
    ) -> None:
        corps = _corps(prof42.list(_Req()))
        messages = [n["message"] for n in corps["data"]["notifications"]]

        assert messages == ["Durand a rendu une copie"]

    def test_le_compteur_ne_compte_que_les_siennes(
        self, prof42: NotificationHttpController
    ) -> None:
        assert _corps(prof42.unread_count(_Req()))["data"]["count"] == 1

    def test_marquer_celle_d_un_autre_ne_fait_rien(
        self, prof42: NotificationHttpController, db: _Db
    ) -> None:
        """L'identifiant seul suffirait sinon à faire disparaître l'alerte de
        quelqu'un d'autre."""
        reponse = prof42.mark_read(_Req(id="2"))

        assert _corps(reponse)["data"]["marked"] is False
        assert db.lignes[1]["read_at"] is None

    def test_marquer_la_sienne_fonctionne(
        self, prof42: NotificationHttpController, db: _Db
    ) -> None:
        assert _corps(prof42.mark_read(_Req(id="1")))["data"]["marked"] is True
        assert db.lignes[0]["read_at"] is not None

    def test_tout_marquer_ne_touche_pas_les_autres(
        self, prof42: NotificationHttpController, db: _Db
    ) -> None:
        prof42.mark_all_read(_Req())

        assert db.lignes[0]["read_at"] is not None
        assert db.lignes[1]["read_at"] is None

    def test_le_sql_borne_est_bien_borne(self) -> None:
        assert "recipient = ?" in _mark_read_sql(scoped=True)
        assert "recipient" not in _mark_read_sql()

    def test_mark_read_borne_refuse_un_destinataire_vide(self) -> None:
        with pytest.raises(NotificationError):
            mark_read(1, recipient="  ", db=_Db())


# ─────────────────────────────────────────────────────────────────────────────
# Sérialisation
# ─────────────────────────────────────────────────────────────────────────────


class TestSerialisation:

    def _une(self) -> Notification:
        return Notification(
            id=7, recipient="professeur.42", type="copie_a_corriger",
            message="Durand a rendu une copie", data={"progression_seance_id": 3},
            read=False, created_at="2026-09-03", target_url="/copies/3",
        )

    def test_le_destinataire_n_est_pas_rendu(self) -> None:
        """Le client ne reçoit que les siennes : le lui répéter n'apprend rien
        et expose la convention de nommage interne de l'application."""
        assert "recipient" not in serialize_notification(self._une())

    def test_les_champs_utiles_y_sont(self) -> None:
        rendu = serialize_notification(self._une())

        assert rendu["id"] == 7
        assert rendu["type"] == "copie_a_corriger"
        assert rendu["data"] == {"progression_seance_id": 3}
        assert rendu["target_url"] == "/copies/3"
        assert rendu["read"] is False


# ─────────────────────────────────────────────────────────────────────────────
# Pagination et paramètres
# ─────────────────────────────────────────────────────────────────────────────


class TestParametres:

    @pytest.mark.parametrize("limite", ["beaucoup", "1.5", "-1", "0"])
    def test_une_limite_illisible_est_une_erreur(
        self, prof42: NotificationHttpController, limite: str
    ) -> None:
        """La remplacer en silence par le défaut rendrait une page que
        l'appelant n'a pas demandée."""
        assert prof42.list(_Req(limit=limite)).status == 400

    def test_une_limite_au_dela_du_plafond_est_refusee(
        self, prof42: NotificationHttpController
    ) -> None:
        assert prof42.list(_Req(limit="100000")).status == 400

    def test_un_curseur_illisible_est_une_erreur(
        self, prof42: NotificationHttpController
    ) -> None:
        assert prof42.list(_Req(before_id="hier")).status == 400

    def test_sans_parametre_la_page_par_defaut_repond(
        self, prof42: NotificationHttpController
    ) -> None:
        assert prof42.list(_Req()).status == 200

    def test_le_curseur_est_absent_quand_la_page_n_est_pas_pleine(
        self, prof42: NotificationHttpController
    ) -> None:
        """Rendre un curseur ferait demander une page vide."""
        assert _corps(prof42.list(_Req()))["data"]["next_before_id"] is None

    def test_le_curseur_est_rendu_quand_la_page_est_pleine(self) -> None:
        lignes = [
            {"id": i, "recipient": "p.1", "type": "info", "message": f"m{i}",
             "data": "{}", "read_at": None, "created_at": "2026-09-03",
             "target_url": None}
            for i in range(1, 4)
        ]
        controleur = NotificationHttpController(lambda r: "p.1", db=_Db(lignes))

        corps = _corps(controleur.list(_Req(limit="3")))

        assert corps["data"]["next_before_id"] == 3

    def test_la_taille_par_defaut_reste_celle_d_un_panneau(self) -> None:
        """En rendre cinquante ferait payer à chaque interrogation une liste
        que personne ne déroule."""
        assert DEFAULT_PAGE_SIZE == 20


# ─────────────────────────────────────────────────────────────────────────────
# Câblage
# ─────────────────────────────────────────────────────────────────────────────


class TestRoutes:

    def _posees(self) -> "list[tuple[str, str, dict[str, Any]]]":
        posees: "list[tuple[str, str, dict[str, Any]]]" = []

        class _Router:
            def add(self, methode: str, chemin: str, handler: Any, **kw: Any) -> None:
                posees.append((methode, chemin, kw))

        register_notification_routes(
            _Router(), recipient_of=lambda r: "professeur.42"
        )
        return posees

    def test_les_quatre_routes_sont_posees(self) -> None:
        chemins = [(m, c) for m, c, _ in self._posees()]

        assert ("GET", ROUTE_UNREAD_COUNT) in chemins
        assert ("GET", ROUTE_LIST) in chemins
        assert ("POST", ROUTE_MARK_READ) in chemins
        assert ("POST", ROUTE_MARK_ALL_READ) in chemins

    def test_les_mutations_gardent_le_csrf(self) -> None:
        """Un appel HTMX doit porter le jeton."""
        mutations = [kw for m, _, kw in self._posees() if m == "POST"]

        assert mutations
        assert all(kw.get("csrf", True) is not False for kw in mutations)

    def test_aucune_route_n_est_publique(self) -> None:
        """Le routeur exige une session, et le résolveur exige en plus qu'elle
        désigne quelqu'un."""
        assert all(kw.get("public", False) is False for _, _, kw in self._posees())

    def test_elles_sont_annoncees_comme_api(self) -> None:
        assert all(kw.get("api") is True for _, _, kw in self._posees())


class TestCoherenceAvecLesAutresPaquets:

    def test_le_paquet_expose_son_enregistrement_comme_video_et_iot(self) -> None:
        """C'était l'incohérence : deux paquets livrent leurs routes, celui ci
        n'en livrait aucune."""
        import forge_mvc_notifications as module

        assert "register_notification_routes" in module.__all__
