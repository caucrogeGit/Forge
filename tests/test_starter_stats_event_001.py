"""Garde-fou STARTER-STATS-EVENT-001 — palier 2 débutant welcome-stats (slot 95)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "stats-event"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "stats_event_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "stats_event" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-stats" / "debutant" / "stats-event.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 95"]


def test_resolves():
    m = resolve("stats-event")
    assert m["id"] == "stats-event" and m["number"] == 95
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("stats-event", "stats_event", "95"):
        assert resolve(a)["id"] == "stats-event"


def test_doc_url():
    assert "welcome-stats/debutant/stats-event" in resolve("stats-event")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/stats-event") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "normalize_event_name" in text and "validate_event_name" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "StatsEventController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Nom d'événement"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "stats-event" in idx and "Nom d'événement" in idx
