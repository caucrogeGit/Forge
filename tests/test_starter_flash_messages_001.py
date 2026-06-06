"""Garde-fou STARTER-FLASH-MESSAGES-001 (test proportionné).

Contrat du palier 8 (dernier) du niveau intermédiaire — Messages flash :

- starter.json : `flash-messages`, slot 19, requires_db **false** ;
- snippet : GET page, POST action ;
- contrôleur : `set_flash` + `redirect` (POST-Redirect-GET), `get_flash`
  one-shot, cookie session durci, CSRF ;
- vue : message conditionnel + formulaire POST avec CSRF ; doc + catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "flash-messages"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "flash_messages_controller.py"
VIEW = FILES / "mvc" / "views" / "flash_messages" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-forge" / "intermediaire" / "flash-messages.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 19"]


def test_resolves():
    m = resolve("flash-messages")
    assert m["id"] == "flash-messages" and m["number"] == 19
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("flash-messages", "flash_messages", "flash", "19"):
        assert resolve(a)["id"] == "flash-messages"


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/flash-messages") in routes
    assert ("POST", "/flash-messages/action") in routes


def test_controller_flash_prg():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from core.security.session import get_flash, get_session, get_session_id" in text
    assert "set_flash(" in text
    assert "redirect(" in text
    assert "get_flash(session_id)" in text
    assert "Set-Cookie" in text and "HttpOnly" in text
    assert "csrf_token" in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "FlashMessagesController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "action"} <= methods


def test_view_flash_and_csrf():
    html = VIEW.read_text(encoding="utf-8")
    assert "{% if flash %}" in html
    assert "{{ flash.message }}" in html
    assert 'method="post"' in html and 'name="csrf_token"' in html


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Messages flash"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "flash-messages" in idx and "Messages flash" in idx
