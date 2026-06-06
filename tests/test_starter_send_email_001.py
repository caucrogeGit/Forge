"""Garde-fou STARTER-SEND-EMAIL-001 (test proportionné).

Contrat du palier 3 du niveau avancé — Envoyer un email :

- starter.json : `send-email`, slot 22, requires_db **false** ;
- snippet : GET formulaire, POST envoi ;
- contrôleur : `MailMessage`, `Mailer(ConsoleTransport())`, gestion de
  `MailError`, CSRF ; pas de base de données ;
- vue : formulaire POST + jeton CSRF + champs destinataire / message ;
- documentation sous `avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "send-email"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "send_email_controller.py"
VIEW = FILES / "mvc" / "views" / "send_email" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-forge" / "avance" / "send-email.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 22"]


def test_resolves():
    m = resolve("send-email")
    assert m["id"] == "send-email" and m["number"] == 22
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("send-email", "send_email", "email", "mail", "22"):
        assert resolve(a)["id"] == "send-email"


def test_doc_url_pointe_avance():
    assert "welcome-forge/avance/send-email" in resolve("send-email")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/send-email") in routes
    assert ("POST", "/send-email") in routes


def test_controller_mail_api_and_no_db():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_mail import ConsoleTransport, MailError, Mailer, MailMessage" in text
    assert "MailMessage(" in text
    assert "Mailer(ConsoleTransport())" in text
    assert "csrf_token" in text
    assert "MailError" in text
    assert "core.database" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "SendEmailController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "send"} <= methods


def test_view_post_form_with_csrf_and_fields():
    html = VIEW.read_text(encoding="utf-8")
    assert 'method="post"' in html
    assert 'name="csrf_token"' in html
    assert 'name="recipient"' in html and 'name="message"' in html


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Envoyer un email"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "send-email" in idx and "Envoyer un email" in idx
