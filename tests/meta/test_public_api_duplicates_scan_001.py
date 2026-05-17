"""Garde-fou PUBLIC-API-DUPLICATES-SCAN-001.

Vérifie que le rapport d'audit des doublons d'API publique existe et contient
les sections et familles attendues. Ce test protège l'existence du rapport,
pas sa mise en forme exacte.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIT_REPORT = PROJECT_ROOT / "docs" / "history" / "audits" / "public-api-duplicates-scan-001.md"


@pytest.fixture(scope="module")
def report() -> str:
    assert AUDIT_REPORT.exists(), (
        f"Rapport d'audit introuvable : {AUDIT_REPORT}. "
        "Ce fichier doit être créé par PUBLIC-API-DUPLICATES-SCAN-001."
    )
    return AUDIT_REPORT.read_text(encoding="utf-8")


class TestReportExists:
    """Le rapport d'audit existe et référence le ticket."""

    def test_fichier_existe(self):
        assert AUDIT_REPORT.exists()

    def test_fichier_non_vide(self, report):
        assert len(report) > 1000

    def test_ticket_reference(self, report):
        assert "PUBLIC-API-DUPLICATES-SCAN-001" in report


class TestFamillesAuditees:
    """Le rapport couvre les 7 familles requises."""

    def test_famille_auth_session(self, report):
        lower = report.lower()
        assert "auth" in lower and "session" in lower

    def test_famille_csrf(self, report):
        assert "CSRF" in report or "csrf" in report.lower()

    def test_famille_modules(self, report):
        lower = report.lower()
        assert "module" in lower

    def test_famille_rbac(self, report):
        assert "RBAC" in report or "rbac" in report.lower()

    def test_famille_mfa(self, report):
        assert "MFA" in report or "mfa" in report.lower()

    def test_famille_cli(self, report):
        assert "CLI" in report or "cli" in report.lower()

    def test_famille_packaging(self, report):
        lower = report.lower()
        assert "packaging" in lower or "paquet" in lower or "pypi" in lower


class TestStatutsClassification:
    """Le rapport utilise les statuts de classification requis."""

    def test_statut_canonique(self, report):
        assert "CANONIQUE" in report

    def test_statut_legacy(self, report):
        assert "LEGACY" in report or "legacy" in report.lower()

    def test_statut_faux_positif(self, report):
        assert "FAUX_POSITIF" in report or "faux positif" in report.lower()

    def test_statut_surveiller(self, report):
        assert "À_SURVEILLER" in report or "surveiller" in report.lower()


class TestSectionsRequises:
    """Le rapport contient les sections structurelles attendues."""

    def test_section_objectif(self, report):
        assert "Objectif" in report

    def test_section_methode(self, report):
        lower = report.lower()
        assert "méthode" in lower or "methode" in lower

    def test_section_tickets_futurs(self, report):
        lower = report.lower()
        assert "tickets futurs" in lower or "ticket futur" in lower

    def test_section_conclusion(self, report):
        assert "Conclusion" in report

    def test_section_doublons(self, report):
        lower = report.lower()
        assert "doublon" in lower


class TestInterditsDeSuppressionAPI:
    """Le rapport ne prétend pas avoir supprimé des API publiques."""

    def test_aucune_suppression_api(self, report):
        lower = report.lower()
        assert "api supprimée" not in lower
        assert "api supprimé" not in lower
        assert "api publique supprimée" not in lower

    def test_audit_uniquement(self, report):
        lower = report.lower()
        assert "audit" in lower
