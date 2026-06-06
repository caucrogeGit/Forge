"""Garde-fou STARTER-WORKFLOW-TRANSITION-001 — palier 1 intermédiaire welcome-workflow (slot 94)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "workflow-transition"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "workflow_transition_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "workflow_transition" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-workflow" / "intermediaire" / "workflow-transition.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 94"]


def test_resolves():
    m = resolve("workflow-transition")
    assert m["id"] == "workflow-transition" and m["number"] == 94
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("workflow-transition", "workflow_transition", "94"):
        assert resolve(a)["id"] == "workflow-transition"


def test_doc_url():
    assert "welcome-workflow/intermediaire/workflow-transition" in resolve("workflow-transition")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/workflow-transition") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "make_transition" in text and "validate_transitions" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "WorkflowTransitionController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Déclarer les transitions"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "workflow-transition" in idx and "Déclarer les transitions" in idx
