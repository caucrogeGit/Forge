"""Garde-fou STARTER-STATS-ADMIN-SQL-001 — palier 1 avancé welcome-stats (slot 100)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "stats-admin-sql"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "stats_admin_sql_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "stats_admin_sql" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-stats" / "avance" / "stats-admin-sql.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 100"]


def test_resolves():
    m = resolve("stats-admin-sql")
    assert m["id"] == "stats-admin-sql" and m["number"] == 100
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("stats-admin-sql", "stats_admin_sql", "100"):
        assert resolve(a)["id"] == "stats-admin-sql"


def test_doc_url():
    assert "welcome-stats/avance/stats-admin-sql" in resolve("stats-admin-sql")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/stats-admin-sql") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "get_stats_events_admin_sql" in text and "prepare_stats_events_admin_params" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "StatsAdminSqlController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Le SQL de consultation"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "stats-admin-sql" in idx and "Le SQL de consultation" in idx
