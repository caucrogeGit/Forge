"""Garde-fou STARTER-VIDEO-PLAYBACK-001 (test proportionné).

Contrat du palier 2 du niveau intermédiaire de welcome-video — Lire une vidéo :

- starter.json : `video-playback`, slot 44, requires_db **true** ;
- snippet : branche `register_video_routes(router)` (délégation au paquet) ;
- migration `videos` ; pas de contrôleur applicatif ;
- documentation sous `intermediaire/`, catalogue.
"""
from __future__ import annotations

from pathlib import Path

from forge_cli.starters.registry import resolve


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "video-playback"
FILES = STARTER_DIR / "files"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-video" / "intermediaire" / "video-playback.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 44"]


def test_resolves():
    m = resolve("video-playback")
    assert m["id"] == "video-playback" and m["number"] == 44
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("video-playback", "video_playback", "44"):
        assert resolve(a)["id"] == "video-playback"


def test_doc_url_pointe_welcome_video():
    assert "welcome-video/intermediaire/video-playback" in resolve("video-playback")["doc_url"]


def test_snippet_delegates_to_package():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    assert "# forge-starter:video-playback:start" in snip
    assert "# forge-starter:video-playback:end" in snip
    assert "from forge_mvc_video import register_video_routes" in snip
    assert "register_video_routes(router)" in snip


def test_no_controller_pure_delegation():
    controllers = FILES / "mvc" / "controllers"
    assert not controllers.exists() or not list(controllers.glob("*.py"))


def test_migration_creates_videos():
    sqls = list(MIGRATIONS.glob("*.sql"))
    assert sqls
    content = "\n".join(p.read_text(encoding="utf-8") for p in sqls)
    assert "CREATE TABLE IF NOT EXISTS videos" in content


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Lire une vidéo"
    text = DOC.read_text(encoding="utf-8")
    assert "register_video_routes" in text
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "video-playback" in idx and "Lire une vidéo" in idx
