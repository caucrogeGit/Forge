"""Garde-fou STARTER-VIDEO-WELCOME-001 (test proportionné).

Contrat du palier 1 du niveau débutant de la progression welcome-video —
Bonjour Forge Vidéo :

- starter.json : `video-welcome`, slot 34, requires_db **false** ;
- snippet : GET `/video-welcome`, GET `/video-welcome/inspect` ;
- contrôleur : `load_video_config`, token **masqué**, `Response.text` +
  `Response.json` ; pas de base de données ;
- documentation sous `welcome-video/debutant/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "video-welcome"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "video_welcome_controller.py"
DOC = ROOT / "docs" / "starters" / "welcome-video" / "debutant" / "video-welcome.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 34"]


def test_resolves():
    m = resolve("video-welcome")
    assert m["id"] == "video-welcome" and m["number"] == 34
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("video-welcome", "video_welcome", "34"):
        assert resolve(a)["id"] == "video-welcome"


def test_doc_url_pointe_welcome_video():
    assert "welcome-video/debutant/video-welcome" in resolve("video-welcome")["doc_url"]


def test_snippet_routes():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = {(m, p) for m, p, *_ in routes_from_snippet(snip)}
    assert ("GET", "/video-welcome") in routes
    assert ("GET", "/video-welcome/inspect") in routes


def test_controller_config_masked_no_db():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_video.config import load_video_config" in text
    assert "load_video_config()" in text
    # token masqué — jamais exposé en clair
    assert '"***"' in text and "api_token" in text
    assert "Response.text(" in text and "Response.json(" in text
    assert "core.database" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "VideoWelcomeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert {"index", "inspect"} <= methods


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Bonjour Forge Vidéo"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "video-welcome" in idx and "Bonjour Forge Vidéo" in idx
