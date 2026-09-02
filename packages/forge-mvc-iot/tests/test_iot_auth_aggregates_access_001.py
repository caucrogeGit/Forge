"""`IOT-DEVICE-AUTH-001`, `IOT-AGGREGATES-001` et `IOT-RBAC-READ-001`.

Le défaut le plus lourd du paquet tenait en une phrase : l'API de lecture
n'avait **qu'un** jeton, qui donnait accès à toutes les mesures de tous les
sites. Un prestataire chargé des capteurs d'un bâtiment lisait par là les
mesures des autres, sans qu'aucun mécanisme ne l'en empêche ni ne le signale.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest

from forge_mvc_iot.access import (
    ACTION_READ_AGGREGATES,
    ACTION_READ_EVENTS,
    IOT_ACTIONS,
    clear_iot_permission_checks,
    is_read_allowed,
    register_iot_permission_check,
    registered_permission_checks,
    unregister_iot_permission_check,
)
from forge_mvc_iot.aggregates import (
    MAX_WINDOW_HOURS,
    IotAggregate,
    IotAggregateError,
    aggregate_for_device,
    aggregate_for_site,
    select_aggregate_sql,
    window_start,
)
from forge_mvc_iot.storage.repository import select_iot_events_scoped_sql
from forge_mvc_iot.tokens import (
    GLOBAL_SCOPE,
    TOKEN_PREFIX,
    IotScope,
    IotTokenError,
    IotTokenRepository,
    generate_token,
    hash_token,
    looks_like_token,
)


# ------------------------------------------------------- IOT-DEVICE-AUTH


class TestPortee:

    def test_le_jeton_global_ouvre_tout(self) -> None:
        assert GLOBAL_SCOPE.allows("batA", "c1")
        assert GLOBAL_SCOPE.allows("batB", "c9")
        assert GLOBAL_SCOPE.is_global

    def test_un_jeton_de_site_ne_lit_pas_un_autre_site(self) -> None:
        """Le défaut que ce ticket corrige."""
        portee = IotScope(site="batA")

        assert portee.allows("batA", "c1")
        assert not portee.allows("batB", "c1")

    def test_un_jeton_d_equipement_ne_lit_que_le_sien(self) -> None:
        portee = IotScope(site="batA", device_id="c1")

        assert portee.allows("batA", "c1")
        assert not portee.allows("batA", "c9")

    def test_un_jeton_d_equipement_refuse_une_lecture_de_site(self) -> None:
        """« Toutes les mesures du site » n'est pas une réponse acceptable
        à qui n'a droit qu'à un capteur."""
        assert not IotScope(site="batA", device_id="c1").allows("batA", None)

    def test_un_equipement_sans_site_est_refuse(self) -> None:
        """Deux sites peuvent nommer leur capteur de la même façon."""
        with pytest.raises(IotTokenError, match="ne désigne rien"):
            IotScope(device_id="c1")

    def test_une_portee_absente_ne_passe_pas_pour_globale(self) -> None:
        assert not IotScope(site="batA").allows(None, None)

    @pytest.mark.parametrize(
        "portee,attendu",
        [
            (IotScope(), "globale"),
            (IotScope(site="batA"), "site 'batA'"),
            (IotScope(site="batA", device_id="c1"), "équipement 'c1'"),
        ],
    )
    def test_la_portee_se_dit_en_clair(self, portee: IotScope, attendu: str) -> None:
        assert attendu in portee.describe()


class TestJetonEngendre:

    def test_il_porte_un_prefixe_reconnaissable(self) -> None:
        """Un jeton trouvé dans un journal doit se laisser identifier."""
        assert generate_token().startswith(TOKEN_PREFIX)

    def test_deux_jetons_different(self) -> None:
        assert generate_token() != generate_token()

    def test_l_entropie_est_de_256_bits(self) -> None:
        assert len(generate_token()) == len(TOKEN_PREFIX) + 64

    def test_la_forme_est_reconnue(self) -> None:
        assert looks_like_token(generate_token())

    @pytest.mark.parametrize(
        "bruit", ["", "abc", "forge_iot_court", "forge_iot_" + "z" * 64]
    )
    def test_ce_qui_n_en_est_pas_est_ecarte(self, bruit: str) -> None:
        assert not looks_like_token(bruit)

    def test_l_empreinte_est_stable_et_ne_rend_pas_le_jeton(self) -> None:
        jeton = generate_token()
        empreinte = hash_token(jeton)

        assert empreinte == hash_token(jeton)
        assert jeton not in empreinte
        assert len(empreinte) == 64

    def test_une_empreinte_de_jeton_vide_leve(self) -> None:
        with pytest.raises(IotTokenError):
            hash_token("  ")


class _FauxDb:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self._suivant = 1

    def insert(self, sql: str, params: Any) -> int:
        identifiant = self._suivant
        self._suivant += 1
        self.rows.append({
            "id": identifiant, "token_hash": params[0], "site": params[1],
            "device_id": params[2], "label": params[3], "created_at": params[4],
            "revoked_at": None,
        })
        return identifiant

    def execute(self, sql: str, params: Any) -> int:
        for ligne in self.rows:
            if ligne["id"] == params[1] and ligne["revoked_at"] is None:
                ligne["revoked_at"] = params[0]
                return 1
        return 0

    def fetch_one(self, sql: str, params: Any) -> "dict[str, Any] | None":
        for ligne in self.rows:
            if ligne["token_hash"] == params[0]:
                return dict(ligne)
        return None

    def fetch_all(self, sql: str, params: Any = ()) -> list[dict[str, Any]]:
        return [
            {k: v for k, v in ligne.items() if k != "token_hash"}
            for ligne in self.rows
        ]


class TestRegistreDeJetons:

    @pytest.fixture
    def depot(self) -> IotTokenRepository:
        return IotTokenRepository(_FauxDb())  # type: ignore[arg-type]

    def test_le_jeton_en_clair_n_est_rendu_qu_a_la_creation(
        self, depot: IotTokenRepository
    ) -> None:
        brut, identifiant = depot.create(site="batA", label="prestataire")

        assert looks_like_token(brut)
        assert identifiant == 1
        assert all("token_hash" not in ligne for ligne in depot.list_all())

    def test_le_jeton_n_est_jamais_stocke_en_clair(
        self, depot: IotTokenRepository
    ) -> None:
        """Le point qui compte : une base lue par un tiers ne donne rien."""
        brut, _ = depot.create(site="batA")
        interne = depot._db  # type: ignore[attr-defined]

        assert all(brut not in str(ligne) for ligne in interne.rows)

    def test_un_jeton_valide_rend_sa_portee(self, depot: IotTokenRepository) -> None:
        brut, _ = depot.create(site="batA", device_id="c1")

        portee = depot.resolve(brut)

        assert portee is not None
        assert (portee.site, portee.device_id) == ("batA", "c1")

    def test_un_jeton_inconnu_n_ouvre_rien(self, depot: IotTokenRepository) -> None:
        assert depot.resolve(generate_token()) is None

    def test_un_jeton_malforme_n_interroge_pas_la_base(
        self, depot: IotTokenRepository
    ) -> None:
        assert depot.resolve("pas un jeton") is None

    def test_un_jeton_revoque_n_ouvre_plus_rien(
        self, depot: IotTokenRepository
    ) -> None:
        brut, identifiant = depot.create(site="batA")

        assert depot.revoke(identifiant) is True
        assert depot.resolve(brut) is None

    def test_la_ligne_survit_a_la_revocation(self, depot: IotTokenRepository) -> None:
        """Savoir qu'un jeton a existé, et quand il a cessé de valoir."""
        _, identifiant = depot.create(site="batA")
        depot.revoke(identifiant)

        lignes = depot.list_all()
        assert len(lignes) == 1
        assert lignes[0]["revoked_at"] is not None

    def test_revoquer_deux_fois_ne_ment_pas(self, depot: IotTokenRepository) -> None:
        _, identifiant = depot.create(site="batA")
        depot.revoke(identifiant)

        assert depot.revoke(identifiant) is False

    @pytest.mark.parametrize("mauvais", ["a b", "../x", "", "x" * 65, "é"])
    def test_un_nom_de_site_invalide_est_refuse(
        self, depot: IotTokenRepository, mauvais: str
    ) -> None:
        with pytest.raises(IotTokenError):
            depot.create(site=mauvais)


