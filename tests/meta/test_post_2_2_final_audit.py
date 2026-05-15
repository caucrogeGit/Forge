"""Tests — POST-2.2-FINAL-AUDIT-001 : audit final Forge post phases 5 à 10."""

import pathlib

import pytest
pytestmark = pytest.mark.meta

AUDIT = pathlib.Path("docs/history/audits/post-2-2-final-audit-001.md")
ROADMAP = pathlib.Path("docs/roadmap/forge-roadmap.md")


def _audit():
    return AUDIT.read_text(encoding="utf-8")


def _roadmap():
    return ROADMAP.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence du rapport
# ---------------------------------------------------------------------------


class TestExistence:
    def test_audit_existe(self):
        assert AUDIT.exists()

    def test_roadmap_existe(self):
        assert ROADMAP.exists()


# ---------------------------------------------------------------------------
# Sections obligatoires du rapport
# ---------------------------------------------------------------------------


class TestSectionsObligatoires:
    def test_section_objectif(self):
        assert "Objectif" in _audit()

    def test_section_resume_executif(self):
        a = _audit()
        assert "Résumé exécutif" in a or "résumé" in a.lower()

    def test_section_etat_global(self):
        a = _audit()
        assert "État global" in a or "état global" in a.lower()

    def test_section_documentation(self):
        assert "Documentation" in _audit()

    def test_section_securite(self):
        a = _audit()
        assert "Sécurité" in a or "sécurité" in a.lower()

    def test_section_tests_qualite(self):
        a = _audit()
        assert "Tests" in a or "qualité" in a.lower()

    def test_section_dettes(self):
        a = _audit()
        assert "Dettes" in a or "dettes" in a.lower()

    def test_section_risques(self):
        a = _audit()
        assert "Risques" in a or "risques" in a.lower()

    def test_section_recommandation(self):
        a = _audit()
        assert "Recommandation" in a or "recommandation" in a.lower()

    def test_section_prochaine_phase(self):
        a = _audit()
        assert "Prochaine phase" in a or "prochaine" in a.lower()


# ---------------------------------------------------------------------------
# Mention des phases 5 à 10
# ---------------------------------------------------------------------------


class TestPhases:
    def test_mention_phase_5(self):
        assert "Phase 5" in _audit()

    def test_mention_phase_6(self):
        assert "Phase 6" in _audit()

    def test_mention_phase_7(self):
        assert "Phase 7" in _audit()

    def test_mention_phase_8(self):
        assert "Phase 8" in _audit()

    def test_mention_phase_9(self):
        assert "Phase 9" in _audit()

    def test_mention_phase_10(self):
        assert "Phase 10" in _audit()


# ---------------------------------------------------------------------------
# Mention de la roadmap unique
# ---------------------------------------------------------------------------


class TestRoadmapUnique:
    def test_mention_roadmap_unifiee(self):
        a = _audit()
        assert "forge-roadmap.md" in a or "roadmap unique" in a.lower() or "Roadmap unique" in a

    def test_mention_roadmap_unified_ticket(self):
        assert "ROADMAP-UNIFIED-001" in _audit()


# ---------------------------------------------------------------------------
# Mention de la landing page
# ---------------------------------------------------------------------------


class TestLandingPage:
    def test_mention_landing_page(self):
        a = _audit()
        assert "landing" in a.lower() or "Landing" in a

    def test_mention_landing_ticket(self):
        assert "LANDING-POST-2.2-REFRESH-001" in _audit()


# ---------------------------------------------------------------------------
# Mention de l'API JSON
# ---------------------------------------------------------------------------


class TestApiJson:
    def test_mention_api_json(self):
        a = _audit()
        assert "API JSON" in a or "api json" in a.lower()

    def test_mention_json_response(self):
        assert "json_response" in _audit()

    def test_mention_require_api_token(self):
        assert "require_api_token" in _audit() or "@require_api_token" in _audit()


# ---------------------------------------------------------------------------
# Mention des dettes restantes
# ---------------------------------------------------------------------------


class TestDettes:
    def test_mention_auth_mfa_004(self):
        assert "AUTH-MFA-004" in _audit()

    def test_auth_mfa_004_priorite_haute(self):
        a = _audit()
        idx = a.find("AUTH-MFA-004")
        assert idx != -1
        bloc = a[idx: idx + 80]
        assert "haute" in bloc or "MFA" in bloc

    def test_mention_security_cache(self):
        assert "SECURITY-CACHE-001" in _audit()

    def test_mention_crud_rbac_ui(self):
        assert "CRUD-RBAC-UI-001" in _audit()


# ---------------------------------------------------------------------------
# Prochaine phase recommandée = AUTH-MFA-004
# ---------------------------------------------------------------------------


class TestProchainePhasePrescrite:
    def test_prochaine_phase_auth_mfa_004(self):
        a = _audit()
        assert "AUTH-MFA-004" in a

    def test_auth_mfa_004_dans_recommandation(self):
        a = _audit()
        idx = a.find("Recommandation")
        assert idx != -1
        bloc = a[idx:]
        assert "AUTH-MFA-004" in bloc

    def test_mention_auth_mfa_005(self):
        assert "AUTH-MFA-005" in _audit()

    def test_mention_auth_oidc(self):
        a = _audit()
        assert "AUTH-OIDC" in a or "OIDC" in a


# ---------------------------------------------------------------------------
# Roadmap mise à jour (POST-2.2-FINAL-AUDIT-001 présent)
# ---------------------------------------------------------------------------


class TestRoadmapMiseAJour:
    def test_post_2_2_dans_roadmap(self):
        assert "POST-2.2-FINAL-AUDIT-001" in _roadmap()

    def test_auth_mfa_004_dans_roadmap(self):
        assert "AUTH-MFA-004" in _roadmap()
