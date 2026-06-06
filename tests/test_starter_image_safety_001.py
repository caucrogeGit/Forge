"""Garde-fou STARTER-IMAGE-SAFETY-001 (test proportionné).

Contrat du palier 3 du niveau avancé de welcome-images —
Garde de sécurité à l'upload :

- starter.json : `image-safety`, slot 51, requires_db **false** ;
- snippet : GET `/image-safety`, POST `/image-safety`, GET `/image-safety/inspect` ;
- contrôleur : `verify_image_content` + lecture de `upload_max_image_pixels`,
  aucune écriture ni base de données ; vue présente ;
- documentation sous `welcome-images/avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "image-safety"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "image_safety_controller.py"
VIEW = FILES / "mvc" / "views" / "image_safety" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-images" / "avance" / "image-safety.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 51"]


def test_resolves():
    m = resolve("image-safety")
    assert m["id"] == "image-safety" and m["number"] == 51
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("image-safety", "image_safety", "51"):
        assert resolve(a)["id"] == "image-safety"


def test_doc_url_pointe_welcome_images():
    assert "welcome-images/avance/image-safety" in resolve("image-safety")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/image-safety") in routes
    assert ("POST", "/image-safety") in routes
    assert ("GET", "/image-safety/inspect") in routes


def test_controller_verifies_no_db():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "verify_image_content" in text
    assert "upload_max_image_pixels" in text
    assert "core.database" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "ImageSafetyController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "check", "inspect"} <= methods


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Garde de sécurité à l'upload"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "image-safety" in idx and "Garde de sécurité à l'upload" in idx
