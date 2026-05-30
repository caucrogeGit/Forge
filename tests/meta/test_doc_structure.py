"""Tests documentaires — DOC-STRUCTURE-001 : organisation de la documentation par parcours."""

from pathlib import Path
import pytest

pytestmark = pytest.mark.meta

MKDOCS = Path("mkdocs.yml")
ROADMAP = Path("docs/roadmap/forge-roadmap.md")


def _mkdocs():
    return MKDOCS.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence des pages clés
# ---------------------------------------------------------------------------


class TestPagesExistent:
    def test_index_existe(self):
        assert Path("docs/index.html").exists() or Path("docs/index.md").exists()

    def test_guide_existe(self):
        assert Path("docs/guide/guide.md").exists()

    def test_reference_existe(self):
        assert Path("docs/reference/reference.md").exists()

    def test_auth_existe(self):
        assert Path("docs/features/auth.md").exists()

    def test_security_existe(self):
        assert Path("docs/philosophy/security.md").exists()

    def test_rbac_existe(self):
        assert Path("docs/features/rbac.md").exists()

    def test_deployment_existe(self):
        assert Path("docs/deployment/deployment.md").exists()

    def test_production_security_existe(self):
        assert Path("docs/deployment/production-security.md").exists()

    def test_stability_contract_existe(self):
        assert Path("docs/release/stability-contract.md").exists()

    def test_release_policy_existe(self):
        assert Path("docs/release/release-policy.md").exists()

    def test_deprecation_policy_existe(self):
        assert Path("docs/release/deprecation-policy.md").exists()

    def test_compatibility_existe(self):
        assert Path("docs/release/compatibility.md").exists()

    def test_migration_guide_existe(self):
        assert Path("docs/features/migration-guide.md").exists()

    def test_lts_policy_existe(self):
        assert Path("docs/release/lts-policy.md").exists()

    def test_release_and_compatibility_existe(self):
        assert Path("docs/release/release-and-compatibility.md").exists()

    def test_starters_index_existe(self):
        assert Path("docs/starters/index.md").exists()


# ---------------------------------------------------------------------------
# Structure mkdocs.yml — grands parcours
# ---------------------------------------------------------------------------


class TestMkdocsStructure:
    def test_section_installation(self):
        assert "Installation" in _mkdocs()

    def test_section_premiers_pas(self):
        assert "Premiers pas" in _mkdocs()

    def test_section_concepts(self):
        mkdocs = _mkdocs()
        assert "Concepts" in mkdocs or "Comprendre" in mkdocs

    def test_section_reference(self):
        assert "Référence" in _mkdocs()

    def test_section_deploiement(self):
        assert "Déploiement" in _mkdocs()

    def test_section_release_et_compatibilite(self):
        mkdocs = _mkdocs()
        assert "Release et compatibilité" in mkdocs or "release-and-compatibility" in mkdocs

    def test_section_modules_ou_starters(self):
        mkdocs = _mkdocs()
        assert "Modules" in mkdocs or "starters" in mkdocs.lower()

    def test_section_projet(self):
        assert "Projet" in _mkdocs()


# ---------------------------------------------------------------------------
# Pages de release accessibles dans la navigation
# ---------------------------------------------------------------------------


class TestReleaseNavigation:
    def test_release_policy_dans_nav(self):
        assert "release-policy.md" in _mkdocs()

    def test_deprecation_policy_dans_nav(self):
        assert "deprecation-policy.md" in _mkdocs()

    def test_compatibility_dans_nav(self):
        assert "compatibility.md" in _mkdocs()

    def test_migration_guide_dans_nav(self):
        assert "migration-guide.md" in _mkdocs()

    def test_lts_policy_dans_nav(self):
        assert "lts-policy.md" in _mkdocs()

    def test_stability_contract_dans_nav(self):
        assert "stability-contract.md" in _mkdocs()

    def test_vue_ensemble_release_dans_nav(self):
        assert "release-and-compatibility.md" in _mkdocs()


# ---------------------------------------------------------------------------
# Pages sécurité accessibles dans la navigation
# ---------------------------------------------------------------------------