class TestLectureBorneeEnSql:

    def test_le_filtre_est_pose_dans_la_requete(self) -> None:
        """Filtrer après la lecture aurait fait passer les mesures des autres
        sites par un processus qui n'y a pas droit."""
        sql = select_iot_events_scoped_sql(site=True, device=False)

        assert "WHERE site = ?" in sql

    def test_une_portee_d_equipement_ajoute_sa_condition(self) -> None:
        sql = select_iot_events_scoped_sql(site=True, device=True)

        assert "site = ? AND device_id = ?" in sql

    def test_sans_borne_aucune_condition(self) -> None:
        assert "WHERE" not in select_iot_events_scoped_sql(site=False, device=False)


# -------------------------------------------------------- IOT-AGGREGATES


class _AggDb:
    def __init__(self, ligne: "dict[str, Any] | None") -> None:
        self.ligne = ligne
        self.params: list[Any] = []

    def fetch_one(self, sql: str, params: Any) -> "dict[str, Any] | None":
        self.params.append(params)
        return self.ligne


class TestFenetre:

    def test_elle_remonte_du_present(self) -> None:
        maintenant = datetime(2026, 9, 2, 12, 0, 0)

        assert window_start(24, now=maintenant) == maintenant - timedelta(hours=24)

    @pytest.mark.parametrize("mauvais", [0, -1, MAX_WINDOW_HOURS + 1])
    def test_une_fenetre_invalide_leve(self, mauvais: int) -> None:
        with pytest.raises(IotAggregateError):
            window_start(mauvais)

    @pytest.mark.parametrize("mauvais", ["24", 24.5, True, None])
    def test_une_fenetre_non_entiere_leve(self, mauvais: Any) -> None:
        with pytest.raises(IotAggregateError):
            window_start(mauvais)

    def test_le_message_dit_pourquoi_la_borne_existe(self) -> None:
        with pytest.raises(IotAggregateError, match="export"):
            window_start(MAX_WINDOW_HOURS + 1)


