"""Garde-fou STARTER-FILTER-LIST-001 (test proportionné).

Contrat du palier 2 du niveau intermédiaire — Rechercher / filtrer :

- starter.json : `filter-list`, slot 13, requires_db true ;
- snippet : `GET /filter-list` ;
- contrôleur : `fetch_all` + `request.param("q")` + `WHERE content LIKE ?`
  paramétré (jamais concaténé) ;
- vue : formulaire de recherche en `method="get"` (pas de CSRF) ;
- migration SQL présente ;
- doc sous `intermediaire/`, sans pattern interdit, listée au catalogue.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "filter-list"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "filter_list_controller.py"
VIEW = FILES / "mvc" / "views" / "filter_list" / "index.html"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-forge" / "intermediaire" / "filter-list.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

MIGRATION_RE = re.compile(r"^\d{14}_[a-z0-9_]+\.sql$")
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 13"]


def test_resolves():
    m = resolve("filter-list")
    assert m["id"] == "filter-list" and m["number"] == 13
    assert m.get("requires_db") is True and m.get("kind") == "skeleton"


def test_aliases():
    for a in ("filter-list", "filter_list", "filter", "13"):
        assert resolve(a)["id"] == "filter-list"


def test_doc_url_intermediaire():
    assert "welcome-forge/intermediaire/filter-list" in resolve("filter-list")["doc_url"]


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    assert "# forge-starter:filter-list:start" in snip
    routes = routes_from_snippet(snip)
    assert any(mth == "GET" and p == "/filter-list" for mth, p, *_ in routes)


def test_controller_param_and_parameterized_where():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from core.database.db import fetch_all" in text
    assert 'request.param("q"' in text
    assert "WHERE content LIKE ?" in text
    # paramètre lié, pas de concaténation du motif dans la chaîne SQL
    assert 'f"%{query}%"' in text
    assert "def index(request: Request) -> Response" in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "FilterListController"), None)
    assert ctrl is not None
    assert "BaseController" in [ast.unparse(b) for b in ctrl.bases]


def test_controller_no_write():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "INSERT" not in text and "UPDATE" not in text and "DELETE" not in text


def test_view_get_search_form():
    html = VIEW.read_text(encoding="utf-8")
    assert 'method="get"' in html
    assert 'name="q"' in html
    assert "{% for m in messages %}" in html
    # recherche GET → pas de jeton CSRF (réservé aux écritures)
    assert "csrf_token" not in html


def test_migration_present():
    sqls = list(MIGRATIONS.glob("*.sql"))
    assert sqls and all(MIGRATION_RE.match(p.name) for p in sqls)
    assert "first_sql_messages" in "\n".join(p.read_text(encoding="utf-8") for p in sqls)


def test_doc_and_catalogue():
    assert DOC.exists()
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Rechercher / filtrer une liste"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "filter-list" in idx and "Rechercher / filtrer" in idx
