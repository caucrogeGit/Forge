"""Garde-fou STARTER-SESSION-STATE-001 (test proportionné).

Contrat du palier 7 du niveau intermédiaire — Mémoriser un état en session :

- starter.json : `session-state`, slot 18, requires_db **false** ;
- snippet : GET `/session-state` ;
- contrôleur : lit/crée la session, `store.set(...)`, pose un cookie
  `session_id` durci (HttpOnly, SameSite=Strict, Secure) ;
- pas de base de données ; doc + catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "session-state"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "session_state_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-forge" / "intermediaire" / "session-state.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 18"]


def test_resolves():
    m = resolve("session-state")
    assert m["id"] == "session-state" and m["number"] == 18
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("session-state", "session_state", "session", "18"):
        assert resolve(a)["id"] == "session-state"


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = routes_from_snippet(snip)
    assert any(m == "GET" and p == "/session-state" for m, p, *_ in routes)


def test_controller_session_api_and_hardened_cookie():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from core.security.session import get_session, get_session_id" in text
    assert "from core.sessions.manager import get_session_store" in text
    assert "store.create()" in text
    assert "store.set(session_id" in text
    # cookie durci
    assert "HttpOnly" in text and "SameSite=Strict" in text and "Secure" in text
    assert "Set-Cookie" in text
    # pas de base de données dans ce palier
    assert "core.database" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "SessionStateController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Mémoriser un état en session"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "session-state" in idx and "Mémoriser un état en session" in idx
