"""Garde-fou STARTER-VIDEO-LIST-001 (test proportionné).

Contrat du palier 2 du niveau débutant de welcome-video — Lister les vidéos :

- starter.json : `video-list`, slot 41, requires_db **false** ;
- snippet : GET `/video-list` ;
- contrôleur : `VideoRepository.list_recent`, réponse `503` pédagogique si la
  table manque, `Response.json` ; pas d'écriture ;
- documentation sous `welcome-video/debutant/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "video-list"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "video_list_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-video" / "debutant" / "video-list.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 41"]


def test_resolves():
    m = resolve("video-list")
    assert m["id"] == "video-list" and m["number"] == 41
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("video-list", "video_list", "41"):
        assert resolve(a)["id"] == "video-list"


def test_doc_url_pointe_welcome_video():
    assert "welcome-video/debutant/video-list" in resolve("video-list")["doc_url"]


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = routes_from_snippet(snip)
    assert any(m == "GET" and p == "/video-list" for m, p, *_ in routes)


def test_controller_list_recent_and_pedagogical_state():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_video.storage.repository import VideoRepository" in text
    assert "list_recent(" in text
    assert "status=503" in text
    assert "video_storage_not_ready" in text
    assert "Response.json(" in text
    assert "INSERT" not in text and "insert(" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "VideoListController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "index" in methods


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Lister les vidéos"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "video-list" in idx and "Lister les vidéos" in idx
