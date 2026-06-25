"""Garde-fous RELEASE-3.0.0-TAG-STABLE-001 : cohérence de la roadmap avec la série 3.0.x."""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _current_version() -> str:
    data = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    return data["project"]["version"]


def _semver_tag() -> str:
    version = _current_version()
    semver = re.sub(r"(\d+\.\d+\.\d+)a(\d+)$", r"\1-alpha.\2", version)
    semver = re.sub(r"(\d+\.\d+\.\d+)b(\d+)$", r"\1-beta.\2", semver)
    semver = re.sub(r"(\d+\.\d+\.\d+)rc(\d+)$", r"\1-rc.\2", semver)
    return f"v{semver}"


class TestRoadmapHeaderMatchesCurrentVersion:
    """L'en-tête État actuel de la roadmap désigne Forge 3.0.1."""

    def test_roadmap_exists(self):
        assert ROADMAP.exists(), "docs/roadmap/forge-roadmap.md introuvable"

    def test_etat_actuel_section_present(self):
        assert "## État actuel" in ROADMAP.read_text(encoding="utf-8")

    def test_etat_actuel_mentions_current_version(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert re.search(r"## État actuel, Forge \d", text), (
            "La section '## État actuel, Forge X.Y.Z' doit exister dans la roadmap."
        )

    def test_no_stale_etat_actuel_2x(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "État actuel, Forge 2." not in text, (
            "La section 'État actuel' pointe encore vers une version 2.x"
        )

    def test_no_rc1_in_etat_actuel(self):
        text = ROADMAP.read_text(encoding="utf-8")
        lines = [l for l in text.splitlines() if "## État actuel" in l]
        for line in lines:
            assert "rc1" not in line, (
                f"La section 'État actuel' mentionne encore rc1 : {line!r}"
            )


class TestRoadmapTagCoherence:
    """Le tag courant dans la roadmap désigne la version courante."""

    def test_tag_matches_current_version(self):
        tag = _semver_tag()
        text = ROADMAP.read_text(encoding="utf-8")
        assert f"`{tag}`" in text, (
            f"Le tag {tag} doit être mentionné dans la roadmap "
            f"(dérivé de pyproject.toml)"
        )

    def test_no_stale_tag_recommande_2x(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "Tag recommandé" not in text, (
            "'Tag recommandé' encore présent dans la roadmap — "
            "format attendu : 'Tag courant : `v<version>`'"
        )