class TestAgregat:

    def test_les_quatre_valeurs_sont_rendues(self) -> None:
        db = _AggDb({"n": 3, "moyenne": 21.5, "mini": 18.0, "maxi": 25.0})

        agregat = aggregate_for_device("batA", "c1", "temperature", unit="C", db=db)  # type: ignore[arg-type]

        assert agregat.as_dict() == {
            "count": 3, "average": 21.5, "min": 18.0, "max": 25.0, "unit": "C",
        }

    def test_un_decimal_de_postgres_devient_un_flottant(self) -> None:
        """PostgreSQL rend AVG en Decimal, MariaDB en float.

        Sans conversion, la même requête donnerait deux types selon le backend,
        et la sérialisation JSON échouerait sur l'un des deux.
        """
        db = _AggDb({"n": 2, "moyenne": Decimal("21.5"), "mini": 18, "maxi": 25})

        agregat = aggregate_for_site("batA", "temperature", db=db)  # type: ignore[arg-type]

        assert isinstance(agregat.average, float)
        assert agregat.average == 21.5

    def test_une_fenetre_vide_ne_rend_pas_zero(self) -> None:
        """« Le capteur n'a rien envoyé » et « le capteur a relevé zéro » sont
        deux faits différents, que confondre fausserait toute moyenne."""
        db = _AggDb({"n": 0, "moyenne": None, "mini": None, "maxi": None})

        agregat = aggregate_for_device("batA", "c1", "temperature", db=db)  # type: ignore[arg-type]

        assert agregat.is_empty
        assert agregat.average is None

    def test_une_ligne_absente_ne_leve_pas(self) -> None:
        agregat = aggregate_for_device("batA", "c1", "t", db=_AggDb(None))  # type: ignore[arg-type]

        assert agregat.is_empty

    def test_les_parametres_partent_lies(self) -> None:
        """Jamais d'interpolation dans le SQL."""
        db = _AggDb({"n": 1, "moyenne": 1.0, "mini": 1.0, "maxi": 1.0})
        maintenant = datetime(2026, 9, 2, 12, 0, 0)

        aggregate_for_device("batA", "c1", "temperature", hours=6, db=db, now=maintenant)  # type: ignore[arg-type]

        site, device, kind, debut = db.params[0]
        assert (site, device, kind) == ("batA", "c1", "temperature")
        assert debut == maintenant - timedelta(hours=6)

    def test_le_comptage_porte_sur_la_valeur(self) -> None:
        """Une mesure sans valeur ne doit pas gonfler l'effectif d'une moyenne
        qu'elle n'alimente pas."""
        assert "COUNT(value)" in select_aggregate_sql(by_device=True)

    def test_le_sql_reste_visible(self) -> None:
        sql = select_aggregate_sql(by_device=False)

        assert "AVG(value)" in sql and "MIN(value)" in sql and "MAX(value)" in sql
        assert "site = ?" in sql and "device_id" not in sql

    def test_un_agregat_vide_se_distingue_d_une_moyenne_nulle(self) -> None:
        assert IotAggregate(count=0).is_empty
        assert not IotAggregate(count=1, average=0.0).is_empty


