"""Garde-fou STARTER-FILE-RATE-LIMIT-001 (test proportionné).

Palier 2 intermédiaire welcome-files — Limiter les uploads : slot 62, requires_db
false, routes GET/POST `/file-rate-limit`, contrôleur `is_upload_rate_limited` +
`record_upload_attempt`, vue présente, doc sous `welcome-files/intermediaire/`.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "file-rate-limit"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "file_rate_limit_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "file_rate_limit" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-files" / "intermediaire" / "file-rate-limit.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 62"]


def test_resolves():
    m = resolve("file-rate-limit")
    assert m["id"] == "file-rate-limit" and m["number"] == 62
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("file-rate-limit", "file_rate_limit", "62"):
        assert resolve(a)["id"] == "file-rate-limit"


def test_doc_url():
    assert "welcome-files/intermediaire/file-rate-limit" in resolve("file-rate-limit")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/file-rate-limit") in routes
    assert ("POST", "/file-rate-limit") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "is_upload_rate_limited" in text and "record_upload_attempt" in text
    assert "request.ip" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "FileRateLimitController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "upload"} <= methods


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Limiter les uploads"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "file-rate-limit" in idx and "Limiter les uploads" in idx
