"""Garde-fou DOCS-RELEASE-LOCAL-STARTERS-COUNT-001.

Vérifie que docs/release/release-local.md référence bien tous les starters
actuellement disponibles (via le nombre de dossiers dans starters/data/).
Le doc utilise des numéros (Starter 1, Starter 2...) et des noms humains,
pas les slugs techniques — on vérifie le count et les sections numérotées.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
RELEASE_LOCAL = PROJECT_ROOT / "docs" / "release" / "release-local.md"
STARTERS_DIR = PROJECT_ROOT / "forge_cli" / "starters" / "data"


def _actual_starter_count() -> int:
    return sum(1 for d in STARTERS_DIR.iterdir() if d.is_dir())


class TestReleaseLocalExists:

    def test_file_exists(self):
        assert RELEASE_LOCAL.exists(), f"{RELEASE_LOCAL} doit exister."


class TestReleaseLocalReferencesAllStarters:

    def test_all_starter_sections_present(self):
        text = RELEASE_LOCAL.read_text(encoding="utf-8")
        count = _actual_starter_count()
        missing = []
        for n in range(1, count + 1):
            if f"### Starter {n}" not in text and f"starter:build {n}" not in text:
                missing.append(n)
        assert not missing, (
            f"docs/release/release-local.md manque les starters numérotés : {missing}. "
            f"Ajouter une section ### Starter N pour chacun."
        )

    def test_starter_count_consistent(self):
        text = RELEASE_LOCAL.read_text(encoding="utf-8")
        actual = _actual_starter_count()
        for m in re.findall(r"(?:les |sur les )?(\d+)\s+starters?\b", text):
            n = int(m)
            if n < 100 and n != actual:
                pytest.fail(
                    f"docs/release/release-local.md mentionne `{n} starters` "
                    f"mais il en existe {actual}. Mettre à jour la référence."
                )

    def test_dry_run_commands_for_all_starters(self):
        text = RELEASE_LOCAL.read_text(encoding="utf-8")
        count = _actual_starter_count()
        missing = [n for n in range(1, count + 1) if f"starter:build {n} --force --dry-run" not in text]
        assert not missing, (
            f"docs/release/release-local.md manque --dry-run pour les starters : {missing}."
        )
