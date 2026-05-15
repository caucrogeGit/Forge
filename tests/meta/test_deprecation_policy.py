"""Tests documentaires — RELEASE-DEPRECATION-001.

Vérifient que docs/deprecation-policy.md existe et couvre les sujets
requis : cycle annonce→maintien→retrait, alternatives obligatoires,
commandes CLI, API publique, exceptions de sécurité, changelog, MAJOR.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parent.parent.parent
POLICY = ROOT / "docs" / "deprecation-policy.md"


@pytest.fixture(scope="module")
def policy() -> str:
    assert POLICY.exists(), f"Politique non trouvée : {POLICY}"
    return POLICY.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Existence et navigation
# ---------------------------------------------------------------------------


class TestExistenceEtNavigation:
    def test_fichier_existe(self):
        assert POLICY.exists()

    def test_fichier_non_vide(self, policy):
        assert len(policy) > 500

    def test_titre_contient_depreciation(self, policy):
        lower = policy.lower()
        assert "dépréciation" in lower or "deprecation" in lower

    def test_mkdocs_contient_deprecation_policy(self):
        mkdocs = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        assert "deprecation-policy.md" in mkdocs


# ---------------------------------------------------------------------------
# 2. Principe général
# ---------------------------------------------------------------------------


class TestPrincipeGeneral:
    def test_mentionne_annonce(self, policy):
        lower = policy.lower()
        assert "annoncée" in lower or "annonce" in lower

    def test_mentionne_maintien(self, policy):
        lower = policy.lower()
        assert "maintien" in lower or "maintenu" in lower

    def test_mentionne_retrait(self, policy):
        lower = policy.lower()
        assert "retrait" in lower or "supprimé" in lower or "retiré" in lower

    def test_mentionne_alternative_obligatoire(self, policy):
        lower = policy.lower()
        assert "alternative" in lower

    def test_mentionne_ne_pas_casser_brutalement(self, policy):
        lower = policy.lower()
        assert "brutal" in lower or "casser" in lower or "cassé" in lower or "rupture" in lower


# ---------------------------------------------------------------------------
# 3. Cycle de dépréciation
# ---------------------------------------------------------------------------


class TestCycleDepreciation:
    def test_mentionne_cycle(self, policy):
        lower = policy.lower()
        assert "cycle" in lower or "annonce" in lower

    def test_mentionne_version_major_pour_retrait(self, policy):
        assert "MAJOR" in policy

    def test_mentionne_periode_transition(self, policy):
        lower = policy.lower()
        assert "période" in lower or "periode" in lower or "maintenu" in lower

    def test_mentionne_serie_2x(self, policy):
        assert "2.x" in policy or "série 2" in policy.lower()


# ---------------------------------------------------------------------------
# 4. Commandes CLI
# ---------------------------------------------------------------------------


class TestCommandesCli:
    def test_mentionne_commandes_cli(self, policy):
        lower = policy.lower()
        assert "cli" in lower and ("commande" in lower or "command" in lower)

    def test_mentionne_avertissement_stderr(self, policy):
        lower = policy.lower()
        assert "stderr" in lower or "avertissement" in lower

    def test_mentionne_exemple_deprecation_cli(self, policy):
        assert "AVERTISSEMENT" in policy or "avertissement" in policy.lower()

    def test_mentionne_alternative_cli(self, policy):
        lower = policy.lower()
        assert "alternative" in lower or "utiliser" in lower


# ---------------------------------------------------------------------------
# 5. API Python publique
# ---------------------------------------------------------------------------


class TestApiPythonPublique:
    def test_mentionne_api_publique(self, policy):
        lower = policy.lower()
        assert "api" in lower

    def test_mentionne_deprecation_warning(self, policy):
        assert "DeprecationWarning" in policy

    def test_mentionne_warnings_warn(self, policy):
        assert "warnings.warn" in policy

    def test_mentionne_stacklevel(self, policy):
        assert "stacklevel" in policy

    def test_mentionne_exemple_core_security_hashing(self, policy):
        assert "core.security.hashing" in policy or "hashing" in policy.lower()


# ---------------------------------------------------------------------------
# 6. Options CLI et conventions
# ---------------------------------------------------------------------------


class TestOptionsCli:
    def test_mentionne_options_cli(self, policy):
        lower = policy.lower()
        assert "option" in lower or "--flag" in lower or "flag" in lower

    def test_mentionne_conventions(self, policy):
        lower = policy.lower()
        assert "convention" in lower


# ---------------------------------------------------------------------------
# 7. Fichiers générés
# ---------------------------------------------------------------------------


class TestFichiersGeneres:
    def test_mentionne_fichiers_generes(self, policy):
        lower = policy.lower()
        assert "généré" in lower or "genere" in lower or "fichier" in lower

    def test_mentionne_sans_force_non_destructif(self, policy):
        lower = policy.lower()
        assert "force" in lower or "destructif" in lower or "écrase" in lower


# ---------------------------------------------------------------------------
# 8. Messages d'avertissement
# ---------------------------------------------------------------------------


class TestMessagesAvertissement:
    def test_mentionne_format_avertissement(self, policy):
        lower = policy.lower()
        assert "avertissement" in lower or "warning" in lower

    def test_mentionne_ne_pas_bloquer(self, policy):
        lower = policy.lower()
        assert "bloquer" in lower or "continue" in lower or "fonctionne" in lower

    def test_mentionne_version_retrait(self, policy):
        assert "3.0.0" in policy or "version MAJOR" in policy or "Forge 3" in policy


# ---------------------------------------------------------------------------
# 9. Changelog
# ---------------------------------------------------------------------------


class TestChangelog:
    def test_mentionne_changelog(self, policy):
        assert "CHANGELOG" in policy or "changelog" in policy.lower()

    def test_mentionne_section_supprime(self, policy):
        lower = policy.lower()
        assert "supprimé" in lower or "supprime" in lower or "Supprimé" in policy

    def test_mentionne_section_modifie_ou_deprecie(self, policy):
        lower = policy.lower()
        assert "modifié" in lower or "déprécié" in lower or "Déprécié" in policy


# ---------------------------------------------------------------------------
# 10. Retrait en version MAJOR
# ---------------------------------------------------------------------------


class TestRetraitVersionMajor:
    def test_retrait_reserve_a_major(self, policy):
        assert "MAJOR" in policy

    def test_mentionne_migration(self, policy):
        lower = policy.lower()
        assert "migration" in lower

    def test_mentionne_mise_a_jour_docs(self, policy):
        lower = policy.lower()
        assert "stability-contract" in lower or "reference.md" in lower or "docs" in lower


# ---------------------------------------------------------------------------
# 11. Exceptions de sécurité
# ---------------------------------------------------------------------------


class TestExceptionsSecurite:
    def test_mentionne_exceptions_securite(self, policy):
        lower = policy.lower()
        assert "exception" in lower and ("sécurité" in lower or "securite" in lower)

    def test_mentionne_vulnerabilite(self, policy):
        lower = policy.lower()
        assert "vulnérabilité" in lower or "vulnerabilite" in lower or "vulnérabilit" in lower

    def test_mentionne_patch_urgence(self, policy):
        lower = policy.lower()
        assert "urgence" in lower or "immédiat" in lower or "immédiatement" in lower or "corrective" in lower

    def test_mentionne_chemin_migration_court(self, policy):
        lower = policy.lower()
        assert "migration" in lower and ("court" in lower or "aussi" in lower or "proposer" in lower)


# ---------------------------------------------------------------------------
# 12. Exemples concrets
# ---------------------------------------------------------------------------


class TestExemplesConcrets:
    def test_mentionne_au_moins_un_exemple(self, policy):
        lower = policy.lower()
        assert "exemple" in lower

    def test_exemple_legacy_present(self, policy):
        assert "CMD-LEGACY" in policy or "core.security" in policy or "require_auth" in policy.lower()

    def test_exemple_core_auth(self, policy):
        assert "core.auth" in policy

    def test_exemple_require_auth_deprecie(self, policy):
        lower = policy.lower()
        assert "require_auth" in lower or "login_required" in lower


# ---------------------------------------------------------------------------
# 13. Lien avec release-policy.md
# ---------------------------------------------------------------------------


class TestLienReleasePolitique:
    def test_reference_release_policy(self, policy):
        assert "release-policy" in policy or "Politique de release" in policy

    def test_reference_stability_contract(self, policy):
        assert "stability-contract" in policy or "Contrat de stabilité" in policy


# ---------------------------------------------------------------------------
# 14. Limites restantes
# ---------------------------------------------------------------------------


class TestLimitesRestantes:
    def test_mentionne_limites_restantes(self, policy):
        lower = policy.lower()
        assert "ne couvre pas" in lower or "limite" in lower

    def test_mentionne_release_compat(self, policy):
        assert "RELEASE-COMPAT-001" in policy

    def test_mentionne_release_migration_guide(self, policy):
        assert "RELEASE-MIGRATION-GUIDE-001" in policy

    def test_mentionne_release_lts(self, policy):
        assert "RELEASE-LTS-001" in policy


# ---------------------------------------------------------------------------
# 15. Roadmap
# ---------------------------------------------------------------------------


class TestRoadmap:
    def test_release_deprecation_dans_roadmap(self):
        roadmap = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
        assert "RELEASE-DEPRECATION-001" in roadmap

    def test_release_compat_dans_roadmap(self):
        roadmap = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
        assert "RELEASE-COMPAT-001" in roadmap
