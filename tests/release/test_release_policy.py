"""Tests documentaires — RELEASE-POLICY-001.

Vérifient que docs/release-policy.md existe et couvre les sujets
requis : schéma MAJOR.MINOR.PATCH, règles de tag, validation obligatoire,
build wheel, publication GitHub/PyPI, changelog, roadmap, limites restantes.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
POLICY = ROOT / "docs" / "release-policy.md"


@pytest.fixture(scope="module")
def policy() -> str:
    """Contenu complet de la politique de release."""
    assert POLICY.exists(), f"Politique non trouvée : {POLICY}"
    return POLICY.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Existence et présence dans la navigation
# ---------------------------------------------------------------------------


class TestExistenceEtNavigation:
    def test_fichier_existe(self):
        assert POLICY.exists()

    def test_fichier_non_vide(self, policy):
        assert len(policy) > 500

    def test_titre_contient_release(self, policy):
        assert "release" in policy.lower() or "Release" in policy

    def test_mkdocs_contient_release_policy(self):
        mkdocs = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        assert "release-policy.md" in mkdocs


# ---------------------------------------------------------------------------
# 2. Schéma de versionnement MAJOR.MINOR.PATCH
# ---------------------------------------------------------------------------


class TestSchemaVersionnement:
    def test_mentionne_major(self, policy):
        assert "MAJOR" in policy

    def test_mentionne_minor(self, policy):
        assert "MINOR" in policy

    def test_mentionne_patch(self, policy):
        assert "PATCH" in policy

    def test_mentionne_semver(self, policy):
        lower = policy.lower()
        assert "semver" in lower or "sem ver" in lower or "sémantique" in lower or "SemVer" in policy

    def test_mentionne_exemple_version(self, policy):
        assert "2.2.0" in policy or "X.Y.Z" in policy

    def test_mentionne_rupture_de_compatibilite(self, policy):
        lower = policy.lower()
        assert "rupture" in lower or "breaking" in lower or "incompatible" in lower


# ---------------------------------------------------------------------------
# 3. Règles PATCH
# ---------------------------------------------------------------------------


class TestReglesPatch:
    def test_patch_mentionne_correction_bug(self, policy):
        lower = policy.lower()
        assert "bug" in lower or "correctif" in lower or "correction" in lower

    def test_patch_mentionne_securite(self, policy):
        lower = policy.lower()
        assert "sécurité" in lower or "securite" in lower or "security" in lower

    def test_patch_mentionne_sans_changement_api(self, policy):
        lower = policy.lower()
        assert "api" in lower and ("sans" in lower or "without" in lower or "compatible" in lower)


# ---------------------------------------------------------------------------
# 4. Règles MINOR
# ---------------------------------------------------------------------------


class TestReglesMinor:
    def test_minor_mentionne_nouvelle_fonctionnalite(self, policy):
        lower = policy.lower()
        assert "fonctionnalité" in lower or "feature" in lower or "nouvelle" in lower

    def test_minor_mentionne_retrocompatible(self, policy):
        lower = policy.lower()
        assert "rétrocompatible" in lower or "compatible" in lower or "opt-in" in lower


# ---------------------------------------------------------------------------
# 5. Règles MAJOR
# ---------------------------------------------------------------------------


class TestReglesMajor:
    def test_major_mentionne_rupture(self, policy):
        lower = policy.lower()
        assert "rupture" in lower or "breaking" in lower or "incompatible" in lower

    def test_major_mentionne_suppression_api(self, policy):
        lower = policy.lower()
        assert "suppression" in lower or "supprimé" in lower or "remove" in lower

    def test_major_mentionne_changement_cli(self, policy):
        lower = policy.lower()
        assert "cli" in lower


# ---------------------------------------------------------------------------
# 6. API publique et contrat de stabilité
# ---------------------------------------------------------------------------


class TestApiPublique:
    def test_mentionne_api_publique(self, policy):
        lower = policy.lower()
        assert "api" in lower and ("publique" in lower or "stable" in lower)

    def test_mentionne_api_interne(self, policy):
        lower = policy.lower()
        assert "interne" in lower or "internal" in lower

    def test_mentionne_experimentale(self, policy):
        lower = policy.lower()
        assert "expérimental" in lower or "experimental" in lower

    def test_reference_contrat_stabilite(self, policy):
        assert "stability-contract" in policy or "stabilité" in policy.lower()


# ---------------------------------------------------------------------------
# 7. Règles Git et tags
# ---------------------------------------------------------------------------


class TestReglesGitEtTags:
    def test_mentionne_format_tag_vxyz(self, policy):
        assert "vX.Y.Z" in policy or "v2.2.0" in policy or "vx.y.z" in policy.lower()

    def test_mentionne_main_stable(self, policy):
        assert "main" in policy and "stable" in policy.lower()

    def test_mentionne_tag_annote(self, policy):
        assert "git tag -a" in policy or "annoté" in policy.lower() or "annote" in policy.lower()

    def test_mentionne_immuabilite_tag(self, policy):
        lower = policy.lower()
        assert "immuable" in lower or "immuabilité" in lower or "ne doit pas être déplacé" in lower or "ne pas" in lower

    def test_mentionne_git_push(self, policy):
        assert "git push" in policy


# ---------------------------------------------------------------------------
# 8. Validation obligatoire
# ---------------------------------------------------------------------------


class TestValidationObligatoire:
    def test_mentionne_pytest(self, policy):
        assert "pytest" in policy

    def test_mentionne_compileall(self, policy):
        assert "compileall" in policy

    def test_mentionne_ruff(self, policy):
        assert "ruff" in policy

    def test_mentionne_mkdocs_build_strict(self, policy):
        assert "mkdocs build --strict" in policy

    def test_mentionne_git_diff_check(self, policy):
        assert "git diff --check" in policy


# ---------------------------------------------------------------------------
# 9. Build wheel
# ---------------------------------------------------------------------------


class TestBuildWheel:
    def test_mentionne_python_build(self, policy):
        assert "python -m build" in policy

    def test_mentionne_dist(self, policy):
        assert "dist/" in policy or "dist/" in policy

    def test_mentionne_forge_version(self, policy):
        assert "forge --version" in policy

    def test_mentionne_validation_locale(self, policy):
        assert "release-local.md" in policy or "Validation locale" in policy


# ---------------------------------------------------------------------------
# 10. Cohérence de version
# ---------------------------------------------------------------------------


class TestCoherenceVersion:
    def test_mentionne_pyproject_toml(self, policy):
        assert "pyproject.toml" in policy

    def test_mentionne_forge_py(self, policy):
        assert "forge.py" in policy

    def test_mentionne_changelog_entree(self, policy):
        assert "CHANGELOG.md" in policy


# ---------------------------------------------------------------------------
# 11. Publication GitHub
# ---------------------------------------------------------------------------


class TestPublicationGithub:
    def test_mentionne_publication_github(self, policy):
        lower = policy.lower()
        assert "github" in lower

    def test_mentionne_release_github(self, policy):
        lower = policy.lower()
        assert "release" in lower and "github" in lower

    def test_mentionne_tag_pousse(self, policy):
        assert "git push origin" in policy


# ---------------------------------------------------------------------------
# 12. Publication PyPI
# ---------------------------------------------------------------------------


class TestPublicationPypi:
    def test_mentionne_pypi(self, policy):
        lower = policy.lower()
        assert "pypi" in lower

    def test_mentionne_twine(self, policy):
        assert "twine" in policy

    def test_mentionne_pypi_manuel(self, policy):
        lower = policy.lower()
        assert "manuel" in lower or "manuelle" in lower or "manuellement" in lower or "automatisé" in lower


# ---------------------------------------------------------------------------
# 13. Changelog
# ---------------------------------------------------------------------------


class TestChangelog:
    def test_mentionne_changelog(self, policy):
        assert "CHANGELOG" in policy or "changelog" in policy.lower()

    def test_mentionne_sections_changelog(self, policy):
        lower = policy.lower()
        assert "ajouté" in lower or "ajout" in lower or "Ajouté" in policy

    def test_mentionne_corrige(self, policy):
        lower = policy.lower()
        assert "corrigé" in lower or "correctif" in lower

    def test_mentionne_securite_changelog(self, policy):
        lower = policy.lower()
        assert "sécurité" in lower or "securite" in lower


# ---------------------------------------------------------------------------
# 14. Roadmap et tickets
# ---------------------------------------------------------------------------


class TestRoadmapEtTickets:
    def test_mentionne_roadmap(self, policy):
        lower = policy.lower()
        assert "roadmap" in lower

    def test_mentionne_ticket_livre(self, policy):
        lower = policy.lower()
        assert "livré" in lower or "terminé" in lower

    def test_mentionne_prochaine_priorite(self, policy):
        lower = policy.lower()
        assert "prochaine priorité" in lower or "priorité" in lower


# ---------------------------------------------------------------------------
# 15. Limites restantes
# ---------------------------------------------------------------------------


class TestLimitesRestantes:
    def test_mentionne_limites_restantes(self, policy):
        lower = policy.lower()
        assert "limite" in lower or "ne couvre pas" in lower

    def test_mentionne_release_deprecation(self, policy):
        assert "RELEASE-DEPRECATION-001" in policy

    def test_mentionne_release_compat(self, policy):
        assert "RELEASE-COMPAT-001" in policy

    def test_mentionne_release_migration(self, policy):
        assert "RELEASE-MIGRATION-GUIDE-001" in policy

    def test_mentionne_release_lts(self, policy):
        assert "RELEASE-LTS-001" in policy


# ---------------------------------------------------------------------------
# 16. Roadmap principale
# ---------------------------------------------------------------------------


class TestRoadmapPrincipale:
    def test_release_policy_dans_roadmap(self):
        roadmap = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
        assert "RELEASE-POLICY-001" in roadmap

    def test_release_deprecation_prochaine_priorite(self):
        roadmap = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
        assert "RELEASE-DEPRECATION-001" in roadmap
