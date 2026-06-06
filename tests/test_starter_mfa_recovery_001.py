"""Garde-fou STARTER-MFA-RECOVERY-001 — palier 3 intermédiaire welcome-mfa (slot 72)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "mfa-recovery"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "mfa_recovery_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "mfa_recovery" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-mfa" / "intermediaire" / "mfa-recovery.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 72"]


def test_resolves():
    m = resolve("mfa-recovery")
    assert m["id"] == "mfa-recovery" and m["number"] == 72
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("mfa-recovery", "mfa_recovery", "72"):
        assert resolve(a)["id"] == "mfa-recovery"


def test_doc_url():
    assert "welcome-mfa/intermediaire/mfa-recovery" in resolve("mfa-recovery")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/mfa-recovery") in routes
    assert ("POST", "/mfa-recovery") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "create_recovery_codes" in text and "consume_recovery_code" in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "MfaRecoveryController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert {"index", "consume"} <= {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Codes de récupération"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "mfa-recovery" in idx and "Codes de récupération" in idx
