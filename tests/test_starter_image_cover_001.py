"""Garde-fou STARTER-IMAGE-COVER-001 (test proportionné).

Contrat du palier 1 du niveau avancé de welcome-images — Image de couverture :

- starter.json : `image-cover`, slot 55, requires_db **true** ;
- snippet : GET `/image-cover`, POST `/image-cover` ;
- contrôleur : `get_cover_media` + `attach_media_to_entity` (rôle cover) ;
- migration `media` livrée avec le starter ; vue présente ;
- documentation sous `welcome-images/avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "image-cover"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "image_cover_controller.py"
VIEW = FILES / "mvc" / "views" / "image_cover" / "index.html"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-images" / "avance" / "image-cover.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 55"]


def test_resolves():
    m = resolve("image-cover")
    assert m["id"] == "image-cover" and m["number"] == 55
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("image-cover", "image_cover", "55"):
        assert resolve(a)["id"] == "image-cover"


def test_doc_url_pointe_welcome_images():
    assert "welcome-images/avance/image-cover" in resolve("image-cover")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/image-cover") in routes
    assert ("POST", "/image-cover") in routes


def test_controller_uses_cover():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "get_cover_media" in text
    assert "attach_media_to_entity" in text
    assert 'role="cover"' in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "ImageCoverController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "set_cover"} <= methods


def test_migration_and_view_present():
    assert VIEW.is_file()
    assert list(MIGRATIONS.glob("*_create_media.sql"))


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Image de couverture"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "image-cover" in idx and "Image de couverture" in idx
