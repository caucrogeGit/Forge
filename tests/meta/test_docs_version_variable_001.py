"""Garde-fou DOCS-VERSION-VARIABLE-001.

Vérifie que :
1. Le hook mkdocs_version_hook.py existe et est référencé dans mkdocs.yml
2. Aucune mention de la version courante en dur dans la doc utilisateur active
   (hors history/, audits/, CHANGELOG, roadmap, adr)
3. Le build mkdocs résout correctement les variables
"""
from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
HOOK = PROJECT_ROOT / "tools" / "mkdocs_version_hook.py"

EXCLUDED_DIRS = {"history", "audits", "roadmap", "adr"}
EXCLUDED_FILES = {"CHANGELOG.md"}


def _current_version() -> str:
    data = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    return data["project"]["version"]


def _active_md_files() -> list[Path]:
    files = []
    for md in DOCS_DIR.rglob("*.md"):
        if any(part in EXCLUDED_DIRS for part in md.parts):
            continue
        if md.name in EXCLUDED_FILES:
            continue
        files.append(md)
    return sorted(files)


class TestHookExists:
    def test_hook_file_exists(self):
        assert HOOK.exists(), f"Hook manquant : {HOOK}"

    def test_hook_referenced_in_mkdocs_yml(self):
        mkdocs = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        assert "tools/mkdocs_version_hook.py" in mkdocs


class TestNoHardcodedCurrentVersion:
    """Aucune mention en dur de la version courante dans la doc active."""

    def test_no_hardcoded_version(self):
        version = _current_version()
        tag = f"v{version}"
        offenders: list[str] = []
        patterns = [
            re.escape(version),
            re.escape(tag),
            f"Forge {re.escape(version)}",
            f"forge_mvc-{re.escape(version)}",
        ]
        big_re = re.compile("|".join(patterns))

        for md in _active_md_files():
            text = md.read_text(encoding="utf-8")
            for line_no, line in enumerate(text.split("\n"), start=1):
                if big_re.search(line):
                    offenders.append(f"{md.relative_to(PROJECT_ROOT)}:{line_no} → {line.strip()}")

        if offenders:
            raise AssertionError(
                f"Version courante ({version}) en dur dans la doc active :\n"
                + "\n".join(f"  - {o}" for o in offenders)
                + "\n\nUtiliser {{forge_version}} ou {{forge_tag}} à la place."
            )


class TestMkdocsBuildResolvesVariables:
    """Le build mkdocs substitue bien les variables."""

    def test_build_resolves_forge_version(self, tmp_path):
        result = subprocess.run(
            ["mkdocs", "build", "--strict", "-d", str(tmp_path / "site")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"mkdocs build a échoué :\n{result.stderr[-500:]}"
        )

        version = _current_version()
        site_dir = tmp_path / "site"
        found = False
        for html in site_dir.rglob("*.html"):
            if version in html.read_text(encoding="utf-8", errors="ignore"):
                found = True
                break
        assert found, f"Version {version} introuvable dans le site rendu"

    def test_build_does_not_leave_placeholders(self, tmp_path):
        """Aucun {{forge_version}} non substitué dans le site rendu."""
        result = subprocess.run(
            ["mkdocs", "build", "--strict", "-d", str(tmp_path / "site")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0

        site_dir = tmp_path / "site"
        offenders = []
        for html in site_dir.rglob("*.html"):
            text = html.read_text(encoding="utf-8", errors="ignore")
            for placeholder in ("{{forge_version}}", "{{forge_tag}}", "{{python_min}}"):
                if placeholder in text:
                    offenders.append(f"{html.name} contient {placeholder}")
        if offenders:
            raise AssertionError(
                "Placeholders non substitués :\n" + "\n".join(offenders)
            )
