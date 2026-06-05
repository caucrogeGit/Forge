"""Garde-fou STARTER-FILE-DELETE-001 (test proportionné).

Palier 3 intermédiaire welcome-files — Supprimer un fichier : slot 63, requires_db
false, routes GET/POST `/file-delete`, contrôleur `delete_media_file`, vue
présente, doc sous `welcome-files/intermediaire/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "file-delete"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "file_delete_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "file_delete" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-files" / "intermediaire" / "file-delete.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 63"]


def test_resolves():
    m = resolve("file-delete")
    assert m["id"] == "file-delete" and m["number"] == 63
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("file-delete", "file_delete", "63"):
        assert resolve(a)["id"] == "file-delete"


def test_doc_url():
    assert "welcome-files/intermediaire/file-delete" in resolve("file-delete")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/file-delete") in routes
    assert ("POST", "/file-delete") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_files import delete_media_file" in text
    assert "delete_media_file(" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "FileDeleteController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "delete"} <= methods


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Supprimer un fichier"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "file-delete" in idx and "Supprimer un fichier" in idx
