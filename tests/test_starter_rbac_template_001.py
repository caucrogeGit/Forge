"""Garde-fou STARTER-RBAC-TEMPLATE-001 — palier 3 intermédiaire welcome-rbac (slot 81)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "rbac-template"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "rbac_template_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "rbac_template" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-rbac" / "intermediaire" / "rbac-template.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 81"]


def test_resolves():
    m = resolve("rbac-template")
    assert m["id"] == "rbac-template" and m["number"] == 81
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("rbac-template", "rbac_template", "81"):
        assert resolve(a)["id"] == "rbac-template"


def test_doc_url():
    assert "welcome-rbac/intermediaire/rbac-template" in resolve("rbac-template")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/rbac-template") in routes


def test_controller_and_view():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "make_can" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "RbacTemplateController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "can(" in VIEW.read_text(encoding="utf-8")


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Permission dans un template"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "rbac-template" in idx and "Permission dans un template" in idx
