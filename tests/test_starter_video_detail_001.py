"""Garde-fou STARTER-VIDEO-DETAIL-001 (test proportionné).

Contrat du palier 3 du niveau débutant de welcome-video — Le détail d'une vidéo :

- starter.json : `video-detail`, slot 42, requires_db **false** ;
- snippet : GET `/video-detail/{uuid}` ;
- contrôleur : `route_param`, `get_by_uuid`, `404` si inconnue, `503` si table
  absente ; lecture seule ;
- documentation sous `welcome-video/debutant/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "video-detail"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "video_detail_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-video" / "debutant" / "video-detail.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 42"]


def test_resolves():
    m = resolve("video-detail")
    assert m["id"] == "video-detail" and m["number"] == 42
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("video-detail", "video_detail", "42"):
        assert resolve(a)["id"] == "video-detail"


def test_doc_url_pointe_welcome_video():
    assert "welcome-video/debutant/video-detail" in resolve("video-detail")["doc_url"]


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = routes_from_snippet(snip)
    assert any(m == "GET" and p == "/video-detail/{uuid}" for m, p, *_ in routes)


def test_controller_get_by_uuid_states():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_video.storage.repository import VideoRepository" in text
    assert 'request.route_param("uuid")' in text
    assert "get_by_uuid(" in text
    assert "status=404" in text
    assert "status=503" in text
    assert "INSERT" not in text and "insert(" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "VideoDetailController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "index" in methods


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Le détail d'une vidéo"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "video-detail" in idx and "Le détail d'une vidéo" in idx
