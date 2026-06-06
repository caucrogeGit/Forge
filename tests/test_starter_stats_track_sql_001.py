"""Garde-fou STARTER-STATS-TRACK-SQL-001 — palier 1 intermédiaire welcome-stats (slot 103)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "stats-track-sql"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "stats_track_sql_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "stats_track_sql" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-stats" / "intermediaire" / "stats-track-sql.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 103"]


def test_resolves():
    m = resolve("stats-track-sql")
    assert m["id"] == "stats-track-sql" and m["number"] == 103
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("stats-track-sql", "stats_track_sql", "103"):
        assert resolve(a)["id"] == "stats-track-sql"


def test_doc_url():
    assert "welcome-stats/intermediaire/stats-track-sql" in resolve("stats-track-sql")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/stats-track-sql") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "get_track_event_sql" in text and "prepare_track_event_values" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "StatsTrackSqlController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Le SQL d'insertion"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "stats-track-sql" in idx and "Le SQL d'insertion" in idx
