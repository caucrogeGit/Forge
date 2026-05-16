"""Garde-fou RELEASE-CHECK-SCRIPT-001.

Vérifie que scripts/release_check.sh existe, est exécutable,
et contient les commandes de validation attendues sans commande de publication.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "release_check.sh"


def _text() -> str:
    if not SCRIPT.exists():
        pytest.skip("scripts/release_check.sh n'existe pas")
    return SCRIPT.read_text(encoding="utf-8")


class TestReleaseCheckScript:
    """scripts/release_check.sh existe et contient la logique attendue."""

    def test_script_existe(self):
        assert SCRIPT.exists(), (
            "scripts/release_check.sh doit exister (RELEASE-CHECK-SCRIPT-001)"
        )

    def test_script_executable(self):
        assert os.access(SCRIPT, os.X_OK), (
            "scripts/release_check.sh doit être exécutable"
        )

    def test_set_euo_pipefail(self):
        assert "set -euo pipefail" in _text(), (
            "scripts/release_check.sh doit déclarer 'set -euo pipefail'"
        )

    def test_contient_pytest(self):
        assert "pytest" in _text(), (
            "scripts/release_check.sh doit lancer pytest"
        )

    def test_contient_mkdocs_strict(self):
        assert "mkdocs build --strict" in _text(), (
            "scripts/release_check.sh doit lancer 'mkdocs build --strict'"
        )

    def test_contient_python_build(self):
        assert "python -m build" in _text(), (
            "scripts/release_check.sh doit inclure 'python -m build'"
        )

    def test_contient_twine_check(self):
        assert "twine check" in _text(), (
            "scripts/release_check.sh doit inclure 'twine check'"
        )

    def test_ne_contient_pas_twine_upload(self):
        assert "twine upload" not in _text(), (
            "scripts/release_check.sh ne doit pas contenir 'twine upload' — "
            "ce script ne publie rien"
        )
