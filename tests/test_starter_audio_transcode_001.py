"""Garde-fou STARTER-AUDIO-TRANSCODE-001 (test proportionné).

Palier 2 avancé welcome-audio — Transcoder en MP3 : slot 71, requires_db false,
routes GET/POST `/audio-transcode`, contrôleur `transcode_to_mp3` + `FfmpegError`,
vue présente, doc sous `welcome-audio/avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "audio-transcode"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "audio_transcode_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "audio_transcode" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-audio" / "avance" / "audio-transcode.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 71"]


def test_resolves():
    m = resolve("audio-transcode")
    assert m["id"] == "audio-transcode" and m["number"] == 71
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("audio-transcode", "audio_transcode", "71"):
        assert resolve(a)["id"] == "audio-transcode"


def test_doc_url():
    assert "welcome-audio/avance/audio-transcode" in resolve("audio-transcode")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/audio-transcode") in routes
    assert ("POST", "/audio-transcode") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "transcode_to_mp3" in text and "FfmpegError" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "AudioTranscodeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "transcode"} <= methods


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Transcoder en MP3"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "audio-transcode" in idx and "Transcoder en MP3" in idx
