"""Garde-fou RELEASE-VALIDATION-ENV-LOCK-001.

Vérifie que docs/release-local.md contient les éléments d'un environnement
de validation release reproductible et explicite la distinction
validation locale / publication PyPI.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
RELEASE_LOCAL = PROJECT_ROOT / "docs" / "release-local.md"


def _text() -> str:
    if not RELEASE_LOCAL.exists():
        pytest.skip("docs/release-local.md n'existe pas")
    return RELEASE_LOCAL.read_text(encoding="utf-8")


class TestReleaseValidationEnvSection:
    """La documentation release-local.md contient la section d'environnement."""

    def test_section_environnement_presente(self):
        assert "Environnement de validation release" in _text(), (
            "docs/release-local.md doit contenir 'Environnement de validation release' "
            "(RELEASE-VALIDATION-ENV-LOCK-001)"
        )

    def test_pytest_mentionne(self):
        assert "pytest" in _text(), (
            "docs/release-local.md doit mentionner 'pytest' dans la procédure de validation"
        )

    def test_mkdocs_strict_mentionne(self):
        assert "mkdocs build --strict" in _text(), (
            "docs/release-local.md doit mentionner 'mkdocs build --strict'"
        )

    def test_python_build_mentionne(self):
        assert "python -m build" in _text(), (
            "docs/release-local.md doit mentionner 'python -m build'"
        )

    def test_twine_check_mentionne(self):
        assert "twine check dist/*" in _text(), (
            "docs/release-local.md doit mentionner 'twine check dist/*' "
            "comme validation locale"
        )

    def test_ne_publie_pas(self):
        text = _text()
        assert "ne publie" in text or "ne publie rien" in text, (
            "docs/release-local.md doit indiquer que la procédure ne publie rien"
        )

    def test_release_check_script_reference_ticket_22(self):
        text = _text()
        assert "scripts/release_check.sh" in text, (
            "docs/release-local.md doit référencer 'scripts/release_check.sh'"
        )
        assert "RELEASE-CHECK-SCRIPT-001" in text or "2.2" in text, (
            "docs/release-local.md doit indiquer que le script relève du ticket 2.2"
        )
