"""Garde-fou STARTER-UPDATE-RECORD-001 (test proportionné).

Contrat du palier 5 du niveau intermédiaire — Modifier un enregistrement :

- starter.json : `update-record`, slot 22, requires_db true ;
- snippet : GET liste, GET edit, POST update ;
- contrôleur : `fetch_one` (pré-remplissage) + `execute("UPDATE … WHERE id=?")`,
  `request.route_param("id")`, `request.form("content")`, CSRF (csrf_token),
  refus 422 si vide, 404 si introuvable ;
- vue d'édition pré-remplie avec jeton CSRF ; migration ; doc + catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "update-record"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "update_record_controller.py"
EDIT_VIEW = FILES / "mvc" / "views" / "update_record" / "edit.html"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-forge" / "intermediaire" / "update-record.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 22"]


def test_resolves():
    m = resolve("update-record")
    assert m["id"] == "update-record" and m["number"] == 22
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("update-record", "update_record", "update", "22"):
        assert resolve(a)["id"] == "update-record"


def test_snippet_three_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/update-record") in routes
    assert ("GET", "/update-record/{id}/edit") in routes
    assert ("POST", "/update-record/{id}") in routes


def test_controller_update_and_prefill():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from core.database.db import execute, fetch_all, fetch_one" in text
    assert "UPDATE first_sql_messages SET content = ? WHERE id = ?" in text
    assert 'request.route_param("id")' in text
    assert 'request.form("content"' in text
    assert "csrf_token" in text
    # garde-fous HTTP honnêtes
    assert "status=404" in text and "status=422" in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "UpdateRecordController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "edit", "update"} <= methods


def test_edit_view_prefilled_with_csrf():
    html = EDIT_VIEW.read_text(encoding="utf-8")
    assert 'method="post"' in html
    assert 'name="csrf_token"' in html
    assert 'value="{{ message.content }}"' in html


def test_migration_present():
    sqls = list(MIGRATIONS.glob("*.sql"))
    assert sqls and "first_sql_messages" in "\n".join(p.read_text(encoding="utf-8") for p in sqls)


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Modifier un enregistrement"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "update-record" in idx and "Modifier un enregistrement" in idx
