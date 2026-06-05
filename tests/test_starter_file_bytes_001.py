"""Garde-fou STARTER-FILE-BYTES-001 (test proportionné).

Palier 3 avancé welcome-files — Écrire des octets générés : slot 66, requires_db
false, routes GET/POST `/file-bytes`, contrôleur `save_bytes`, vue présente,
doc sous `welcome-files/avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "file-bytes"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "file_bytes_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "file_bytes" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-files" / "avance" / "file-bytes.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 66"]


def test_resolves():
    m = resolve("file-bytes")
    assert m["id"] == "file-bytes" and m["number"] == 66
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("file-bytes", "file_bytes", "66"):
        assert resolve(a)["id"] == "file-bytes"


def test_doc_url():
    assert "welcome-files/avance/file-bytes" in resolve("file-bytes")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/file-bytes") in routes
    assert ("POST", "/file-bytes") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_files import save_bytes, upload_root" in text
    assert "save_bytes(" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "FileBytesController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "generate"} <= methods


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Écrire des octets générés"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "file-bytes" in idx and "Écrire des octets générés" in idx
