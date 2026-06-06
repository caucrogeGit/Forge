"""Garde-fou STARTER-VIDEO-DOCTOR-001 (test proportionné).

Contrat du dernier palier du niveau avancé de welcome-video — Diagnostiquer :

- starter.json : `video-doctor`, slot 42, requires_db **false** ;
- snippet : GET `/video-doctor` ;
- contrôleur : appelle les contrôles non invasifs de `cli.doctor` (dont
  présence ffprobe/ffmpeg), expose le statut en JSON ; ne touche pas la base ;
- documentation sous `avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "video-doctor"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "video_doctor_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-video" / "avance" / "video-doctor.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 42"]


def test_resolves():
    m = resolve("video-doctor")
    assert m["id"] == "video-doctor" and m["number"] == 42
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("video-doctor", "video_doctor", "42"):
        assert resolve(a)["id"] == "video-doctor"


def test_doc_url_pointe_welcome_video():
    assert "welcome-video/avance/video-doctor" in resolve("video-doctor")["doc_url"]


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = routes_from_snippet(snip)
    assert any(m == "GET" and p == "/video-doctor" for m, p, *_ in routes)


def test_controller_runs_safe_checks():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_video.cli.doctor import" in text
    assert "check_package_importable" in text
    assert "check_config_loadable" in text
    assert "check_migration_present" in text
    assert "check_ffprobe_present" in text
    assert "check_ffmpeg_present" in text
    assert "Response.json(" in text
    # contrôle invasif (table en base) volontairement exclu
    assert "check_database_table" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "VideoDoctorController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "index" in methods


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Diagnostiquer le module Vidéo"
    text = DOC.read_text(encoding="utf-8")
    assert "forge video:doctor" in text
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "video-doctor" in idx and "Diagnostiquer le module Vidéo" in idx
