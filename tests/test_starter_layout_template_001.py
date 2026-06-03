"""Garde-fou STARTER-LAYOUT-TEMPLATE-001 (test proportionné).

Contrat du palier 4 du niveau intermédiaire — Héritage de gabarit :

- starter.json : `layout-template`, slot 21, requires_db **false** ;
- snippet : `GET /layout-template` ;
- un gabarit `layouts/starter_layout.html` avec des `{% block %}` ;
- une page qui `{% extends %}` le gabarit ;
- aucune base de données ; doc sous `intermediaire/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "layout-template"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "layout_template_controller.py"
LAYOUT = FILES / "mvc" / "views" / "layouts" / "starter_layout.html"
PAGE = FILES / "mvc" / "views" / "layout_template" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-forge" / "intermediaire" / "layout-template.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 21"]


def test_resolves():
    m = resolve("layout-template")
    assert m["id"] == "layout-template" and m["number"] == 21
    assert m.get("kind") == "skeleton"


def test_requires_db_false():
    assert resolve("layout-template").get("requires_db") is False


def test_aliases():
    for a in ("layout-template", "layout_template", "layout", "21"):
        assert resolve(a)["id"] == "layout-template"


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = routes_from_snippet(snip)
    assert any(mth == "GET" and p == "/layout-template" for mth, p, *_ in routes)


def test_controller_typed_no_db():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "def index(request: Request) -> Response" in text
    assert "core.database" not in text  # palier vue pure, sans BDD
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "LayoutTemplateController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]


def test_layout_declares_blocks():
    html = LAYOUT.read_text(encoding="utf-8")
    assert "{% block title %}" in html
    assert "{% block content %}" in html
    assert "<!DOCTYPE html>" in html


def test_page_extends_layout():
    html = PAGE.read_text(encoding="utf-8")
    assert '{% extends "layouts/starter_layout.html" %}' in html
    assert "{% block content %}" in html
    assert "<!DOCTYPE html>" not in html  # la page n'écrit plus le document complet


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Héritage de gabarit"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "layout-template" in idx and "Héritage de gabarit" in idx
