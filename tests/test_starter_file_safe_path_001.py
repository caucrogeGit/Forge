"""Garde-fou STARTER-FILE-SAFE-PATH-001 (test proportionné).

Palier 2 avancé welcome-files — Chemin anti-traversal : slot 65, requires_db
false, routes `/file-safe-path` + `/inspect`, contrôleur `is_safe_media_path` +
`normalize_media_path`, vue présente, doc sous `welcome-files/avance/`.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "file-safe-path"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "file_safe_path_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "file_safe_path" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-files" / "avance" / "file-safe-path.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 65"]


def test_resolves():
    m = resolve("file-safe-path")
    assert m["id"] == "file-safe-path" and m["number"] == 65
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("file-safe-path", "file_safe_path", "65"):
        assert resolve(a)["id"] == "file-safe-path"


def test_doc_url():
    assert "welcome-files/avance/file-safe-path" in resolve("file-safe-path")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/file-safe-path") in routes
    assert ("GET", "/file-safe-path/inspect") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "is_safe_media_path" in text and "normalize_media_path" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "FileSafePathController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "inspect"} <= methods


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Chemin anti-traversal"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "file-safe-path" in idx and "Chemin anti-traversal" in idx
