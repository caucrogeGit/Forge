"""Garde-fou STARTER-RBAC-RESOLVE-001 — palier 2 avancé welcome-rbac (slot 83)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "rbac-resolve"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "rbac_resolve_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-rbac" / "avance" / "rbac-resolve.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 83"]


def test_resolves():
    m = resolve("rbac-resolve")
    assert m["id"] == "rbac-resolve" and m["number"] == 83
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("rbac-resolve", "rbac_resolve", "83"):
        assert resolve(a)["id"] == "rbac-resolve"


def test_doc_url():
    assert "welcome-rbac/avance/rbac-resolve" in resolve("rbac-resolve")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/rbac-resolve") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "get_user_permissions" in text and "user_has_permission" in text
    assert "fetch_all" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "RbacResolveController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Résoudre les permissions d'un utilisateur"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "rbac-resolve" in idx and "Résoudre les permissions" in idx
