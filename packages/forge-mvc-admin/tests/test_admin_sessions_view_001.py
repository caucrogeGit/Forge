"""`ADMIN-SESSIONS-VIEW-001` — le back-office montre l'état des sessions.

`forge-mvc-sessions-db` compte les sessions depuis `SESSIONS-METRICS-001`,
réparties par nature, et sait dire si la purge suit. **Personne ne regardait ce
nombre** : il fallait ouvrir un client SQL, ou lire `forge sessions:gc` en
aveugle.

La question à laquelle cette page répond est celle de l'exploitation : une
table qui grossit pendant que le nombre d'actives stagne signale un minuteur
`sessions:gc` arrêté, et le guide de déploiement demande justement de le poser.

## Deux décisions qui tiennent la page

Le couplage est **souple**. `forge-mvc-admin` ne déclare pas
`forge-mvc-sessions-db` en dépendance, comme il ne déclare ni `forge-mvc-rbac`
ni `forge-mvc-workflow`. Son absence rend un panneau qui dit pourquoi il est
vide, jamais une page en erreur.

**Aucun identifiant de session n'est affiché**, et il n'y en a pas à afficher :
la mesure rend des agrégats. C'est heureux, un identifiant lu sur un écran, une
capture ou une épaule est une session volée.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_admin")

from forge_mvc_admin.sessions_panel import (  # noqa: E402
    PURGE_ALERT_RATIO,
    SessionsPanel,
    sessions_panel,
)


class _Mesures:
    """Ce que `session_metrics` rend, réduit à ce que le panneau lit."""

    def __init__(self, active: int, expired: int, by_kind: "dict[str, int]") -> None:
        self.active = active
        self.expired = expired
        self.by_kind = by_kind

    @property
    def total(self) -> int:
        return self.active + self.expired

    @property
    def purge_backlog_ratio(self) -> float:
        return self.expired / self.total if self.total else 0.0


def _avec_mesures(monkeypatch: pytest.MonkeyPatch, mesures: Any) -> SessionsPanel:
    import forge_mvc_sessions_db

    monkeypatch.setattr(
        forge_mvc_sessions_db, "session_metrics",
        lambda **kw: mesures, raising=False)
    return sessions_panel()


# ─────────────────────────────────────────────────────────────────────────────
# Ce que la page montre
# ─────────────────────────────────────────────────────────────────────────────


class TestPhotographie:

    def test_les_totaux_sont_rendus(self, monkeypatch: pytest.MonkeyPatch) -> None:
        panneau = _avec_mesures(
            monkeypatch, _Mesures(12, 3, {"anonymous": 8, "authenticated": 4}))

        assert panneau.disponible
        assert (panneau.actives, panneau.expirees, panneau.total) == (12, 3, 15)

    def test_la_repartition_par_nature_est_triee(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Un ordre stable, sans quoi le tableau danse d'un rafraîchissement
        à l'autre."""
        panneau = _avec_mesures(monkeypatch, _Mesures(
            3, 0, {"remembered": 1, "anonymous": 2, "authenticated": 0}))

        assert [n for n, _ in panneau.par_nature] == [
            "anonymous", "authenticated", "remembered"]

    def test_une_nature_a_zero_reste_affichee(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Une ligne absente et une valeur nulle se lisent différemment, et
        l'absence ferait croire à une métrique cassée."""
        panneau = _avec_mesures(monkeypatch, _Mesures(
            2, 0, {"anonymous": 2, "authenticated": 0, "remembered": 0}))

        assert dict(panneau.par_nature)["remembered"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# La question que la page existe pour répondre
# ─────────────────────────────────────────────────────────────────────────────


class TestPurgeEnRetard:

    def test_une_table_saine_n_alerte_pas(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        panneau = _avec_mesures(monkeypatch, _Mesures(90, 10, {"anonymous": 90}))

        assert not panneau.purge_en_retard

    def test_une_majorite_de_lignes_mortes_alerte(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Au delà de la moitié, la table coûte deux fois ce qu'elle devrait à
        chaque balayage : c'est un minuteur `sessions:gc` arrêté."""
        panneau = _avec_mesures(monkeypatch, _Mesures(10, 90, {"anonymous": 10}))

        assert panneau.purge_en_retard

    def test_le_seuil_est_celui_que_la_metrique_documente(self) -> None:
        assert PURGE_ALERT_RATIO == 0.5

    def test_une_table_vide_n_alerte_pas(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Zéro sur zéro ne vaut pas « en retard »."""
        panneau = _avec_mesures(monkeypatch, _Mesures(0, 0, {}))

        assert not panneau.purge_en_retard


# ─────────────────────────────────────────────────────────────────────────────
# Le couplage reste souple
# ─────────────────────────────────────────────────────────────────────────────


class TestCouplageSouple:

    def test_sans_l_optin_le_panneau_dit_pourquoi(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Un projet dont les sessions vivent en mémoire n'a pas à installer
        l'opt-in pour ouvrir son back-office."""
        import builtins

        vrai_import = builtins.__import__

        def _sans_sessions(nom: str, *a: Any, **k: Any) -> Any:
            if nom == "forge_mvc_sessions_db":
                raise ImportError("absent")
            return vrai_import(nom, *a, **k)

        monkeypatch.setattr(builtins, "__import__", _sans_sessions)
        panneau = sessions_panel()

        assert not panneau.disponible
        assert "forge-mvc-sessions-db" in panneau.indisponible

    def test_une_table_absente_ne_casse_pas_la_page(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Une page d'administration qui tombe parce qu'un panneau ne répond
        pas retire l'accès à tout le reste."""
        import forge_mvc_sessions_db

        def _leve(**kw: Any) -> Any:
            raise RuntimeError("table forge_sessions inconnue")

        monkeypatch.setattr(
            forge_mvc_sessions_db, "session_metrics", _leve, raising=False)
        panneau = sessions_panel()

        assert not panneau.disponible
        assert "sessions:init" in panneau.indisponible

    def test_l_indisponible_ne_rend_pas_des_zeros(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """« Aucune session » et « je ne sais pas » ne se corrigent pas au même
        endroit."""
        import forge_mvc_sessions_db

        monkeypatch.setattr(
            forge_mvc_sessions_db, "session_metrics",
            lambda **kw: (_ for _ in ()).throw(RuntimeError("hs")), raising=False)
        panneau = sessions_panel()

        assert panneau.indisponible
        assert not panneau.purge_en_retard

    def test_l_admin_ne_declare_pas_sessions_db_en_dependance(self) -> None:
        """Le couplage souple n'est souple que si rien ne le durcit."""
        import tomllib
        from pathlib import Path

        pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
        projet = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]
        declarees = " ".join(projet.get("dependencies", []))

        assert "forge-mvc-sessions-db" not in declarees


# ─────────────────────────────────────────────────────────────────────────────
# Rien qui puisse voler une session
# ─────────────────────────────────────────────────────────────────────────────


class TestAucunIdentifiantExpose:

    def test_le_panneau_ne_porte_aucun_identifiant(self) -> None:
        """Le contrat de la donnée, pas seulement du gabarit : ce qui n'est pas
        dans le panneau ne peut pas fuir par un gabarit modifié."""
        champs = set(SessionsPanel.__dataclass_fields__)

        for interdit in ("session_id", "sessions", "user_id", "identifiants"):
            assert interdit not in champs

    def test_le_gabarit_n_affiche_pas_de_session_id(self) -> None:
        from pathlib import Path

        gabarit = (Path(__file__).resolve().parents[1] / "forge_mvc_admin"
                   / "templates" / "admin" / "sessions.html")
        texte = gabarit.read_text(encoding="utf-8")

        assert "session_id" not in texte
        assert "Aucun identifiant de session n'est affiché" in texte


# ─────────────────────────────────────────────────────────────────────────────
# La page est atteignable
# ─────────────────────────────────────────────────────────────────────────────


class TestRouteCablee:
    """`ADMIN-BULK-ACTIONS-001` avait livré une fonction que rien n'atteignait.
    On vérifie donc le câblage, pas seulement le calcul."""

    def _routes(self) -> "list[tuple[str, str, dict[str, Any]]]":
        from forge_mvc_admin.http import register_admin_routes

        posees: "list[tuple[str, str, dict[str, Any]]]" = []

        class _Router:
            def add(self, methode: str, chemin: str, handler: Any, **kw: Any) -> None:
                posees.append((methode, chemin, kw))

        register_admin_routes(_Router())
        return posees

    def test_la_route_est_posee(self) -> None:
        assert ("GET", "/admin/_sessions") in [(m, c) for m, c, _ in self._routes()]

    def test_elle_precede_la_route_a_slug(self) -> None:
        """Le routeur retient la première route qui matche : `_sessions` serait
        sinon lu comme le slug d'une ressource."""
        chemins = [c for _, c, _ in self._routes()]

        assert chemins.index("/admin/_sessions") < chemins.index("/admin/{slug}")

    def test_le_tableau_de_bord_y_mene(self) -> None:
        """Une page qu'aucun lien n'atteint n'est pas une page."""
        from pathlib import Path

        gabarit = (Path(__file__).resolve().parents[1] / "forge_mvc_admin"
                   / "templates" / "admin" / "dashboard.html")

        assert "/admin/_sessions" in gabarit.read_text(encoding="utf-8")
