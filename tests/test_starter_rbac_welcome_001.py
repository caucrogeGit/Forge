"""Garde-fou STARTER-RBAC-WELCOME-001 — palier 1 débutant welcome-rbac (slot 76)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "rbac-welcome"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "rbac_welcome_controller.py"
CONTRACT = STARTER_DIR / "files" / "mvc" / "security" / "rbac.json"
DOC = ROOT / "docs" / "starters" / "welcome-rbac" / "debutant" / "rbac-welcome.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 76"]


def test_resolves():
    m = resolve("rbac-welcome")
    assert m["id"] == "rbac-welcome" and m["number"] == 76
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("rbac-welcome", "rbac_welcome", "76"):
        assert resolve(a)["id"] == "rbac-welcome"


def test_doc_url():
    assert "welcome-rbac/debutant/rbac-welcome" in resolve("rbac-welcome")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/rbac-welcome") in routes
    assert ("GET", "/rbac-welcome/inspect") in routes


def test_controller_and_contract():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "load_rbac_contract" in text and "get_contract_permissions" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "RbacWelcomeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert {"index", "inspect"} <= {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert CONTRACT.is_file(), "Le starter doit livrer mvc/security/rbac.json."


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Bonjour Forge RBAC"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "rbac-welcome" in idx and "Bonjour Forge RBAC" in idx
