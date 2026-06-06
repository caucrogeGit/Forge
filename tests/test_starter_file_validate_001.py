"""Garde-fou STARTER-FILE-VALIDATE-001 (test proportionné).

Palier 1 intermédiaire welcome-files — Valider un upload : slot 55, requires_db
false, routes GET/POST `/file-validate`, contrôleur taxonomie `UploadError`,
vue présente, doc sous `welcome-files/intermediaire/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "file-validate"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "file_validate_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "file_validate" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-files" / "intermediaire" / "file-validate.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 55"]


def test_resolves():
    m = resolve("file-validate")
    assert m["id"] == "file-validate" and m["number"] == 55
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("file-validate", "file_validate", "55"):
        assert resolve(a)["id"] == "file-validate"


def test_doc_url():
    assert "welcome-files/intermediaire/file-validate" in resolve("file-validate")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/file-validate") in routes
    assert ("POST", "/file-validate") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "UploadInvalidExtensionError" in text and "UploadTooLargeError" in text
    assert "save_upload(" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "FileValidateController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "check"} <= methods


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Valider un upload"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "file-validate" in idx and "Valider un upload" in idx