# -------------------------------------------------------- IOT-RBAC-READ


@pytest.fixture(autouse=True)
def _sans_controle():
    clear_iot_permission_checks()
    yield
    clear_iot_permission_checks()


class TestPriseDeControle:

    def test_sans_controle_branche_rien_ne_change(self) -> None:
        """Le paquet n'invente pas une politique que personne n'a demandée."""
        assert is_read_allowed(None, GLOBAL_SCOPE, ACTION_READ_EVENTS)

    def test_un_refus_ferme_la_lecture(self) -> None:
        register_iot_permission_check(lambda req, scope, action: False)

        assert not is_read_allowed(None, GLOBAL_SCOPE, ACTION_READ_EVENTS)

    def test_tous_doivent_accepter(self) -> None:
        """Une politique d'accès s'ajoute, elle ne se remplace pas."""
        register_iot_permission_check(lambda req, scope, action: True)
        register_iot_permission_check(lambda req, scope, action: False)

        assert not is_read_allowed(None, GLOBAL_SCOPE, ACTION_READ_EVENTS)

    def test_le_premier_refus_arrete_la_serie(self) -> None:
        appels: list[str] = []

        def premier(req: Any, scope: Any, action: str) -> bool:
            appels.append("premier")
            return False

        def second(req: Any, scope: Any, action: str) -> bool:
            appels.append("second")
            return True

        register_iot_permission_check(premier)
        register_iot_permission_check(second)
        is_read_allowed(None, GLOBAL_SCOPE, ACTION_READ_EVENTS)

        assert appels == ["premier"]

    def test_une_panne_refuse_la_lecture(self) -> None:
        """Le jour où le service de permissions tombe, tout s'ouvrirait."""

        def en_panne(req: Any, scope: Any, action: str) -> bool:
            raise RuntimeError("service de permissions injoignable")

        register_iot_permission_check(en_panne)

        assert not is_read_allowed(None, GLOBAL_SCOPE, ACTION_READ_EVENTS)

    @pytest.mark.parametrize("retour", [None, "oui", 1, [], object()])
    def test_un_retour_non_booleen_refuse_la_lecture(self, retour: Any) -> None:
        """Un contrôle qui rend une chaîne non vide serait lu comme un vrai."""
        register_iot_permission_check(lambda req, scope, action: retour)

        assert not is_read_allowed(None, GLOBAL_SCOPE, ACTION_READ_EVENTS)

    def test_le_controle_recoit_la_portee_et_l_action(self) -> None:
        vus: list[tuple[Any, str]] = []

        def espion(req: Any, scope: Any, action: str) -> bool:
            vus.append((scope, action))
            return True

        register_iot_permission_check(espion)
        portee = IotScope(site="batA")
        is_read_allowed(None, portee, ACTION_READ_AGGREGATES)

        assert vus == [(portee, ACTION_READ_AGGREGATES)]

    def test_une_action_inconnue_leve(self) -> None:
        """La liste est fermée : un contrôle branché sait ce qu'il peut recevoir."""
        with pytest.raises(ValueError, match="action inconnue"):
            is_read_allowed(None, GLOBAL_SCOPE, "iot.tout_supprimer")

    def test_les_deux_actions_sont_declarees(self) -> None:
        assert IOT_ACTIONS == {ACTION_READ_EVENTS, ACTION_READ_AGGREGATES}

    def test_un_double_enregistrement_ne_double_pas(self) -> None:
        def controle(req: Any, scope: Any, action: str) -> bool:
            return True

        register_iot_permission_check(controle)
        register_iot_permission_check(controle)

        assert len(registered_permission_checks()) == 1

    def test_on_peut_debrancher(self) -> None:
        def refuse(req: Any, scope: Any, action: str) -> bool:
            return False

        register_iot_permission_check(refuse)
        assert unregister_iot_permission_check(refuse) is True
        assert is_read_allowed(None, GLOBAL_SCOPE, ACTION_READ_EVENTS)

    def test_un_controle_non_appelable_est_refuse(self) -> None:
        with pytest.raises(TypeError):
            register_iot_permission_check("rbac")  # type: ignore[arg-type]

    def test_aucun_opt_in_n_est_importe(self) -> None:
        """Un paquet IoT qui dépendrait du RBAC obligerait à installer le RBAC
        pour recevoir des mesures MQTT."""
        import ast
        from pathlib import Path

        import forge_mvc_iot.access as module

        arbre = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        importes = {
            (n.module or "")
            for n in ast.walk(arbre)
            if isinstance(n, ast.ImportFrom)
        } | {
            alias.name
            for n in ast.walk(arbre)
            if isinstance(n, ast.Import)
            for alias in n.names
        }

        autres = [
            m for m in importes
            if m.startswith("forge_mvc_") and not m.startswith("forge_mvc_iot")
        ]
        assert autres == [], f"opt-in importé depuis access.py : {autres}"


