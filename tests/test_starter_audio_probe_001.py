"""Garde-fou STARTER-AUDIO-PROBE-001 (test proportionné).

Palier 1 avancé welcome-audio — Sonder un audio : slot 64, requires_db false,
route `/audio-probe`, contrôleur `probe_audio` (+ repli pédagogique), vue
présente, doc sous `welcome-audio/avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "audio-probe"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "audio_probe_controller.py"
VIEW = STARTER_DIR / "files" / "mvc" / "views" / "audio_probe" / "index.html"
DOC = ROOT / "docs" / "starters" / "welcome-audio" / "avance" / "audio-probe.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 64"]


def test_resolves():
    m = resolve("audio-probe")
    assert m["id"] == "audio-probe" and m["number"] == 64
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("audio-probe", "audio_probe", "64"):
        assert resolve(a)["id"] == "audio-probe"


def test_doc_url():
    assert "welcome-audio/avance/audio-probe" in resolve("audio-probe")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/audio-probe") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "probe_audio" in text and "AudioProbeError" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "AudioProbeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "index" in methods


def test_view_present():
    assert VIEW.is_file()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Sonder un audio"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "audio-probe" in idx and "Sonder un audio" in idx
