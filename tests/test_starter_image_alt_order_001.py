"""Garde-fou STARTER-IMAGE-ALT-ORDER-001 (test proportionné).

Contrat du palier 3 du niveau intermédiaire de welcome-images —
Texte alternatif et ordre :

- starter.json : `image-alt-order`, slot 48, requires_db **true** ;
- snippet : GET `/image-alt-order`, POST `/image-alt-order` ;
- contrôleur : `update_media_alt_text` + `update_media_position`, repli pédagogique ;
- migration `media` livrée avec le starter ; vue présente ;
- documentation sous `welcome-images/intermediaire/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "image-alt-order"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "image_alt_order_controller.py"
VIEW = FILES / "mvc" / "views" / "image_alt_order" / "index.html"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-images" / "intermediaire" / "image-alt-order.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 48"]


def test_resolves():
    m = resolve("image-alt-order")
    assert m["id"] == "image-alt-order" and m["number"] == 48
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("image-alt-order", "image_alt_order", "48"):
        assert resolve(a)["id"] == "image-alt-order"


def test_doc_url_pointe_welcome_images():
    assert "welcome-images/intermediaire/image-alt-order" in resolve("image-alt-order")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/image-alt-order") in routes
    assert ("POST", "/image-alt-order") in routes


def test_controller_updates_alt_and_position():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "update_media_alt_text" in text and "update_media_position" in text
    assert "list_media_for_entity" in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "ImageAltOrderController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "update"} <= methods


def test_migration_and_view_present():
    assert VIEW.is_file()
    migrations = list(MIGRATIONS.glob("*_create_media.sql"))
    assert migrations, "Le starter doit livrer la migration de la table media."


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Texte alternatif et ordre"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "image-alt-order" in idx and "Texte alternatif et ordre" in idx
