"""Garde-fou documentaire — IOT-END-TO-END-LOCAL-SMOKE-001.

Vérifie que le smoke test local Forge IoT est présent et complet : un
script semi-automatique `scripts/iot-local-smoke.sh` et une page
`docs/iot/local-smoke-test.md`. Aucun service externe n'est lancé ici :
ce ticket est docs + script opt-in, pas un test d'intégration CI.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "iot-local-smoke.sh"
PAGE = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "docs" / "local-smoke-test.md"
MKDOCS = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "mkdocs.yml"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _script_text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def _page_text() -> str:
    return PAGE.read_text(encoding="utf-8")


# ── Présence ─────────────────────────────────────────────────────────────────


def test_script_exists():
    assert SCRIPT.is_file(), "scripts/iot-local-smoke.sh doit exister"


def test_page_exists():
    assert PAGE.is_file(), "docs/iot/local-smoke-test.md doit exister"


def test_page_referenced_in_mkdocs():
    assert "local-smoke-test.md" in MKDOCS.read_text(encoding="utf-8"), (
        "la page doit être référencée dans la nav mkdocs.yml"
    )


def test_roadmap_mentions_ticket():
    assert "IOT-END-TO-END-LOCAL-SMOKE-001" in ROADMAP.read_text(encoding="utf-8")


# ── Contenu du script ────────────────────────────────────────────────────────


class TestScriptContent:
    def test_strict_mode(self):
        assert "set -euo pipefail" in _script_text()

    @pytest.mark.parametrize("command", [
        "forge iot:doctor --mqtt",
        "forge iot:init",
        "forge migration:apply",
        "forge iot:doctor --db",
        "forge iot:simulate",
    ])
    def test_script_invokes_or_mentions(self, command):
        assert command in _script_text(), (
            f"le script doit appeler ou mentionner {command!r}"
        )


# ── Contenu de la doc ────────────────────────────────────────────────────────


class TestDocContent:
    @pytest.mark.parametrize("needle", [
        "forge iot:doctor --mqtt",
        "forge iot:init",
        "forge migration:apply",
        "forge iot:doctor --db",
        "forge iot:listen",
        "forge iot:simulate",
        "/api/iot/events",
        "mosquitto",
    ])
    def test_doc_mentions(self, needle):
        assert needle in _page_text(), f"la doc doit mentionner {needle!r}"

    def test_doc_states_not_ci(self):
        text = _page_text().lower()
        assert "ci" in text and (
            "pas un test de la ci" in text
            or "pas un test de ci" in text
            or "pas destiné à la ci" in text
            or "pas de la ci standard" in text
            or "pas un test de la ci standard" in text
        ), "la doc doit préciser que ce smoke test n'est pas pour la CI standard"
