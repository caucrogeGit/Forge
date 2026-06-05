"""Garde-fou STARTER-IMAGE-DELETE-001 (test proportionné).

Contrat du palier 2 du niveau avancé de welcome-images — Supprimer proprement :

- starter.json : `image-delete`, slot 56, requires_db **true** ;
- snippet : GET `/image-delete`, POST `/image-delete` ;
- contrôleur : `delete_media(delete_files=True)` + `list_media_for_entity` ;
- migration `media` livrée avec le starter ; vue présente ;
- documentation sous `welcome-images/avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "image-delete"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "image_delete_controller.py"
VIEW = FILES / "mvc" / "views" / "image_delete" / "index.html"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-images" / "avance" / "image-delete.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 56"]


def test_resolves():
    m = resolve("image-delete")
    assert m["id"] == "image-delete" and m["number"] == 56
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("image-delete", "image_delete", "56"):
        assert resolve(a)["id"] == "image-delete"


def test_doc_url_pointe_welcome_images():
    assert "welcome-images/avance/image-delete" in resolve("image-delete")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/image-delete") in routes
    assert ("POST", "/image-delete") in routes


def test_controller_deletes_with_files():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "delete_media" in text
    assert "delete_files=True" in text
    assert "list_media_for_entity" in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "ImageDeleteController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "delete"} <= methods


def test_migration_and_view_present():
    assert VIEW.is_file()
    assert list(MIGRATIONS.glob("*_create_media.sql"))


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Supprimer proprement"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "image-delete" in idx and "Supprimer proprement" in idx
