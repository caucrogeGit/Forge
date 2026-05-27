"""Garde-fous DOCS-INSTALL-TAGS-V3-001.

Vérifie que les guides d'installation actifs n'utilisent pas de tags Forge
obsolètes (v0.x, v1.x, v2.x). Sans ce garde-fou, les pages d'installation
ont historiquement traîné sur d'anciens tags après les bumps majeurs.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

INSTALL_GUIDES = [
    PROJECT_ROOT / "docs" / "guide.md",
    PROJECT_ROOT / "docs" / "install" / "index.md",
    PROJECT_ROOT / "docs" / "install" / "github.md",
    PROJECT_ROOT / "docs" / "install" / "pipx.md",
    PROJECT_ROOT / "docs" / "install" / "vm-debian.md",
    PROJECT_ROOT / "docs" / "install" / "mariadb.md",
    PROJECT_ROOT / "docs" / "install" / "core-dev.md",
    PROJECT_ROOT / "docs" / "profiles.md",
]

_STALE_TAG = re.compile(r"v[12]\.\d+(\.\d+)?")
_CLONE_STALE = re.compile(r"git clone[^\n]*--branch\s+v[12]\.\d+")
_REF_STALE = re.compile(r"--ref\s+v[12]\.\d+")


def _current_major() -> str:
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"].split(".")[0]


class TestInstallGuidesNoStaleTags:
    """Aucune commande d'installation active ne pointe sur un tag d'une majeure antérieure."""

    def test_guides_exist(self):
        for guide in INSTALL_GUIDES:
            assert guide.exists(), f"{guide.relative_to(PROJECT_ROOT)} doit exister"

    def test_no_stale_v1_or_v2_in_install_guides(self):
        for guide in INSTALL_GUIDES:
            text = guide.read_text(encoding="utf-8")
            stale_lines = [
                (i + 1, line)
                for i, line in enumerate(text.splitlines())
                if _STALE_TAG.search(line)
            ]
            assert not stale_lines, (
                f"{guide.relative_to(PROJECT_ROOT)} contient des tags v1.x/v2.x obsolètes :\n"
                + "\n".join(f"  L.{no}: {ln!r}" for no, ln in stale_lines)
            )

    def test_no_stale_tags_in_clone_or_ref_commands(self):
        for guide in INSTALL_GUIDES:
            text = guide.read_text(encoding="utf-8")
            for line_no, line in enumerate(text.splitlines(), start=1):
                if _CLONE_STALE.search(line) or _REF_STALE.search(line):
                    raise AssertionError(
                        f"{guide.relative_to(PROJECT_ROOT)}:{line_no} — commande "
                        f"d'installation sur une majeure obsolète : {line!r}"
                    )


class TestInstallGuidesMatchCurrentMajor:
    """Au moins un guide référence la majeure courante de pyproject.toml."""

    def test_at_least_one_guide_references_current_major(self):
        current = _current_major()
        pattern = re.compile(rf"v{re.escape(current)}\.\d+")
        for guide in INSTALL_GUIDES:
            if not guide.exists():
                continue
            text = guide.read_text(encoding="utf-8")
            # Accepter aussi le placeholder mkdocs (substitué au build en v{current}.x.y)
            if pattern.search(text) or "{{forge_tag}}" in text:
                return
        raise AssertionError(
            f"Aucun guide d'installation ne mentionne la majeure courante v{current}.x. "
            f"Vérifier docs/guide.md, docs/install/github.md ou docs/profiles.md."
        )
