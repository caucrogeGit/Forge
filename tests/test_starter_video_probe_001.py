"""Garde-fou STARTER-VIDEO-PROBE-001 (test proportionné).

Contrat du palier 1 du niveau avancé de welcome-video — Sonder une vidéo :

- starter.json : `video-probe`, slot 46, requires_db **true** ;
- snippet : GET `/video-probe/{uuid}` ;
- contrôleur : `get_by_uuid` → chemin → `probe_video` (ffprobe), gestion
  `VideoProbeError` (`502`), `404` si inconnue ; lecture seule ;
- migration `videos` ; documentation sous `avance/`, catalogue.
"""
from __future__ import annotations

import ast
from pathlib import Path

from forge_cli.starters.registry import resolve
from forge_cli.starters.route_ops import routes_from_snippet


ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "video-probe"
FILES = STARTER_DIR / "files"
CONTROLLER = FILES / "mvc" / "controllers" / "video_probe_controller.py"
MIGRATIONS = FILES / "mvc" / "migrations"
DOC = ROOT / "docs" / "starters" / "welcome-video" / "avance" / "video-probe.md"
INDEX = ROOT / "docs" / "starters" / "index.md"

FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 46"]


def test_resolves():
    m = resolve("video-probe")
    assert m["id"] == "video-probe" and m["number"] == 46
    assert m.get("requires_db") is True


def test_aliases():
    for a in ("video-probe", "video_probe", "46"):
        assert resolve(a)["id"] == "video-probe"


def test_doc_url_pointe_welcome_video():
    assert "welcome-video/avance/video-probe" in resolve("video-probe")["doc_url"]


def test_snippet_route():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    routes = routes_from_snippet(snip)
    assert any(m == "GET" and p == "/video-probe/{uuid}" for m, p, *_ in routes)


def test_controller_probe_flow():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "from forge_mvc_video.probe import VideoProbeError, probe_video" in text
    assert "get_by_uuid(" in text
    assert "probe_video(" in text
    assert "status=404" in text
    assert "status=502" in text
    # lecture seule : ffprobe lit, ne transcode pas, on n'écrit rien
    assert "process_video" not in text and "transcode" not in text
    tree = ast.parse(text)
    ctrl = next((c for c in tree.body if isinstance(c, ast.ClassDef)
                 and c.name == "VideoProbeController"), None)
    assert ctrl is not None and "BaseController" in [ast.unparse(b) for b in ctrl.bases]
    methods = {n.name for n in ctrl.body if isinstance(n, ast.FunctionDef)}
    assert "index" in methods


def test_migration_creates_videos():
    sqls = list(MIGRATIONS.glob("*.sql"))
    assert sqls
    content = "\n".join(p.read_text(encoding="utf-8") for p in sqls)
    assert "CREATE TABLE IF NOT EXISTS videos" in content


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Sonder une vidéo"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "video-probe" in idx and "Sonder une vidéo" in idx
