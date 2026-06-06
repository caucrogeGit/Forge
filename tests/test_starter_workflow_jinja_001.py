"""Garde-fou STARTER-WORKFLOW-JINJA-001 — palier 3 avancé welcome-workflow (slot 93)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "workflow-jinja"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "workflow_jinja_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "workflow_jinja" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-workflow" / "avance" / "workflow-jinja.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 93"]


def test_resolves():
    m = resolve("workflow-jinja")
    assert m["id"] == "workflow-jinja" and m["number"] == 93
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("workflow-jinja", "workflow_jinja", "93"):
        assert resolve(a)["id"] == "workflow-jinja"


def test_doc_url():
    assert "welcome-workflow/avance/workflow-jinja" in resolve("workflow-jinja")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/workflow-jinja") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "make_workflow_jinja_helpers" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "WorkflowJinjaController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Helpers Workflow dans Jinja"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "workflow-jinja" in idx and "Helpers Workflow dans Jinja" in idx
