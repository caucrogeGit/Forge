"""Garde-fou STARTER-DELETE-RECORD-001 (test proportionné).

Contrat du palier 6 du niveau intermédiaire — Supprimer un enregistrement :

- starter.json : `delete-record`, slot 17, requires_db true ;
- snippet : GET liste, POST suppression ;
- contrôleur : `execute("DELETE … WHERE id = ?")` paramétré,
  `request.route_param("id")`, CSRF ; après écriture, relit + ré-affiche ;
- vue : suppression par mini-formulaire POST + jeton CSRF (pas de lien GET) ;
- migration ; doc + catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "delete-record"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "delete_record_controller.py"
VIEW = FILES / "mvc" / "views" / "delete_record" / "index.html"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-forge" / "intermediaire" / "delete-record.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 17"]


def test_resolves():
    m = resolve("delete-record")
    assert m["id"] == "delete-record" and m["number"] == 17
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("delete-record", "delete_record", "delete", "17"):
        assert resolve(a)["id"] == "delete-record"


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/delete-record") in routes
    assert ("POST", "/delete-record/{id}") in routes


def test_controller_delete():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from core.database.db import execute, fetch_all" in text
    assert "DELETE FROM first_sql_messages WHERE id = ?" in text
    assert 'request.route_param("id")' in text
    assert "csrf_token" in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "DeleteRecordController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "delete"} <= methods


def test_view_post_delete_with_csrf():
    html = VIEW.read_text(encoding="utf-8")
    assert 'method="post"' in html
    assert 'name="csrf_token"' in html
    assert "/delete-record/{{ m.id }}" in html


def test_migration_present():
    sqls = list(MIGRATIONS.glob("*.sql"))
    assert sqls and "first_sql_messages" in "\n".join(p.read_text(encoding="utf-8") for p in sqls)


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Supprimer un enregistrement"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "delete-record" in idx and "Supprimer un enregistrement" in idx
