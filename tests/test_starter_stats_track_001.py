"""Garde-fou STARTER-STATS-TRACK-001 — palier 2 intermédiaire welcome-stats (slot 98)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "stats-track"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "stats_track_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "stats_track" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-stats" / "intermediaire" / "stats-track.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 98"]


def test_resolves():
    m = resolve("stats-track")
    assert m["id"] == "stats-track" and m["number"] == 98
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("stats-track", "stats_track", "98"):
        assert resolve(a)["id"] == "stats-track"


def test_doc_url():
    assert "welcome-stats/intermediaire/stats-track" in resolve("stats-track")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/stats-track") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_stats import make_event, track_event" in text
    assert "track_event(" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "StatsTrackController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Enregistrer un événement"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "stats-track" in idx and "Enregistrer un événement" in idx
