"""Garde-fou STARTER-AUDIO-DOCTOR-001 (test proportionné).

Palier 3 avancé welcome-audio — Diagnostiquer le module Audio : slot 66,
requires_db false, route `/audio-doctor`, contrôleur exposant les `check_*` de
`forge audio:doctor`, doc sous `welcome-audio/avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "audio-doctor"
CONTROLLER = STARTER_DIR / "files" / "mvc" / "controllers" / "audio_doctor_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-audio" / "avance" / "audio-doctor.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 66"]


def test_resolves():
    m = resolve("audio-doctor")
    assert m["id"] == "audio-doctor" and m["number"] == 66
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("audio-doctor", "audio_doctor", "66"):
        assert resolve(a)["id"] == "audio-doctor"


def test_doc_url():
    assert "welcome-audio/avance/audio-doctor" in resolve("audio-doctor")["doc_url"]


def test_snippet_routes():
    routes = {(m, p) for m, p, *_ in routes_from_snippet((STARTER_DIR / "routes.py.snippet").read_text())}
    assert ("GET", "/audio-doctor") in routes


def test_controller():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_audio.cli.doctor import" in text
    assert "check_ffprobe_present" in text and "check_ffmpeg_present" in text
    assert "Response.json(" in text
    assert "core.database" not in text
    ctrl = next((c for c in ast.parse(text).body if isinstance(c, ast.ClassDef) and c.name == "AudioDoctorController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "index" in methods


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Diagnostiquer le module Audio"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "audio-doctor" in idx and "Diagnostiquer le module Audio" in idx
