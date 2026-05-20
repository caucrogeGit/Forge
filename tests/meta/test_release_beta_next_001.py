"""
Garde-fous documentaires pour RELEASE-BETA-NEXT-001.
Vérifie la cohérence de la version 1.0.0b6 dans les fichiers clés.
"""

import pytest
from pathlib import Path

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
FORGE_PY = PROJECT_ROOT / "forge.py"
RELEASE_NOTES = PROJECT_ROOT / "docs/history/releases/release-1.0.0-beta.6.md"


# --- version dans les sources ---

def test_pyproject_mentions_b6():
    assert '1.0.0b6' in PYPROJECT.read_text()


def test_forge_py_mentions_b6():
    content = FORGE_PY.read_text()
    assert '1.0.0b6' in content or '1.0.0-beta.6' in content


# --- notes de release ---

def test_release_notes_exist():
    assert RELEASE_NOTES.exists(), f"Notes de release introuvables : {RELEASE_NOTES}"


def test_release_notes_not_empty():
    assert RELEASE_NOTES.stat().st_size > 300


def test_release_notes_mentions_version():
    content = RELEASE_NOTES.read_text()
    assert '1.0.0-beta.6' in content or '1.0.0b6' in content


def test_release_notes_mentions_rbac():
    assert 'RBAC' in RELEASE_NOTES.read_text()


def test_release_notes_mentions_pivot_advanced():
    content = RELEASE_NOTES.read_text()
    assert 'Pivot advanced' in content or 'pivot-advanced' in content


def test_release_notes_mentions_make_pivot_crud():
    assert 'make:pivot-crud' in RELEASE_NOTES.read_text()


def test_release_notes_mentions_field_test():
    assert 'FIELD-TEST-APP-001' in RELEASE_NOTES.read_text()


def test_release_notes_mentions_f001():
    assert 'F-001' in RELEASE_NOTES.read_text()


def test_release_notes_mentions_f002():
    assert 'F-002' in RELEASE_NOTES.read_text()


def test_release_notes_mentions_f003():
    assert 'F-003' in RELEASE_NOTES.read_text()


def test_release_notes_confirms_no_pypi():
    content = RELEASE_NOTES.read_text()
    assert 'PyPI' in content
    assert 'Aucune publication' in content or 'NON' in content or 'pas de publication' in content.lower()


def test_release_notes_not_claiming_stable():
    content = RELEASE_NOTES.read_text()
    assert 'stable' not in content.lower() or 'bêta' in content.lower() or 'beta' in content.lower()


def test_release_notes_not_claiming_pypi_published():
    content = RELEASE_NOTES.read_text()
    assert 'publié sur PyPI' not in content
    assert 'twine upload' not in content
