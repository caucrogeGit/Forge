"""Garde-fou STARTER-IMAGE-ATTACH-001 (test proportionné).

Contrat du palier 1 du niveau intermédiaire de welcome-images —
Rattacher une image à une entité :

- starter.json : `image-attach`, slot 52, requires_db **true** ;
- snippet : GET `/image-attach`, POST `/image-attach` ;
- contrôleur : `save_image_upload` + `attach_media_to_entity`, repli pédagogique ;
- migration `media` livrée avec le starter ; vue présente ;
- documentation sous `welcome-images/intermediaire/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "image-attach"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "image_attach_controller.py"
VIEW = FILES / "mvc" / "views" / "image_attach" / "index.html"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-images" / "intermediaire" / "image-attach.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 52"]


def test_resolves():
    m = resolve("image-attach")
    assert m["id"] == "image-attach" and m["number"] == 52
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("image-attach", "image_attach", "52"):
        assert resolve(a)["id"] == "image-attach"


def test_doc_url_pointe_welcome_images():
    assert "welcome-images/intermediaire/image-attach" in resolve("image-attach")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/image-attach") in routes
    assert ("POST", "/image-attach") in routes


def test_controller_attaches_media():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_images import attach_media_to_entity, save_image_upload" in text
    assert "attach_media_to_entity(" in text
    assert "save_image_upload(" in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "ImageAttachController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "attach"} <= methods


def test_migration_and_view_present():
    assert VIEW.is_file()
    migrations = list(MIGRATIONS.glob("*_create_media.sql"))
    assert migrations, "Le starter doit livrer la migration de la table media."
    assert "CREATE TABLE IF NOT EXISTS media" in migrations[0].read_text(encoding="utf-8")


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Rattacher une image à une entité"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "image-attach" in idx and "Rattacher une image à une entité" in idx
