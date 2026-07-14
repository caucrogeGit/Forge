"""
Garde-fous documentaires pour FIELD-TEST-APP-001.
Vérifie la présence et le contenu du rapport de terrain.
"""

import pytest
from pathlib import Path

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "docs/history/field-tests/field-test-app-001.md"


# --- existence ---

def test_report_exists():
    assert REPORT.exists(), f"Rapport introuvable : {REPORT}"


def test_report_not_empty():
    assert REPORT.stat().st_size > 500


# --- structure du rapport ---

def test_report_has_ticket_reference():
    assert "FIELD-TEST-APP-001" in REPORT.read_text()


def test_report_has_date():
    assert "2026-05-20" in REPORT.read_text()


def test_report_has_friction_section():
    assert "## 3. Frictions" in REPORT.read_text()


def test_report_has_generated_files_section():
    assert "## 4. Fichiers générés" in REPORT.read_text()


def test_report_has_verdict():
    assert "FIELD TEST OK" in REPORT.read_text()


# --- frictions documentées ---

def test_report_documents_name_key_friction():
    content = REPORT.read_text()
    assert "F-001" in content
    assert '"name"' in content


def test_report_documents_directory_structure_friction():
    content = REPORT.read_text()
    assert "F-002" in content
    assert "build:model" in content


def test_report_documents_make_crud_guard_friction():
    content = REPORT.read_text()
    assert "F-003" in content
    assert "make:crud" in content


def test_report_mentions_both_sides_guard():
    assert "côté `from`" in REPORT.read_text() or "coté" in REPORT.read_text()


# --- entités déclarées ---

def test_report_mentions_article_entity():
    assert "Article" in REPORT.read_text()


def test_report_mentions_tag_entity():
    assert "Tag" in REPORT.read_text()


def test_report_mentions_pivot_table():
    assert "article_tag" in REPORT.read_text()


# --- commandes exécutées ---

@pytest.mark.parametrize("cmd", [
    "entity:validate",
    "build:model",
    "make:crud Article",
    "make:crud Tag",
    "make:pivot-crud Article tags",
    "rbac:validate",
    "rbac:audit",
])
def test_report_documents_command(cmd):
    assert cmd in REPORT.read_text(), f"Commande non documentée : {cmd!r}"


# --- points positifs ---

def test_report_mentions_write_if_new():
    content = REPORT.read_text()
    assert "write-if-new" in content or "PRÉSERVÉ" in content


def test_report_mentions_rbac_ok():
    content = REPORT.read_text()
    assert "rbac:validate" in content
    assert "OK" in content


def test_report_mentions_dry_run():
    assert "--dry-run" in REPORT.read_text()
