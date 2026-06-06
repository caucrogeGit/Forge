"""Garde-fou STARTER-JSON-API-001 (test proportionné).

Contrat du palier 4 du niveau avancé — API JSON protégée :

- starter.json : `json-api`, slot 23, requires_db **true** ;
- snippet : GET `/json-api` ;
- contrôleur : `request.header("Authorization")`, vérification d'un jeton
  Bearer, `Response.json(...)` (200 et 401), `fetch_all` ;
- migration SQL présente (`first_sql_messages`) ;
- documentation sous `avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "json-api"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "json_api_controller.py"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-forge" / "avance" / "json-api.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 23"]


def test_resolves():
    m = resolve("json-api")
    assert m["id"] == "json-api" and m["number"] == 23
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("json-api", "json_api", "api", "23"):
        assert resolve(a)["id"] == "json-api"


def test_doc_url_pointe_avance():
    assert "welcome-forge/avance/json-api" in resolve("json-api")["doc_url"]


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = routes_from_snippet(snip)
    assert any(m == "GET" and p == "/json-api" for m, p, *_ in routes)


def test_controller_bearer_and_json():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert 'request.header("Authorization")' in text
    assert "Bearer" in text
    assert "Response.json(" in text
    assert "status=401" in text
    assert "from core.database.db import fetch_all" in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "JsonApiController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "index" in methods


def test_migration_present():
    sqls = list(MIGRATIONS.glob("*.sql"))
    assert sqls and "first_sql_messages" in "\n".join(
        p.read_text(encoding="utf-8") for p in sqls
    )


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# API JSON protégée"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "json-api" in idx and "API JSON protégée" in idx
