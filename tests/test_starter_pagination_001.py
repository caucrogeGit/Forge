"""Garde-fou STARTER-PAGINATION-001 (test proportionné).

Contrat du palier 3 du niveau intermédiaire — Paginer une liste :

- starter.json : `pagination`, slot 20, requires_db true ;
- snippet : `GET /pagination` ;
- contrôleur : `fetch_all` + `fetch_one`, `LIMIT ? OFFSET ?` paramétré,
  `COUNT(*)`, conversion robuste du paramètre `page` ;
- vue : liens précédent/suivant conditionnels ;
- migration SQL présente ; doc sous `intermediaire/`, catalogue.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "pagination"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "pagination_controller.py"
VIEW = FILES / "mvc" / "views" / "pagination" / "index.html"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-forge" / "intermediaire" / "pagination.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

MIGRATION_RE = re.compile(r"^\d{14}_[a-z0-9_]+\.sql$")
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 20"]


def test_resolves():
    m = resolve("pagination")
    assert m["id"] == "pagination" and m["number"] == 20
    assert m.get("requires_db") is True and m.get("kind") == "skeleton"


def test_aliases():
    for a in ("pagination", "paginate", "20"):
        assert resolve(a)["id"] == "pagination"


def test_doc_url_intermediaire():
    assert "welcome-forge/intermediaire/pagination" in resolve("pagination")["doc_url"]


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = routes_from_snippet(snip)
    assert any(mth == "GET" and p == "/pagination" for mth, p, *_ in routes)


def test_controller_limit_offset_count():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from core.database.db import fetch_all, fetch_one" in text
    assert "LIMIT ? OFFSET ?" in text
    assert "COUNT(*)" in text
    assert 'request.param("page"' in text
    assert "def index(request: Request) -> Response" in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "PaginationController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]


def test_controller_robust_page_parse():
    # une page invalide (non numérique) ne doit pas planter : présence d'un
    # garde de conversion.
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "except (TypeError, ValueError)" in text


def test_controller_no_write():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "INSERT" not in text and "UPDATE" not in text and "DELETE" not in text


def test_view_prev_next_conditional():
    html = VIEW.read_text(encoding="utf-8")
    assert "{% if has_prev %}" in html and "{% if has_next %}" in html
    assert "page={{ page - 1 }}" in html and "page={{ page + 1 }}" in html


def test_migration_present():
    sqls = list(MIGRATIONS.glob("*.sql"))
    assert sqls and all(MIGRATION_RE.match(p.name) for p in sqls)


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Paginer une liste"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "pagination" in idx and "Paginer une liste" in idx
