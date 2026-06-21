"""Garde-fou MEDIA-FFMPEG-ARG-HARDENING-001 (audio).

Un chemin commençant par ``-`` ne doit jamais être passé tel quel à ffmpeg : il
serait interprété comme une option (le chemin de sortie est positionnel).
"""

from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_audio")

from forge_mvc_audio.transcode import build_transcode_command


def test_chemin_de_sortie_dangereux_est_prefixe() -> None:
    cmd = build_transcode_command("ffmpeg", "in.wav", "-evil.mp3")
    assert "./-evil.mp3" in cmd
    assert "-evil.mp3" not in cmd


def test_chemin_entree_dangereux_est_prefixe() -> None:
    cmd = build_transcode_command("ffmpeg", "-i.wav", "out.mp3")
    assert "./-i.wav" in cmd


def test_chemins_normaux_inchanges() -> None:
    cmd = build_transcode_command("ffmpeg", "originals/abc/source.wav", "out/x.mp3")
    assert "originals/abc/source.wav" in cmd
    assert "out/x.mp3" in cmd
