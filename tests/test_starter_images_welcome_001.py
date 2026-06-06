"""Garde-fou STARTER-IMAGES-WELCOME-001 (test proportionné).

Contrat du palier 1 du niveau débutant de la progression welcome-images —
Bonjour Forge Images :

- starter.json : `images-welcome`, slot 43, requires_db **false** ;
- snippet : GET `/images-welcome`, GET `/images-welcome/inspect` ;
- contrôleur : constantes `ALLOWED_IMAGE_EXTENSIONS` / `IMAGE_VARIANT_SIZES`,
  `Response.text` + `Response.json`, pas de base de données ;
- documentation sous `welcome-images/debutant/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "images-welcome"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "images_welcome_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-images" / "debutant" / "images-welcome.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 43"]


def test_resolves():
    m = resolve("images-welcome")
    assert m["id"] == "images-welcome" and m["number"] == 43
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("images-welcome", "images_welcome", "43"):
        assert resolve(a)["id"] == "images-welcome"


def test_doc_url_pointe_welcome_images():
    assert "welcome-images/debutant/images-welcome" in resolve("images-welcome")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/images-welcome") in routes
    assert ("GET", "/images-welcome/inspect") in routes


def test_controller_inspects_capabilities_no_db():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_images import" in text
    assert "ALLOWED_IMAGE_EXTENSIONS" in text and "IMAGE_VARIANT_SIZES" in text
    assert "Response.text(" in text and "Response.json(" in text
    assert "core.database" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "ImagesWelcomeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "inspect"} <= methods


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Bonjour Forge Images"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "images-welcome" in idx and "Bonjour Forge Images" in idx
