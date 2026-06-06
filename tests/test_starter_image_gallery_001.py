"""Garde-fou STARTER-IMAGE-GALLERY-001 (test proportionné).

Contrat du palier 2 du niveau intermédiaire de welcome-images — Afficher la galerie :

- starter.json : `image-gallery`, slot 47, requires_db **true** ;
- snippet : GET `/image-gallery` ;
- contrôleur : `get_media_gallery`, repli pédagogique ;
- migration `media` livrée avec le starter ; vue présente ;
- documentation sous `welcome-images/intermediaire/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "image-gallery"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "image_gallery_controller.py"
VIEW = FILES / "mvc" / "views" / "image_gallery" / "index.html"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-images" / "intermediaire" / "image-gallery.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 47"]


def test_resolves():
    m = resolve("image-gallery")
    assert m["id"] == "image-gallery" and m["number"] == 47
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("image-gallery", "image_gallery", "47"):
        assert resolve(a)["id"] == "image-gallery"


def test_doc_url_pointe_welcome_images():
    assert "welcome-images/intermediaire/image-gallery" in resolve("image-gallery")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/image-gallery") in routes


def test_controller_reads_gallery():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_images import get_media_gallery" in text
    assert "get_media_gallery(" in text
    assert "except Exception" in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "ImageGalleryController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "index" in methods


def test_migration_and_view_present():
    assert VIEW.is_file()
    migrations = list(MIGRATIONS.glob("*_create_media.sql"))
    assert migrations, "Le starter doit livrer la migration de la table media."


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Afficher la galerie"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "image-gallery" in idx and "Afficher la galerie" in idx
