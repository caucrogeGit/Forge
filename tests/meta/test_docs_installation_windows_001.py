"""Garde-fou DOCS-INSTALLATION-WINDOWS-001.

Vérifie que la doc d'installation Windows (WSL2) existe et est correctement
référencée depuis les points d'entrée de la documentation.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
WINDOWS_DOC = PROJECT_ROOT / "docs" / "installation-windows.md"


class TestInstallationWindowsDocExists:

    def test_file_exists(self):
        assert WINDOWS_DOC.exists(), (
            "docs/installation-windows.md doit exister."
        )

    def test_mentions_wsl2(self):
        text = WINDOWS_DOC.read_text(encoding="utf-8")
        assert "WSL2" in text, (
            "docs/installation-windows.md doit mentionner WSL2."
        )

    def test_mentions_microsoft_docs(self):
        text = WINDOWS_DOC.read_text(encoding="utf-8")
        assert "microsoft.com" in text.lower(), (
            "Le guide doit pointer vers la documentation Microsoft pour WSL2."
        )

    def test_mentions_frictions_natives(self):
        text = WINDOWS_DOC.read_text(encoding="utf-8")
        assert "natif" in text.lower() or "frictions" in text.lower(), (
            "Le guide doit mentionner les limites du support natif Windows."
        )


class TestWindowsDocReferenced:

    def test_getting_started_links_to_windows(self):
        text = (PROJECT_ROOT / "docs" / "getting-started.md").read_text(encoding="utf-8")
        assert "installation-windows" in text, (
            "docs/getting-started.md doit lier vers installation-windows.md."
        )

    def test_landing_mentions_windows(self):
        text = (PROJECT_ROOT / "mvc" / "views" / "landing" / "index.html").read_text(encoding="utf-8")
        assert "installation-windows" in text or "Windows" in text, (
            "La landing (source) doit mentionner Windows ou installation-windows."
        )

    def test_mkdocs_nav_includes_windows(self):
        text = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        assert "installation-windows" in text, (
            "mkdocs.yml nav doit inclure installation-windows.md."
        )
