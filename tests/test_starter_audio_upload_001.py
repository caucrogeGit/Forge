"""Garde-fou STARTER-AUDIO-UPLOAD-001 (test proportionné).

Palier 2 débutant welcome-audio — Téléverser un audio : slot 68, requires_db
false, routes GET/POST `/audio-upload`, contrôleur `ingest_audio` +
`AudioIngestError`, vue présente, doc sous `welcome-audio/debutant/`.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "audio-upload"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "audio_upload_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "audio_upload" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-audio" / "debutant" / "audio-upload.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 68"]


def test_resolves():
    m = resolve("audio-upload")
    assert m["id"] == "audio-upload" and m["number"] == 68
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("audio-upload", "audio_upload", "68"):
        assert resolve(a)["id"] == "audio-upload"


def test_doc_url():
    assert "welcome-audio/debutant/audio-upload" in resolve("audio-upload")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/audio-upload") in routes
    assert ("POST", "/audio-upload") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_audio import AudioIngestError, ingest_audio" in text
    assert "ingest_audio(" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "AudioUploadController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "upload"} <= methods


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Téléverser un audio"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "audio-upload" in idx and "Téléverser un audio" in idx
