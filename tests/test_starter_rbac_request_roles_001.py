"""Garde-fou STARTER-RBAC-REQUEST-ROLES-001 — palier 3 avancé welcome-rbac (slot 84)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "rbac-request-roles"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "rbac_request_roles_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-rbac" / "avance" / "rbac-request-roles.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 84"]


def test_resolves():
    m = resolve("rbac-request-roles")
    assert m["id"] == "rbac-request-roles" and m["number"] == 84
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("rbac-request-roles", "rbac_request_roles", "84"):
        assert resolve(a)["id"] == "rbac-request-roles"


def test_doc_url():
    assert "welcome-rbac/avance/rbac-request-roles" in resolve("rbac-request-roles")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/rbac-request-roles") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "get_request_roles" in text and "get_request_permissions" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "RbacRequestRolesController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Rôles de la requête"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "rbac-request-roles" in idx and "Rôles de la requête" in idx
