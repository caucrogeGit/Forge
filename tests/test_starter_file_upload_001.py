"""Garde-fou STARTER-FILE-UPLOAD-001 (test proportionné).

Contrat du palier 2 du niveau avancé — Téléverser un fichier :

- starter.json : `file-upload`, slot 21, requires_db **false** ;
- snippet : GET formulaire, POST upload ;
- contrôleur : `request.file(...)`, `core.uploads.save_upload`, gestion de
  `UploadError`, CSRF ; pas de base de données ;
- vue : formulaire `multipart/form-data` + jeton CSRF + champ fichier ;
- documentation sous `avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "file-upload"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "file_upload_controller.py"
VIEW = FILES / "mvc" / "views" / "file_upload" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-forge" / "avance" / "file-upload.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 21"]


def test_resolves():
    m = resolve("file-upload")
    assert m["id"] == "file-upload" and m["number"] == 21
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("file-upload", "file_upload", "upload", "21"):
        assert resolve(a)["id"] == "file-upload"


def test_doc_url_pointe_avance():
    assert "welcome-forge/avance/file-upload" in resolve("file-upload")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/file-upload") in routes
    assert ("POST", "/file-upload") in routes


def test_controller_uploads_api_and_no_db():
    text = CONTROLLER.read_text(encoding="utf-8")
    # FILES-CLI-RENAME-001 (ADR-019) : l'upload est un opt-in (forge-mvc-files).
    assert "from forge_mvc_files import UploadError, save_upload" in text
    assert 'request.file("document")' in text
    assert "save_upload(" in text
    assert "csrf_token" in text
    # validation/erreur gérée explicitement
    assert "UploadError" in text
    # pas de base de données dans ce palier
    assert "core.database" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "FileUploadController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "upload"} <= methods


def test_view_multipart_form_with_csrf_and_file():
    html = VIEW.read_text(encoding="utf-8")
    assert 'method="post"' in html
    assert 'enctype="multipart/form-data"' in html
    assert 'name="csrf_token"' in html
    assert 'type="file"' in html and 'name="document"' in html


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Téléverser un fichier"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "file-upload" in idx and "Téléverser un fichier" in idx
