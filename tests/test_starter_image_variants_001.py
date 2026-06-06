"""Garde-fou STARTER-IMAGE-VARIANTS-001 (test proportionné).

Contrat du palier 3 du niveau débutant de la progression welcome-images —
Miniatures et variantes :

- starter.json : `image-variants`, slot 45, requires_db **false** ;
- snippet : GET `/image-variants`, GET `/image-variants/inspect` ;
- contrôleur : `image_variant_relative_paths`, `media_url`, `IMAGE_VARIANT_SIZES`,
  pas de base de données ; vue présente ;
- documentation sous `welcome-images/debutant/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "image-variants"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "image_variants_controller.py"
VIEW = FILES / "mvc" / "views" / "image_variants" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-images" / "debutant" / "image-variants.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 45"]


def test_resolves():
    m = resolve("image-variants")
    assert m["id"] == "image-variants" and m["number"] == 45
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("image-variants", "image_variants", "45"):
        assert resolve(a)["id"] == "image-variants"


def test_doc_url_pointe_welcome_images():
    assert "welcome-images/debutant/image-variants" in resolve("image-variants")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/image-variants") in routes
    assert ("GET", "/image-variants/inspect") in routes


def test_controller_derives_variants_no_db():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "image_variant_relative_paths" in text
    assert "media_url" in text
    assert "IMAGE_VARIANT_SIZES" in text
    assert "core.database" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "ImageVariantsController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "inspect"} <= methods


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Miniatures et variantes"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "image-variants" in idx and "Miniatures et variantes" in idx
