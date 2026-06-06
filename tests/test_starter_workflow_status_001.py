"""Garde-fou STARTER-WORKFLOW-STATUS-001 — palier 2 débutant welcome-workflow (slot 92)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "workflow-status"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "workflow_status_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "workflow_status" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-workflow" / "debutant" / "workflow-status.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 92"]


def test_resolves():
    m = resolve("workflow-status")
    assert m["id"] == "workflow-status" and m["number"] == 92
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("workflow-status", "workflow_status", "92"):
        assert resolve(a)["id"] == "workflow-status"


def test_doc_url():
    assert "welcome-workflow/debutant/workflow-status" in resolve("workflow-status")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/workflow-status") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "normalize_status_name" in text and "validate_status_name" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "WorkflowStatusController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Nom de statut"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "workflow-status" in idx and "Nom de statut" in idx
