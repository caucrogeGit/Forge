"""Garde-fou STARTER-MFA-CHALLENGE-001 — palier 2 intermédiaire welcome-mfa (slot 71)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "mfa-challenge"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "mfa_challenge_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "mfa_challenge" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-mfa" / "intermediaire" / "mfa-challenge.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 71"]


def test_resolves():
    m = resolve("mfa-challenge")
    assert m["id"] == "mfa-challenge" and m["number"] == 71
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("mfa-challenge", "mfa_challenge", "71"):
        assert resolve(a)["id"] == "mfa-challenge"


def test_doc_url():
    assert "welcome-mfa/intermediaire/mfa-challenge" in resolve("mfa-challenge")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/mfa-challenge") in routes
    assert ("POST", "/mfa-challenge") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "start_mfa_challenge" in text and "verify_mfa_challenge" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "MfaChallengeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert {"index", "verify"} <= {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Challenge de connexion"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "mfa-challenge" in idx and "Challenge de connexion" in idx
