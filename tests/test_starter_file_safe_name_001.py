"""Garde-fou STARTER-FILE-SAFE-NAME-001 (test proportionné).

Palier 1 avancé welcome-files — Assainir un nom de fichier : slot 64, requires_db
false, routes `/file-safe-name` + `/inspect`, contrôleur `secure_filename`, vue
présente, doc sous `welcome-files/avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "file-safe-name"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "file_safe_name_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "file_safe_name" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-files" / "avance" / "file-safe-name.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 64"]


def test_resolves():
    m = resolve("file-safe-name")
    assert m["id"] == "file-safe-name" and m["number"] == 64
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("file-safe-name", "file_safe_name", "64"):
        assert resolve(a)["id"] == "file-safe-name"


def test_doc_url():
    assert "welcome-files/avance/file-safe-name" in resolve("file-safe-name")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/file-safe-name") in routes
    assert ("GET", "/file-safe-name/inspect") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "secure_filename" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "FileSafeNameController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "inspect"} <= methods


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Assainir un nom de fichier"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "file-safe-name" in idx and "Assainir un nom de fichier" in idx
