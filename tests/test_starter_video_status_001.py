"""Garde-fou STARTER-VIDEO-STATUS-001 (test proportionné).

Contrat du palier 3 du niveau intermédiaire de welcome-video — Suivre l'état :

- starter.json : `video-status`, slot 45, requires_db **true** ;
- snippet : GET `/video-status` ;
- contrôleur : `list_by_status` sur le cycle de vie, réponse `503` pédagogique ;
  lecture seule (ne fait pas avancer le statut) ;
- migration `videos` ; documentation sous `intermediaire/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "video-status"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "video_status_controller.py"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-video" / "intermediaire" / "video-status.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 45"]


def test_resolves():
    m = resolve("video-status")
    assert m["id"] == "video-status" and m["number"] == 45
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("video-status", "video_status", "45"):
        assert resolve(a)["id"] == "video-status"


def test_doc_url_pointe_welcome_video():
    assert "welcome-video/intermediaire/video-status" in resolve("video-status")["doc_url"]


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = routes_from_snippet(snip)
    assert any(m == "GET" and p == "/video-status" for m, p, *_ in routes)


def test_controller_list_by_status_readonly():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_video.storage.repository import VideoRepository" in text
    assert "list_by_status(" in text
    assert "uploaded" in text and "processing" in text and "ready" in text and "failed" in text
    assert "status=503" in text
    # lecture seule : on n'écrit pas et on ne fait pas avancer le statut
    assert "update_status" not in text and "mark_ready" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "VideoStatusController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "index" in methods


def test_migration_creates_videos():
    sqls = list(MIGRATIONS.glob("*.sql"))
    assert sqls
    content = "\n".join(p.read_text(encoding="utf-8") for p in sqls)
    assert "CREATE TABLE IF NOT EXISTS videos" in content


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Suivre l'état d'une vidéo"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "video-status" in idx and "Suivre l'état d'une vidéo" in idx
