"""Garde-fou STARTER-FILE-STORE-001 (test proportionné).

Palier 2 débutant welcome-files — Stocker un document : slot 59, requires_db
false, routes GET/POST `/file-store`, contrôleur `save_upload` + `UploadError`,
vue présente, doc sous `welcome-files/debutant/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "file-store"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "file_store_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "file_store" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-files" / "debutant" / "file-store.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 59"]


def test_resolves():
    m = resolve("file-store")
    assert m["id"] == "file-store" and m["number"] == 59
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("file-store", "file_store", "59"):
        assert resolve(a)["id"] == "file-store"


def test_doc_url():
    assert "welcome-files/debutant/file-store" in resolve("file-store")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/file-store") in routes
    assert ("POST", "/file-store") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_files import UploadError, save_upload" in text
    assert "save_upload(" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "FileStoreController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "store"} <= methods


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Stocker un document"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "file-store" in idx and "Stocker un document" in idx
