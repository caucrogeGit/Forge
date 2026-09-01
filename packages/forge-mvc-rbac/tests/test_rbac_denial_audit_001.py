"""RBAC-DENIAL-AUDIT-001 : les refus d'accès peuvent être observés.

Un refus rendait une 403 et rien de plus. Aucune trace nulle part, si bien
qu'une énumération de droits, quelqu'un qui essaie une à une les routes
protégées, ne laissait rien derrière elle. L'exploitant n'avait aucun moyen de
la voir, ni même de savoir qu'un compte butait sur une permission mal
attribuée.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import (  # noqa: E402
    DenialEvent,
    clear_denial_observers,
    denial_observers,
    notify_permission_denied,
    on_permission_denied,
)
from forge_mvc_rbac.contract import (  # noqa: E402
    RbacContractResult,
    require_contract_permission,
)

CONTRAT_ABSENT = RbacContractResult(valid=False, exists=False, path="")


@pytest.fixture(autouse=True)
def _sans_observateur():
    """Un observateur laissé en place ferait dépendre les tests les uns des autres."""
    clear_denial_observers()
    yield
    clear_denial_observers()


class TestEnregistrement:
    def test_rien_n_observe_par_defaut(self) -> None:
        """L'enregistrement est explicite."""
        assert denial_observers() == ()

    def test_un_observateur_enregistre_est_appele(self) -> None:
        vus: list[DenialEvent] = []
        on_permission_denied(vus.append)

        notify_permission_denied("article.update")

        assert len(vus) == 1
        assert vus[0].permission == "article.update"

    def test_l_ordre_d_enregistrement_est_conserve(self) -> None:
        ordre: list[str] = []
        on_permission_denied(lambda e: ordre.append("premier"))
        on_permission_denied(lambda e: ordre.append("second"))

        notify_permission_denied("x")

        assert ordre == ["premier", "second"]

    def test_l_enregistrement_rend_l_observateur(self) -> None:
        """Pour permettre l'usage en décorateur."""
        def observateur(refus: DenialEvent) -> None: ...

        assert on_permission_denied(observateur) is observateur


class TestIsolation:
    def test_un_observateur_qui_leve_ne_casse_pas_la_reponse(self) -> None:
        """Une base d'audit indisponible ne doit pas transformer un 403 en 500."""
        def casse(refus: DenialEvent) -> None:
            raise RuntimeError("base d'audit injoignable")

        on_permission_denied(casse)

        reponse = require_contract_permission(CONTRAT_ABSENT, ["visiteur"], "article.update")
        assert reponse is not None
        assert reponse.status == 403

    def test_un_observateur_qui_leve_n_empeche_pas_les_suivants(self) -> None:
        vus: list[str] = []

        def casse(refus: DenialEvent) -> None:
            raise RuntimeError("premier en erreur")

        on_permission_denied(casse)
        on_permission_denied(lambda e: vus.append("second"))

        notify_permission_denied("x")

        assert vus == ["second"]

    def test_l_erreur_de_l_observateur_est_journalisee(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Avaler sans rien dire cacherait un audit muet."""
        on_permission_denied(lambda e: (_ for _ in ()).throw(RuntimeError("boum")))

        with caplog.at_level("WARNING"):
            notify_permission_denied("article.update")

        assert "article.update" in caplog.text


class TestEvenement:
    def test_un_visiteur_anonyme_est_rapporte_sans_acteur(self) -> None:
        """C'est souvent celui qu'on veut voir."""
        vus: list[DenialEvent] = []
        on_permission_denied(vus.append)

        notify_permission_denied("article.update", request=None)

        assert vus[0].actor is None

    def test_le_chemin_et_la_methode_suivent_quand_la_requete_les_porte(self) -> None:
        vus: list[DenialEvent] = []
        on_permission_denied(vus.append)

        class _Requete:
            path = "/admin/articles"
            method = "POST"

        notify_permission_denied("article.update", request=_Requete())

        assert vus[0].path == "/admin/articles"
        assert vus[0].method == "POST"

    def test_une_requete_sans_ces_attributs_ne_fait_pas_echouer(self) -> None:
        """Les doubles de test varient : l'observation ne doit pas en dépendre."""
        vus: list[DenialEvent] = []
        on_permission_denied(vus.append)

        notify_permission_denied("x", request=object())

        assert vus[0].path is None

    def test_l_evenement_est_immuable(self) -> None:
        evenement = DenialEvent(permission="x")
        with pytest.raises(Exception):
            evenement.permission = "y"  # type: ignore[misc]

    def test_l_evenement_est_construit_une_fois_pour_tous(self) -> None:
        vus: list[DenialEvent] = []
        on_permission_denied(vus.append)
        on_permission_denied(vus.append)

        notify_permission_denied("x")

        assert vus[0] is vus[1]


class TestGardesBranchees:
    def test_la_garde_contractuelle_annonce(self) -> None:
        vus: list[DenialEvent] = []
        on_permission_denied(vus.append)

        require_contract_permission(CONTRAT_ABSENT, ["visiteur"], "article.update")

        assert vus[0].source == "contract"

    def test_une_permission_accordee_n_annonce_rien(self) -> None:
        """Seuls les refus intéressent : annoncer les succès noierait le journal."""
        vus: list[DenialEvent] = []
        on_permission_denied(vus.append)

        # Le contrat range les permissions en liste sous le rôle, directement.
        contrat = RbacContractResult(
            valid=True, exists=True, path="rbac.json",
            data={"roles": {"admin": ["article.update"]}},
        )
        require_contract_permission(contrat, ["admin"], "article.update")

        assert vus == []

    @pytest.mark.parametrize(
        "module", ["contract", "rbac", "prefix_guard"]
    )
    def test_chaque_garde_annonce_ses_refus(self, module: str) -> None:
        """Une garde qui refuse en silence laisserait un angle mort."""
        import importlib

        cible = importlib.import_module(f"forge_mvc_rbac.{module}")
        source = Path(cible.__file__ or "").read_text(encoding="utf-8")
        assert "notify_permission_denied" in source


class TestSansDependance:
    def test_rbac_n_importe_aucun_opt_in(self) -> None:
        """Ce module annonce, il ne journalise pas : l'application décide."""
        from forge_mvc_rbac import denials

        arbre = ast.parse(Path(denials.__file__).read_text(encoding="utf-8"))
        modules: list[str] = []
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Import):
                modules.extend(alias.name for alias in noeud.names)
            elif isinstance(noeud, ast.ImportFrom) and noeud.module:
                modules.append(noeud.module)

        interdits = [m for m in modules if m.startswith("forge_mvc_") and "rbac" not in m]
        assert interdits == [], f"dépendance vers un autre opt-in : {interdits}"


class TestBranchementVersAudit:
    """Le motif que la référence donne à copier."""

    def test_un_refus_devient_une_ligne_d_audit(self) -> None:
        pytest.importorskip("forge_mvc_audit")
        from forge_mvc_audit import record_audit

        lignes: list[tuple[str, Any]] = []

        class _FauxDb:
            @staticmethod
            def insert(sql: str, params: Any) -> int:
                lignes.append((sql, params))
                return 1

        on_permission_denied(lambda refus: record_audit(
            "acces.refuse",
            actor=refus.actor,
            target_type="permission",
            target_id=refus.permission,
            db=_FauxDb(),
        ))

        require_contract_permission(CONTRAT_ABSENT, ["visiteur"], "article.update")

        assert len(lignes) == 1
        assert "article.update" in lignes[0][1]
