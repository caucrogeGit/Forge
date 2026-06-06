"""Garde-fou STARTER-MAIL-MESSAGE-001 — Composer un message (slot 103)."""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "mail-message"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "mail_message_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "mail_message" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-mail" / "debutant" / "mail-message.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 103"]


def test_resolves():
    m = resolve("mail-message")
    assert m["id"] == "mail-message" and m["number"] == 103
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("mail-message", "mail_message", "103"):
        assert resolve(a)["id"] == "mail-message"


def test_doc_url():
    assert "welcome-mail/debutant/mail-message" in resolve("mail-message")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/mail-message") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "MailMessageController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    assert "index" in {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Composer un message"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "mail-message" in idx and "Composer un message" in idx
