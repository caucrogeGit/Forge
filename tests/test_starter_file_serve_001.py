"""Garde-fou STARTER-FILE-SERVE-001 (test proportionné).

Palier 3 débutant welcome-files — Servir un fichier : slot 60, requires_db false,
routes `/file-serve` + `/file-serve/download`, contrôleur `serve_media_file`,
vue présente, doc sous `welcome-files/debutant/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "file-serve"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "file_serve_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "file_serve" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-files" / "debutant" / "file-serve.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 60"]


def test_resolves():
    m = resolve("file-serve")
    assert m["id"] == "file-serve" and m["number"] == 60
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("file-serve", "file_serve", "60"):
        assert resolve(a)["id"] == "file-serve"


def test_doc_url():
    assert "welcome-files/debutant/file-serve" in resolve("file-serve")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/file-serve") in routes
    assert ("GET", "/file-serve/download") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_files import serve_media_file" in text
    assert "serve_media_file(" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "FileServeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "download"} <= methods


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Servir un fichier"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "file-serve" in idx and "Servir un fichier" in idx
