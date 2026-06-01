"""Garde-fou VIDEO-CLOSING-AUDIT-001 : l'audit de clôture vidéo existe et couvre
les points clés de la phase. Test documentaire (lit du texte).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
AUDIT = PROJECT_ROOT / "docs" / "history" / "audits" / "audit-video-closing.md"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"


def _text() -> str:
    return AUDIT.read_text(encoding="utf-8")


def test_audit_exists():
    assert AUDIT.exists(), "docs/history/audits/audit-video-closing.md doit exister"


def test_verdict_et_decision_de_cloture():
    text = _text().lower()
    assert "verdict" in text
    assert "clôture" in text or "cloture" in text


def test_mentionne_le_package_optin():
    assert "forge-mvc-video" in _text()


@pytest.mark.parametrize("command", [
    "video:doctor", "video:init", "video:process",
])
def test_mentionne_chaque_commande(command):
    assert command in _text()


@pytest.mark.parametrize("needle", [
    "GET /videos/{uuid}",     # route de lecture
    "Range",                  # streaming HTTP Range
    "Response.file",          # primitive core réutilisée
    "+faststart",             # détail clé MP4 seekable
    "videos",                 # table
    "FORGE_VIDEO_API_TOKEN",  # auth optionnelle
    "uuid-based",             # stockage anti-traversal
    "ffmpeg",
    "ffprobe",
])
def test_mentionne_les_points_cles(needle):
    assert needle in _text(), f"l'audit doit mentionner {needle!r}"


def test_limites_et_reports():
    text = _text()
    assert "HLS" in text          # exclusion explicite
    assert "video:cleanup" in text or "VIDEO-CLEANUP" in text  # ticket reporté


def test_reference_dans_la_nav_mkdocs():
    assert "history/audits/audit-video-closing.md" in MKDOCS.read_text(encoding="utf-8")
