"""Garde-fou STARTER-WORKFLOW-AVAILABLE-001 — palier 3 intermédiaire welcome-workflow (slot 90)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "workflow-available"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "workflow_available_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "workflow_available" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-workflow" / "intermediaire" / "workflow-available.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 90"]


def test_resolves():
    m = resolve("workflow-available")
    assert m["id"] == "workflow-available" and m["number"] == 90
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("workflow-available", "workflow_available", "90"):
        assert resolve(a)["id"] == "workflow-available"


def test_doc_url():
    assert "welcome-workflow/intermediaire/workflow-available" in resolve("workflow-available")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/workflow-available") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "get_available_transitions" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "WorkflowAvailableController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Transitions disponibles"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "workflow-available" in idx and "Transitions disponibles" in idx
