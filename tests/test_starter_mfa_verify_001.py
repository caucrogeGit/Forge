"""Garde-fou STARTER-MFA-VERIFY-001 — palier 3 débutant welcome-mfa (slot 69)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "mfa-verify"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "mfa_verify_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "mfa_verify" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-mfa" / "debutant" / "mfa-verify.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 69"]


def test_resolves():
    m = resolve("mfa-verify")
    assert m["id"] == "mfa-verify" and m["number"] == 69
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("mfa-verify", "mfa_verify", "69"):
        assert resolve(a)["id"] == "mfa-verify"


def test_doc_url():
    assert "welcome-mfa/debutant/mfa-verify" in resolve("mfa-verify")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/mfa-verify") in routes
    assert ("POST", "/mfa-verify") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_mfa import verify_totp_code" in text
    assert "verify_totp_code(" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "MfaVerifyController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert {"index", "check"} <= {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Vérifier un code TOTP"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "mfa-verify" in idx and "Vérifier un code TOTP" in idx
