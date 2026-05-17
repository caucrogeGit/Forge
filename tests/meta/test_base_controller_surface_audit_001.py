"""Garde-fou BASE-CONTROLLER-SURFACE-AUDIT-001.

Vérifie que le rapport d'audit de la surface publique de BaseController existe
et couvre les sections et éléments attendus.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIT = PROJECT_ROOT / "docs" / "history" / "audits" / "base-controller-surface-audit-001.md"


@pytest.fixture(scope="module")
def report() -> str:
    assert AUDIT.exists(), f"Rapport introuvable : {AUDIT}"
    return AUDIT.read_text(encoding="utf-8")


class TestReportExists:

    def test_fichier_existe(self):
        assert AUDIT.exists()

    def test_fichier_non_vide(self, report):
        assert len(report) > 2000

    def test_ticket_reference(self, report):
        assert "BASE-CONTROLLER-SURFACE-AUDIT-001" in report


class TestBaseControllerMentionne:

    def test_base_controller_present(self, report):
        assert "BaseController" in report

    def test_methodes_principales_presentes(self, report):
        assert "render" in report
        assert "redirect" in report
        assert "current_user" in report
        assert "set_flash" in report
        assert "csrf_token" in report


class TestSectionsRequises:

    def test_section_objectif(self, report):
        assert "Objectif" in report

    def test_section_methode(self, report):
        lower = report.lower()
        assert "méthode" in lower or "methode" in lower

    def test_section_synthese(self, report):
        lower = report.lower()
        assert "synthèse" in lower or "synthese" in lower

    def test_section_surface_publique(self, report):
        lower = report.lower()
        assert "surface" in lower

    def test_section_usages(self, report):
        lower = report.lower()
        assert "usages" in lower or "usage" in lower

    def test_section_risques(self, report):
        lower = report.lower()
        assert "risque" in lower

    def test_section_tickets_futurs(self, report):
        lower = report.lower()
        assert "tickets futurs" in lower or "ticket futur" in lower

    def test_section_conclusion(self, report):
        assert "Conclusion" in report


class TestStatutsClassification:

    def test_statut_canonique(self, report):
        assert "CANONIQUE" in report

    def test_statut_legacy(self, report):
        assert "LEGACY" in report

    def test_statut_surveiller(self, report):
        assert "À_SURVEILLER" in report or "surveiller" in report.lower()

    def test_statut_migrer(self, report):
        assert "À_MIGRER" in report or "migrer" in report.lower()


class TestSessionAPI:

    def test_core_security_session_mentionne(self, report):
        assert "core.security.session" in report

    def test_core_auth_session_mentionne(self, report):
        assert "core.auth.session" in report

    def test_get_user_deprecated_identifie(self, report):
        lower = report.lower()
        assert "get_user" in lower
        assert "déprécié" in lower or "depreci" in lower or "DeprecationWarning" in report

    def test_current_user_legacy_identifie(self, report):
        assert "current_user" in report
        lower = report.lower()
        assert "legacy" in lower or "déprécié" in lower or "migrer" in lower


class TestRuntimeNonModifie:

    def test_audit_uniquement(self, report):
        lower = report.lower()
        assert "ne modifie" in lower or "aucun fichier runtime" in lower or "audit" in lower

    def test_aucune_suppression_api(self, report):
        lower = report.lower()
        assert "api supprimée" not in lower
        assert "méthode supprimée" not in lower
