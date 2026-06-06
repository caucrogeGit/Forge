"""Garde-fou STARTER-WORKFLOW-FIND-001 — palier 3 débutant welcome-workflow (slot 93)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "workflow-find"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "workflow_find_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "workflow_find" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-workflow" / "debutant" / "workflow-find.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 93"]


def test_resolves():
    m = resolve("workflow-find")
    assert m["id"] == "workflow-find" and m["number"] == 93
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("workflow-find", "workflow_find", "93"):
        assert resolve(a)["id"] == "workflow-find"


def test_doc_url():
    assert "welcome-workflow/debutant/workflow-find" in resolve("workflow-find")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/workflow-find") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "find_status" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "WorkflowFindController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Retrouver un statut"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "workflow-find" in idx and "Retrouver un statut" in idx
