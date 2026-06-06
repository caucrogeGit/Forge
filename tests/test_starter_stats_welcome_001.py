"""Garde-fou STARTER-STATS-WELCOME-001 — palier 1 débutant welcome-stats (slot 100)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "stats-welcome"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "stats_welcome_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-stats" / "debutant" / "stats-welcome.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 100"]


def test_resolves():
    m = resolve("stats-welcome")
    assert m["id"] == "stats-welcome" and m["number"] == 100
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("stats-welcome", "stats_welcome", "100"):
        assert resolve(a)["id"] == "stats-welcome"


def test_doc_url():
    assert "welcome-stats/debutant/stats-welcome" in resolve("stats-welcome")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/stats-welcome") in routes
    assert ("GET", "/stats-welcome/inspect") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "make_event" in text and "STATS_EVENTS_TABLE" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "StatsWelcomeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert {"index", "inspect"} <= {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Bonjour Forge Stats"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "stats-welcome" in idx and "Bonjour Forge Stats" in idx
