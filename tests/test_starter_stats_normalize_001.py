"""Garde-fou STARTER-STATS-NORMALIZE-001 — palier 3 avancé welcome-stats (slot 102)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "stats-normalize"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "stats_normalize_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "stats_normalize" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-stats" / "avance" / "stats-normalize.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 102"]


def test_resolves():
    m = resolve("stats-normalize")
    assert m["id"] == "stats-normalize" and m["number"] == 102
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("stats-normalize", "stats_normalize", "102"):
        assert resolve(a)["id"] == "stats-normalize"


def test_doc_url():
    assert "welcome-stats/avance/stats-normalize" in resolve("stats-normalize")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/stats-normalize") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "normalize_stats_event_row" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "StatsNormalizeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Normaliser une ligne"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "stats-normalize" in idx and "Normaliser une ligne" in idx
