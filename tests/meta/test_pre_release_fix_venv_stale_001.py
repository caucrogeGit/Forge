"""Tests PRE-RELEASE-FIX-VENV-STALE-001 : doc de synchronisation venv ajoutée."""
from __future__ import annotations

from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRIBUTING = PROJECT_ROOT / "CONTRIBUTING.md"


class TestContributingDocsVenvSync:
    """CONTRIBUTING.md documente la procédure de synchronisation venv."""

    def setup_method(self):
        self.content = CONTRIBUTING.read_text(encoding="utf-8")

    def test_synchronisation_keyword_present(self):
        assert "Synchronisation" in self.content, (
            "CONTRIBUTING.md devrait contenir le mot 'Synchronisation' "
            "(section sur la synchronisation venv après bump version)"
        )

    def test_venv_keyword_present(self):
        assert "venv" in self.content, (
            "CONTRIBUTING.md devrait mentionner 'venv' dans la section "
            "sur la synchronisation"
        )

    def test_wheel_keyword_present(self):
        assert "wheel" in self.content, (
            "CONTRIBUTING.md devrait mentionner 'wheel' dans la section "
            "sur la synchronisation"
        )

    def test_build_wheel_command_mentioned(self):
        assert "python -m build --wheel" in self.content, (
            "CONTRIBUTING.md devrait mentionner 'python -m build --wheel' "
            "pour régénérer le wheel après bump de version"
        )

    def test_force_reinstall_mentioned(self):
        assert "force-reinstall" in self.content, (
            "CONTRIBUTING.md devrait mentionner 'force-reinstall' "
            "pour réinstaller le wheel dans le venv"
        )

    def test_deferred_ticket_referenced(self):
        assert "PACKAGING-FORGE-MODULE-001" in self.content, (
            "CONTRIBUTING.md devrait référencer le ticket différé "
            "PACKAGING-FORGE-MODULE-001 (restructuration de forge.py)"
        )
