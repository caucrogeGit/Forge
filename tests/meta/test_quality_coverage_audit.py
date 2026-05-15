"""
Tests documentaires QUALITY-COVERAGE-001 — Rapport d'audit de couverture.

Vérifie que le rapport docs/history/audits/quality-coverage-001.md :
  - existe ;
  - contient les sections obligatoires ;
  - mentionne les familles de tests principales ;
  - recense les tests E2E livrés ;
  - signale E2E-MARIADB-001 comme opt-in ;
  - liste les risques avant la phase sécurité ;
  - propose des recommandations ;
  - propose des tickets suivants.
"""
from __future__ import annotations

from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parent.parent.parent
AUDIT = (ROOT / "docs" / "history" / "audits" / "quality-coverage-001.md").read_text(encoding="utf-8")
ROADMAP = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")


# ── Existence et structure ────────────────────────────────────────────────────

def test_rapport_existe():
    assert (ROOT / "docs" / "history" / "audits" / "quality-coverage-001.md").exists()


def test_rapport_titre():
    assert "QUALITY-COVERAGE-001" in AUDIT


def test_section_objectif():
    assert "## Objectif" in AUDIT


def test_section_resume_executif():
    assert "Résumé exécutif" in AUDIT


def test_section_etat_global():
    assert "État global des tests" in AUDIT


def test_section_couverture_par_famille():
    assert "Couverture par famille" in AUDIT


def test_section_zones_fortes():
    assert "Zones fortement couvertes" in AUDIT


def test_section_zones_partielles():
    assert "Zones partiellement couvertes" in AUDIT


def test_section_zones_faibles():
    assert "non couvertes" in AUDIT or "insuffisantes" in AUDIT


def test_section_tests_e2e_existants():
    assert "Tests E2E existants" in AUDIT


def test_section_tests_e2e_manquants():
    assert "Tests E2E manquants" in AUDIT


def test_section_tests_opt_in():
    assert "opt-in" in AUDIT.lower() or "Tests opt-in" in AUDIT


def test_section_tests_fragiles():
    assert "fragiles" in AUDIT.lower() or "surveiller" in AUDIT.lower()


def test_section_risques():
    assert "Risques" in AUDIT


def test_section_recommandations():
    assert "Recommandations" in AUDIT


def test_section_tickets_proposes():
    assert "Tickets proposés" in AUDIT or "tickets" in AUDIT.lower()


# ── Familles de tests mentionnées ─────────────────────────────────────────────

def test_mentionne_auth():
    assert "Auth" in AUDIT


def test_mentionne_crud():
    assert "CRUD" in AUDIT


def test_mentionne_cli():
    assert "CLI" in AUDIT


def test_mentionne_modules():
    assert "Modules" in AUDIT


def test_mentionne_starters():
    assert "Starters" in AUDIT


def test_mentionne_migrations():
    assert "Migration" in AUDIT


def test_mentionne_securite():
    assert "sécurité" in AUDIT.lower() or "Sécurité" in AUDIT


def test_mentionne_uploads_media():
    assert "Upload" in AUDIT or "Média" in AUDIT or "Uploads" in AUDIT


def test_mentionne_mail():
    assert "Mail" in AUDIT


def test_mentionne_runtime_errors():
    assert "Runtime" in AUDIT or "runtime" in AUDIT


def test_mentionne_templates():
    assert "Template" in AUDIT


def test_mentionne_session():
    assert "Session" in AUDIT


# ── Tests E2E livrés recensés ─────────────────────────────────────────────────

def test_recense_e2e_cli_001():
    assert "E2E-CLI-001" in AUDIT


def test_recense_e2e_non_overwrite():
    assert "E2E-NON-OVERWRITE-001" in AUDIT or "NON-OVERWRITE" in AUDIT


def test_recense_e2e_starter_001():
    assert "E2E-STARTER-001" in AUDIT


def test_recense_e2e_module_001():
    assert "E2E-MODULE-001" in AUDIT


def test_recense_e2e_mariadb_001():
    assert "E2E-MARIADB-001" in AUDIT


def test_e2e_mariadb_signale_opt_in():
    assert "E2E-MARIADB-001" in AUDIT
    assert "opt-in" in AUDIT.lower() or "FORGE_E2E_MARIADB" in AUDIT


def test_recense_http_e2e():
    assert "test_http_e2e_001" in AUDIT or "HTTP-E2E" in AUDIT


# ── Risques avant sécurité mentionnés ─────────────────────────────────────────

def test_risque_csrf_mentionne():
    assert "CSRF" in AUDIT


def test_risque_mariadb_ci_mentionne():
    assert "CI" in AUDIT


def test_risque_upload_mentionne():
    assert "upload" in AUDIT.lower() or "Upload" in AUDIT


# ── Recommandations et tickets ────────────────────────────────────────────────

def test_security_audit_001_recommande():
    assert "SECURITY-AUDIT-001" in AUDIT


def test_recommandations_non_vides():
    idx = AUDIT.find("## Recommandations")
    assert idx != -1
    section = AUDIT[idx:idx + 500]
    assert len(section.strip()) > 50


# ── Roadmap mise à jour ───────────────────────────────────────────────────────

def test_roadmap_mentionne_quality_coverage_livre():
    assert "QUALITY-COVERAGE-001" in ROADMAP


def test_roadmap_prochaine_priorite_security_audit():
    assert "SECURITY-AUDIT-001" in ROADMAP
