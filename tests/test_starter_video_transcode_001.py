"""Garde-fou STARTER-VIDEO-TRANSCODE-001 (test proportionné).

Contrat du palier 2 du niveau avancé de welcome-video — Transcoder une vidéo :

- starter.json : `video-transcode`, slot 47, requires_db **true** ;
- snippet : GET `/video-transcode` ;
- contrôleur : liste les vidéos `uploaded` + config ffmpeg ; ne transcode PAS
  dans la requête (worker CLI) ;
- vue : mentionne `forge video:process` ;
- migration `videos` ; documentation sous `avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "video-transcode"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "video_transcode_controller.py"
VIEW = FILES / "mvc" / "views" / "video_transcode" / "index.html"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-video" / "avance" / "video-transcode.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 47"]


def test_resolves():
    m = resolve("video-transcode")
    assert m["id"] == "video-transcode" and m["number"] == 47
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("video-transcode", "video_transcode", "47"):
        assert resolve(a)["id"] == "video-transcode"


def test_doc_url_pointe_welcome_video():
    assert "welcome-video/avance/video-transcode" in resolve("video-transcode")["doc_url"]


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = routes_from_snippet(snip)
    assert any(m == "GET" and p == "/video-transcode" for m, p, *_ in routes)


def test_controller_prepares_not_transcodes():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_video.config import load_video_config" in text
    assert "from forge_mvc_video.storage.repository import VideoRepository" in text
    assert 'list_by_status("uploaded"' in text
    assert "ffmpeg_bin" in text
    # le transcodage lourd reste un worker CLI : pas d'APPEL process_video en HTTP
    assert "process_video(" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "VideoTranscodeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "index" in methods


def test_view_mentions_process_command():
    html = VIEW.read_text(encoding="utf-8")
    assert "forge video:process" in html


def test_migration_creates_videos():
    sqls = list(MIGRATIONS.glob("*.sql"))
    assert sqls
    content = "\n".join(p.read_text(encoding="utf-8") for p in sqls)
    assert "CREATE TABLE IF NOT EXISTS videos" in content


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Transcoder une vidéo"
    text = DOC.read_text(encoding="utf-8")
    assert "forge video:process" in text
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "video-transcode" in idx and "Transcoder une vidéo" in idx
