"""Garde-fou STARTER-RBAC-USER-ROLE-001 — palier 1 avancé welcome-rbac (slot 82)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "rbac-user-role"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "rbac_user_role_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "rbac_user_role" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-rbac" / "avance" / "rbac-user-role.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 82"]


def test_resolves():
    m = resolve("rbac-user-role")
    assert m["id"] == "rbac-user-role" and m["number"] == 82
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("rbac-user-role", "rbac_user_role", "82"):
        assert resolve(a)["id"] == "rbac-user-role"


def test_doc_url():
    assert "welcome-rbac/avance/rbac-user-role" in resolve("rbac-user-role")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/rbac-user-role") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "create_auth_user_role" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "RbacUserRoleController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Associer un rôle à un utilisateur"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "rbac-user-role" in idx and "Associer un rôle à un utilisateur" in idx
