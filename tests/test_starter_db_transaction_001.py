"""Garde-fou STARTER-DB-TRANSACTION-001 (test proportionné).

Contrat du dernier palier du niveau avancé — Écritures transactionnelles :

- starter.json : `db-transaction`, slot 30, requires_db **true** ;
- snippet : GET formulaire, POST enregistrement ;
- contrôleur : `with transaction() as tx:`, deux `insert(..., tx=tx)`, rollback
  via exception, CSRF, redirection (PRG) ;
- vue : formulaire POST + jeton CSRF + deux champs + liste ;
- migration SQL présente (`first_sql_messages`) ;
- documentation sous `avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "db-transaction"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "db_transaction_controller.py"
VIEW = FILES / "mvc" / "views" / "db_transaction" / "index.html"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-forge" / "avance" / "db-transaction.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 30"]


def test_resolves():
    m = resolve("db-transaction")
    assert m["id"] == "db-transaction" and m["number"] == 30
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("db-transaction", "db_transaction", "transaction", "30"):
        assert resolve(a)["id"] == "db-transaction"


def test_doc_url_pointe_avance():
    assert "welcome-forge/avance/db-transaction" in resolve("db-transaction")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/db-transaction") in routes
    assert ("POST", "/db-transaction") in routes


def test_controller_transaction_and_rollback():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from core.database.transaction import transaction" in text
    assert "from core.database.db import fetch_all, insert" in text
    assert "with transaction() as tx:" in text
    # deux insertions dans la transaction
    assert text.count("insert(INSERT_MESSAGE") >= 2
    assert "tx=tx" in text
    # rollback déclenché par une exception
    assert "raise ValueError" in text
    assert "csrf_token" in text
    assert "redirect(" in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "DbTransactionController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "store"} <= methods


def test_view_post_form_with_csrf_and_two_fields():
    html = VIEW.read_text(encoding="utf-8")
    assert 'method="post"' in html
    assert 'name="csrf_token"' in html
    assert 'name="message_a"' in html and 'name="message_b"' in html
    assert "{% for m in messages %}" in html


def test_migration_present():
    sqls = list(MIGRATIONS.glob("*.sql"))
    assert sqls and "first_sql_messages" in "\n".join(
        p.read_text(encoding="utf-8") for p in sqls
    )


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Écritures transactionnelles"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "db-transaction" in idx and "Écritures transactionnelles" in idx