class TestRoutesProtegees:

    def _controleur(self, **kw: Any) -> Any:
        from forge_mvc_iot.http import IotHttpController

        return IotHttpController(object(), **kw)  # type: ignore[arg-type]

    def _requete(self, jeton: "str | None" = None, **routes: str) -> Any:
        class _Req:
            def header(self, name: str, default: Any = None) -> Any:
                return f"Bearer {jeton}" if jeton else default

            def route(self, name: str) -> str:
                return routes.get(name, "")

            def query(self, name: str, default: Any = None) -> Any:
                return default

        return _Req()

    def test_sans_jeton_la_lecture_est_refusee(self) -> None:
        controleur = self._controleur(api_token="secret", token_repository=None)

        assert controleur.list_events(self._requete()).status == 401

    def test_un_jeton_de_site_ne_lit_pas_un_autre_site(self) -> None:
        """Bout en bout : le refus est un 403, pas un 401."""
        db = _FauxDb()
        depot = IotTokenRepository(db)  # type: ignore[arg-type]
        brut, _ = depot.create(site="batA")
        controleur = self._controleur(api_token="secret", token_repository=depot)

        reponse = controleur.count_by_device(
            self._requete(brut, site="batB", device_id="c1")
        )

        assert reponse.status == 403

    def test_le_refus_de_portee_n_est_pas_un_refus_d_authentification(self) -> None:
        """Un 401 ferait croire au porteur que son jeton est faux, et il le
        remplacerait au lieu d'en demander un dont la portée convient."""
        db = _FauxDb()
        depot = IotTokenRepository(db)  # type: ignore[arg-type]
        brut, _ = depot.create(site="batA", device_id="c1")
        controleur = self._controleur(api_token="secret", token_repository=depot)

        assert controleur.count_by_device(
            self._requete(brut, site="batA", device_id="c9")
        ).status == 403

    def test_le_jeton_d_environnement_garde_la_portee_globale(self) -> None:
        """Le retirer casserait les déploiements existants."""
        from forge_mvc_iot.http import IotHttpController

        class _Repo:
            def count_by_device(self, site: str, device_id: str) -> int:
                return 7

        controleur = IotHttpController(
            _Repo(), api_token="secret", token_repository=IotTokenRepository(_FauxDb())  # type: ignore[arg-type]
        )

        reponse = controleur.count_by_device(
            self._requete("secret", site="nimporte", device_id="c1")
        )

        assert reponse.status == 200

    def test_un_controle_de_permission_ferme_meme_avec_un_bon_jeton(self) -> None:
        register_iot_permission_check(lambda req, scope, action: False)
        controleur = self._controleur(api_token="secret", token_repository=None)

        assert controleur.list_events(self._requete("secret")).status == 403
