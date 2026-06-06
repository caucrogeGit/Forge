"""Garde-fou STARTER-WORKFLOW-COLOR-001 — palier 2 avancé welcome-workflow (slot 98)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "workflow-color"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "workflow_color_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "workflow_color" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-workflow" / "avance" / "workflow-color.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 98"]


def test_resolves():
    m = resolve("workflow-color")
    assert m["id"] == "workflow-color" and m["number"] == 98
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("workflow-color", "workflow_color", "98"):
        assert resolve(a)["id"] == "workflow-color"


def test_doc_url():
    assert "welcome-workflow/avance/workflow-color" in resolve("workflow-color")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/workflow-color") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "workflow_status_color" in text and "workflow_status_label" in text and "workflow_status_badge_class" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "WorkflowColorController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Couleur, libellé, classe"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "workflow-color" in idx and "Couleur, libellé, classe" in idx
