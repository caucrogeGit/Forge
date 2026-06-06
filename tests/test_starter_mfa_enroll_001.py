"""Garde-fou STARTER-MFA-ENROLL-001 — palier 1 intermédiaire welcome-mfa (slot 70)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "mfa-enroll"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "mfa_enroll_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "mfa_enroll" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-mfa" / "intermediaire" / "mfa-enroll.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 70"]


def test_resolves():
    m = resolve("mfa-enroll")
    assert m["id"] == "mfa-enroll" and m["number"] == 70
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("mfa-enroll", "mfa_enroll", "70"):
        assert resolve(a)["id"] == "mfa-enroll"


def test_doc_url():
    assert "welcome-mfa/intermediaire/mfa-enroll" in resolve("mfa-enroll")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/mfa-enroll") in routes
    assert ("POST", "/mfa-enroll") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "create_totp_factor" in text and "confirm_totp_factor" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "MfaEnrollController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert {"index", "confirm"} <= {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Enrôler un facteur TOTP"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "mfa-enroll" in idx and "Enrôler un facteur TOTP" in idx
