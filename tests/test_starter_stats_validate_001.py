"""Garde-fou STARTER-STATS-VALIDATE-001 — palier 3 intermédiaire welcome-stats (slot 99)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "stats-validate"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "stats_validate_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "stats_validate" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-stats" / "intermediaire" / "stats-validate.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 99"]


def test_resolves():
    m = resolve("stats-validate")
    assert m["id"] == "stats-validate" and m["number"] == 99
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("stats-validate", "stats_validate", "99"):
        assert resolve(a)["id"] == "stats-validate"


def test_doc_url():
    assert "welcome-stats/intermediaire/stats-validate" in resolve("stats-validate")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/stats-validate") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "validate_event" in text and "StatsEventError" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "StatsValidateController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Valider un événement"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "stats-validate" in idx and "Valider un événement" in idx
