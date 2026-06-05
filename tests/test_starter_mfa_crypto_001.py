"""Garde-fou STARTER-MFA-CRYPTO-001 — palier 3 avancé welcome-mfa (slot 81)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "mfa-crypto"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "mfa_crypto_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "mfa_crypto" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-mfa" / "avance" / "mfa-crypto.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 81"]


def test_resolves():
    m = resolve("mfa-crypto")
    assert m["id"] == "mfa-crypto" and m["number"] == 81
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("mfa-crypto", "mfa_crypto", "81"):
        assert resolve(a)["id"] == "mfa-crypto"


def test_doc_url():
    assert "welcome-mfa/avance/mfa-crypto" in resolve("mfa-crypto")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/mfa-crypto") in routes
    assert ("POST", "/mfa-crypto") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "encrypt_totp_secret" in text and "decrypt_totp_secret" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "MfaCryptoController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert {"index", "demo"} <= {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Secret chiffré au repos"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "mfa-crypto" in idx and "Secret chiffré au repos" in idx
