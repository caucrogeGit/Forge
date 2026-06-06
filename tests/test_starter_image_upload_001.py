"""Garde-fou STARTER-IMAGE-UPLOAD-001 (test proportionné).

Contrat du palier 2 du niveau débutant de la progression welcome-images —
Téléverser une image :

- starter.json : `image-upload`, slot 44, requires_db **false** ;
- snippet : GET `/image-upload`, POST `/image-upload` ;
- contrôleur : `save_image_upload`, `request.file(...)`, gestion `UploadError`,
  pas de base de données ; vue présente ;
- documentation sous `welcome-images/debutant/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "image-upload"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "image_upload_controller.py"
VIEW = FILES / "mvc" / "views" / "image_upload" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-images" / "debutant" / "image-upload.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 44"]


def test_resolves():
    m = resolve("image-upload")
    assert m["id"] == "image-upload" and m["number"] == 44
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("image-upload", "image_upload", "44"):
        assert resolve(a)["id"] == "image-upload"


def test_doc_url_pointe_welcome_images():
    assert "welcome-images/debutant/image-upload" in resolve("image-upload")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/image-upload") in routes
    assert ("POST", "/image-upload") in routes


def test_controller_uses_save_image_upload_no_db():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_images import save_image_upload" in text
    assert "from forge_mvc_files import UploadError" in text
    assert "save_image_upload(" in text
    assert 'request.file("image")' in text
    assert "except UploadError" in text
    assert "core.database" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "ImageUploadController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "upload"} <= methods


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Téléverser une image"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "image-upload" in idx and "Téléverser une image" in idx
