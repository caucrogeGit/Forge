"""Garde-fou MEDIA-FFMPEG-ARG-HARDENING-001 (video).

Un chemin commençant par ``-`` ne doit jamais être passé tel quel à ffmpeg : il
serait interprété comme une option (le chemin de sortie est positionnel).
"""

from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_video")

from forge_mvc_video.transcode import build_poster_command, build_transcode_command


def test_chemin_de_sortie_dangereux_est_prefixe() -> None:
    cmd = build_transcode_command("ffmpeg", "in.mp4", "-evil.mp4")
    assert "./-evil.mp4" in cmd
    assert "-evil.mp4" not in cmd


def test_chemin_entree_dangereux_est_prefixe() -> None:
    cmd = build_transcode_command("ffmpeg", "-i.mp4", "out.mp4")
    assert "./-i.mp4" in cmd


def test_chemins_normaux_inchanges() -> None:
    cmd = build_transcode_command("ffmpeg", "originals/abc/source.mp4", "out/x.mp4")
    assert "originals/abc/source.mp4" in cmd
    assert "out/x.mp4" in cmd


def test_poster_protege_aussi() -> None:
    cmd = build_poster_command("ffmpeg", "in.mp4", "-poster.jpg")
    assert "./-poster.jpg" in cmd
