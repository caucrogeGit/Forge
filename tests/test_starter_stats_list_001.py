"""Garde-fou STARTER-STATS-LIST-001 — palier 2 avancé welcome-stats (slot 107)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "stats-list"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "stats_list_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-stats" / "avance" / "stats-list.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 107"]


def test_resolves():
    m = resolve("stats-list")
    assert m["id"] == "stats-list" and m["number"] == 107
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("stats-list", "stats_list", "107"):
        assert resolve(a)["id"] == "stats-list"


def test_doc_url():
    assert "welcome-stats/avance/stats-list" in resolve("stats-list")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/stats-list") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_stats import list_stats_events" in text
    assert "fetch_all" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "StatsListController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Lister les événements"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "stats-list" in idx and "Lister les événements" in idx
