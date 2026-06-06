"""Garde-fou STARTER-AUDIO-WELCOME-001 (test proportionné).

Palier 1 débutant welcome-audio — Bonjour Forge Audio : slot 61, requires_db
false, routes `/audio-welcome` + `/inspect`, contrôleur `load_audio_config`
(token masqué), doc sous `welcome-audio/debutant/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "audio-welcome"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "audio_welcome_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-audio" / "debutant" / "audio-welcome.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 61"]


def test_resolves():
    m = resolve("audio-welcome")
    assert m["id"] == "audio-welcome" and m["number"] == 61
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("audio-welcome", "audio_welcome", "61"):
        assert resolve(a)["id"] == "audio-welcome"


def test_doc_url():
    assert "welcome-audio/debutant/audio-welcome" in resolve("audio-welcome")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/audio-welcome") in routes
    assert ("GET", "/audio-welcome/inspect") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "load_audio_config" in text
    assert '"***"' in text and "api_token" in text
    assert "Response.text(" in text and "Response.json(" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "AudioWelcomeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "inspect"} <= methods


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Bonjour Forge Audio"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "audio-welcome" in idx and "Bonjour Forge Audio" in idx
