"""Garde-fou STARTER-FILES-WELCOME-001 (test proportionné).

Palier 1 débutant welcome-files — Bonjour Forge Files : slot 58, requires_db
false, routes `/files-welcome` + `/inspect`, contrôleur `upload_root` + politique
d'upload, doc sous `welcome-files/debutant/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "files-welcome"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "files_welcome_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-files" / "debutant" / "files-welcome.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 58"]


def test_resolves():
    m = resolve("files-welcome")
    assert m["id"] == "files-welcome" and m["number"] == 58
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("files-welcome", "files_welcome", "58"):
        assert resolve(a)["id"] == "files-welcome"


def test_doc_url():
    assert "welcome-files/debutant/files-welcome" in resolve("files-welcome")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/files-welcome") in routes
    assert ("GET", "/files-welcome/inspect") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "upload_root" in text
    assert "Response.text(" in text and "Response.json(" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "FilesWelcomeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "inspect"} <= methods


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Bonjour Forge Files"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "files-welcome" in idx and "Bonjour Forge Files" in idx
