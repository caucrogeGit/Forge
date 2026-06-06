"""Garde-fou STARTER-VIDEO-UPLOAD-001 (test proportionné).

Contrat du palier 1 du niveau intermédiaire de welcome-video — Téléverser :

- starter.json : `video-upload`, slot 37, requires_db **true** ;
- snippet : GET formulaire, POST upload ;
- contrôleur : `request.file`, `ingest_video`, gestion `VideoIngestError`,
  CSRF, redirection (PRG) ; **aucun ffmpeg** ;
- vue : formulaire `multipart/form-data` + CSRF + champ fichier ;
- migration `videos` ; documentation sous `intermediaire/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "video-upload"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "video_upload_controller.py"
VIEW = FILES / "mvc" / "views" / "video_upload" / "index.html"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-video" / "intermediaire" / "video-upload.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 37"]


def test_resolves():
    m = resolve("video-upload")
    assert m["id"] == "video-upload" and m["number"] == 37
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("video-upload", "video_upload", "37"):
        assert resolve(a)["id"] == "video-upload"


def test_doc_url_pointe_welcome_video():
    assert "welcome-video/intermediaire/video-upload" in resolve("video-upload")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/video-upload") in routes
    assert ("POST", "/video-upload") in routes


def test_controller_ingest_flow_no_ffmpeg():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_video.ingest import VideoIngestError, ingest_video" in text
    assert 'request.file("video")' in text
    assert "ingest_video(" in text
    assert "VideoIngestError" in text
    assert "csrf_token" in text
    assert "redirect(" in text
    # le transcodage (ffmpeg) n'a pas sa place dans une requête HTTP
    assert "process_video" not in text and "transcode" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "VideoUploadController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "upload"} <= methods


def test_view_multipart_form_with_csrf():
    html = VIEW.read_text(encoding="utf-8")
    assert 'method="post"' in html
    assert 'enctype="multipart/form-data"' in html
    assert 'name="csrf_token"' in html
    assert 'type="file"' in html and 'name="video"' in html


def test_migration_creates_videos():
    sqls = list(MIGRATIONS.glob("*.sql"))
    assert sqls
    content = "\n".join(p.read_text(encoding="utf-8") for p in sqls)
    assert "CREATE TABLE IF NOT EXISTS videos" in content


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Téléverser une vidéo"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "video-upload" in idx and "Téléverser une vidéo" in idx
