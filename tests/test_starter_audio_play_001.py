"""Garde-fou STARTER-AUDIO-PLAY-001 (test proportionné).

Palier 3 débutant welcome-audio — Lire un audio : slot 63, requires_db false,
snippet branchant `register_audio_routes(router)` (délégation au paquet, pas de
contrôleur applicatif), doc sous `welcome-audio/debutant/`, catalogue.
"""
from __future__ import annotations

from pathlib import Path

from forge_cli.starters.registry import resolve

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "forge_cli" / "starters" / "data" / "audio-play"
DOC = ROOT / "docs" / "starters" / "welcome-audio" / "debutant" / "audio-play.md"
INDEX = ROOT / "docs" / "starters" / "index.md"
FORBIDDEN = ["forge starter:build", "forge new mon-projet", "cd mon-projet", "Starter 63"]


def test_resolves():
    m = resolve("audio-play")
    assert m["id"] == "audio-play" and m["number"] == 63
    assert m.get("requires_db") is False


def test_aliases():
    for a in ("audio-play", "audio_play", "63"):
        assert resolve(a)["id"] == "audio-play"


def test_doc_url():
    assert "welcome-audio/debutant/audio-play" in resolve("audio-play")["doc_url"]


def test_snippet_delegates_to_package():
    snip = (STARTER_DIR / "routes.py.snippet").read_text(encoding="utf-8")
    assert "# forge-starter:audio-play:start" in snip
    assert "# forge-starter:audio-play:end" in snip
    assert "register_audio_routes(router)" in snip


def test_no_applicative_controller():
    assert not (STARTER_DIR / "files").exists()


def test_doc_and_catalogue():
    assert DOC.read_text(encoding="utf-8").splitlines()[0] == "# Lire un audio"
    text = DOC.read_text(encoding="utf-8")
    for bad in FORBIDDEN:
        assert bad not in text
    idx = INDEX.read_text(encoding="utf-8")
    assert "audio-play" in idx and "Lire un audio" in idx
