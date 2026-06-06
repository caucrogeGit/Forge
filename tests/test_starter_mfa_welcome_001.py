"""Garde-fou STARTER-MFA-WELCOME-001 — palier 1 débutant welcome-mfa (slot 67)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "mfa-welcome"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "mfa_welcome_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-mfa" / "debutant" / "mfa-welcome.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 67"]


def test_resolves():
    m = resolve("mfa-welcome")
    assert m["id"] == "mfa-welcome" and m["number"] == 67
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("mfa-welcome", "mfa_welcome", "67"):
        assert resolve(a)["id"] == "mfa-welcome"


def test_doc_url():
    assert "welcome-mfa/debutant/mfa-welcome" in resolve("mfa-welcome")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/mfa-welcome") in routes
    assert ("GET", "/mfa-welcome/inspect") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "validate_mfa_secret_key_config" in text
    assert "MFA_FACTOR_TOTP" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "MfaWelcomeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "inspect"} <= methods


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Bonjour Forge MFA"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "mfa-welcome" in idx and "Bonjour Forge MFA" in idx