class TestSecuriteNavigation:
    def test_security_dans_nav(self):
        assert "security.md" in _mkdocs()

    def test_production_security_dans_nav(self):
        assert "production-security.md" in _mkdocs()

    def test_rbac_dans_nav(self):
        assert "rbac.md" in _mkdocs()

    def test_auth_dans_nav(self):
        assert "auth.md" in _mkdocs()


# ---------------------------------------------------------------------------
# Page d'entrée Release et compatibilité
# ---------------------------------------------------------------------------


class TestReleaseAndCompatibilityPage:
    def test_page_existe(self):
        assert Path("docs/release/release-and-compatibility.md").exists()

    def test_lien_release_policy(self):
        text = Path("docs/release/release-and-compatibility.md").read_text(encoding="utf-8")
        assert "release-policy.md" in text or "Politique de release" in text

    def test_lien_deprecation_policy(self):
        text = Path("docs/release/release-and-compatibility.md").read_text(encoding="utf-8")
        assert "deprecation-policy.md" in text or "Politique de dépréciation" in text

    def test_lien_compatibility(self):
        text = Path("docs/release/release-and-compatibility.md").read_text(encoding="utf-8")
        assert "compatibility.md" in text or "Matrice de compatibilité" in text

    def test_lien_migration_guide(self):
        text = Path("docs/release/release-and-compatibility.md").read_text(encoding="utf-8")
        assert "migration-guide.md" in text or "Guide de migration" in text

    def test_lien_lts_policy(self):
        text = Path("docs/release/release-and-compatibility.md").read_text(encoding="utf-8")
        assert "lts-policy.md" in text or "Politique LTS" in text

    def test_lien_stability_contract(self):
        text = Path("docs/release/release-and-compatibility.md").read_text(encoding="utf-8")
        assert "stability-contract.md" in text or "Contrat de stabilité" in text


# ---------------------------------------------------------------------------
# Liens croisés entre docs de release
# ---------------------------------------------------------------------------


class TestLiensCroisesRelease:
    def test_release_policy_lien_vers_deprecation(self):
        text = Path("docs/release/release-policy.md").read_text(encoding="utf-8")
        assert "deprecation-policy.md" in text or "dépréciation" in text.lower()

    def test_deprecation_policy_lien_vers_release(self):
        text = Path("docs/release/deprecation-policy.md").read_text(encoding="utf-8")
        assert "release-policy.md" in text or "politique de release" in text.lower()

    def test_migration_guide_lien_vers_compatibility(self):
        text = Path("docs/features/migration-guide.md").read_text(encoding="utf-8")
        assert "compatibility.md" in text or "compatibilité" in text.lower()

    def test_lts_policy_lien_vers_stability(self):
        text = Path("docs/release/lts-policy.md").read_text(encoding="utf-8")
        assert "stability-contract.md" in text or "contrat de stabilité" in text.lower()


# ---------------------------------------------------------------------------
# Futurs tickets DOC dans la roadmap
# ---------------------------------------------------------------------------


class TestFutursTicketsDoc:
    def test_doc_15min_dans_roadmap(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-15MIN-001" in text

    def test_doc_app_complete_dans_roadmap(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-APP-COMPLETE-001" in text

    def test_doc_contribute_dans_roadmap(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-CONTRIBUTE-001" in text

    def test_doc_deploy_advanced_dans_roadmap(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-DEPLOY-ADVANCED-001" in text


# ---------------------------------------------------------------------------
# Mkdocs build et roadmap
# ---------------------------------------------------------------------------


class TestMkdocsBuild:
    def test_mkdocs_build_strict(self):
        import subprocess

        result = subprocess.run(
            ["mkdocs", "build", "--strict"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"mkdocs build --strict a échoué :\n{result.stderr}"


class TestRoadmap:
    def test_ticket_livre_dans_roadmap(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-STRUCTURE-001" in text

    def test_ticket_marque_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "DOC-STRUCTURE-001" in line:
                assert "livré" in line.lower() or "terminé" in line.lower(), (
                    f"DOC-STRUCTURE-001 non marqué comme livré : {line}"
                )
                break

    def test_prochaine_priorite_doc_15min(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "DOC-15MIN-001" in text
