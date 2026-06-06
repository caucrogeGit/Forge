"""Garde-fou STARTER-STATS-SCHEMA-001 — palier 3 débutant welcome-stats (slot 96)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "stats-schema"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "stats_schema_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "stats_schema" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-stats" / "debutant" / "stats-schema.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 96"]


def test_resolves():
    m = resolve("stats-schema")
    assert m["id"] == "stats-schema" and m["number"] == 96
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("stats-schema", "stats_schema", "96"):
        assert resolve(a)["id"] == "stats-schema"


def test_doc_url():
    assert "welcome-stats/debutant/stats-schema" in resolve("stats-schema")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/stats-schema") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "get_stats_events_schema_sql" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "StatsSchemaController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Le schéma SQL"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "stats-schema" in idx and "Le schéma SQL" in idx
