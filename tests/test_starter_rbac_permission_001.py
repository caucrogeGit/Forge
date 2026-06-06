"""Garde-fou STARTER-RBAC-PERMISSION-001 — palier 2 débutant welcome-rbac (slot 77)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "rbac-permission"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "rbac_permission_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "rbac_permission" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-rbac" / "debutant" / "rbac-permission.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 77"]


def test_resolves():
    m = resolve("rbac-permission")
    assert m["id"] == "rbac-permission" and m["number"] == 77
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("rbac-permission", "rbac_permission", "77"):
        assert resolve(a)["id"] == "rbac-permission"


def test_doc_url():
    assert "welcome-rbac/debutant/rbac-permission" in resolve("rbac-permission")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/rbac-permission") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "normalize_permission_code" in text and "validate_permission" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "RbacPermissionController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Code de permission"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "rbac-permission" in idx and "Code de permission" in idx
