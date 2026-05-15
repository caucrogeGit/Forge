"""Tests PRE-RELEASE-FIX-LANDING-CSS-SYNC-001 : forge sync:landing copie HTML + assets."""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
STATIC_SRC = PROJECT_ROOT / "static" / "tailwind.css"
STATIC_DST = PROJECT_ROOT / "docs" / "static" / "tailwind.css"
SYNC_LANDING_MODULE = PROJECT_ROOT / "forge_cli" / "sync_landing.py"
PACKAGE_JSON = PROJECT_ROOT / "package.json"
CONTRIBUTING = PROJECT_ROOT / "CONTRIBUTING.md"


class TestCSSSourceExists:
    """static/tailwind.css existe et est non vide."""

    def test_static_tailwind_exists(self):
        assert STATIC_SRC.exists(), (
            "static/tailwind.css doit exister (source canonique CSS, "
            "généré par 'npm run build:css')"
        )

    def test_static_tailwind_not_empty(self):
        assert STATIC_SRC.stat().st_size > 1000, (
            "static/tailwind.css devrait avoir un contenu substantiel (>1000 octets)"
        )


class TestCSSSynchronized:
    """docs/static/tailwind.css est synchronisé avec static/tailwind.css."""

    def test_docs_tailwind_exists(self):
        assert STATIC_DST.exists(), (
            "docs/static/tailwind.css doit exister (copie pour le site MkDocs, "
            "synchronisée par forge sync:landing)"
        )

    def test_same_size_as_source(self):
        size_src = STATIC_SRC.stat().st_size
        size_dst = STATIC_DST.stat().st_size
        assert size_src == size_dst, (
            f"docs/static/tailwind.css ({size_dst} o) devrait avoir la même "
            f"taille que static/tailwind.css ({size_src} o). "
            f"Lancer 'forge sync:landing' pour synchroniser."
        )


class TestSyncLandingHandlesStatic:
    """forge_cli/sync_landing.py contient la logique de copie des assets."""

    def setup_method(self):
        self.content = SYNC_LANDING_MODULE.read_text(encoding="utf-8")

    @pytest.mark.parametrize("marker", [
        "static",
        "docs/static",
    ])
    def test_module_mentions_static_path(self, marker):
        assert marker in self.content, (
            f"forge_cli/sync_landing.py devrait référencer '{marker}' "
            f"pour la copie des assets statiques"
        )

    def test_sync_static_function_exists(self):
        assert "def sync_static" in self.content, (
            "forge_cli/sync_landing.py devrait définir une fonction sync_static()"
        )

    def test_shutil_copy_used(self):
        assert "shutil" in self.content, (
            "forge_cli/sync_landing.py devrait utiliser shutil pour la copie des fichiers"
        )


class TestPackageJsonScript:
    """package.json a un script build:css correct (Tailwind v4)."""

    def test_build_css_uses_tailwindcss_cli(self):
        content = PACKAGE_JSON.read_text(encoding="utf-8")
        assert "@tailwindcss/cli" in content, (
            "package.json devrait utiliser '@tailwindcss/cli' "
            "(Tailwind v4 a déplacé le binaire)"
        )


class TestContributingDocumented:
    """CONTRIBUTING.md documente le workflow de modification de la landing."""

    def setup_method(self):
        self.content = CONTRIBUTING.read_text(encoding="utf-8")

    @pytest.mark.parametrize("marker", [
        "landing",
        "build:css",
        "forge sync:landing",
        "static/",
    ])
    def test_workflow_documented(self, marker):
        assert marker in self.content, (
            f"CONTRIBUTING.md devrait mentionner '{marker}' dans la "
            f"section de modification de la landing"
        )
