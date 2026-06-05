"""Garde-fou STARTER-MFA-REPLAY-001 — palier 2 avancé welcome-mfa (slot 80)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "mfa-replay"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "mfa_replay_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "mfa_replay" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-mfa" / "avance" / "mfa-replay.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 80"]


def test_resolves():
    m = resolve("mfa-replay")
    assert m["id"] == "mfa-replay" and m["number"] == 80
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("mfa-replay", "mfa_replay", "80"):
        assert resolve(a)["id"] == "mfa-replay"


def test_doc_url():
    assert "welcome-mfa/avance/mfa-replay" in resolve("mfa-replay")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/mfa-replay") in routes
    assert ("POST", "/mfa-replay") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "is_replay" in text and "record_used" in text and "step_for_time" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "MfaReplayController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert {"index", "use"} <= {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Anti-rejeu TOTP"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "mfa-replay" in idx and "Anti-rejeu TOTP" in idx
