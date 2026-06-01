"""Tests VIDEO-FFMPEG-RUNNER-001 : commandes ffmpeg + exécution injectable.

Aucun ffmpeg réel : on teste la commande **construite** (pure) et on injecte
un runner factice. Garde-fous de sécurité : args en liste, faststart présent.
"""
from __future__ import annotations

import pytest

from forge_mvc_video.transcode import (
    DEFAULT_POSTER_TIMEOUT,
    DEFAULT_TRANSCODE_TIMEOUT,
    FfmpegError,
    build_poster_command,
    build_transcode_command,
    generate_poster,
    transcode_to_mp4,
)


def test_transcode_command_profil_standard():
    cmd = build_transcode_command("ffmpeg", "/in/source.mov", "/out/video.mp4")
    assert isinstance(cmd, list) and cmd[0] == "ffmpeg"
    assert cmd[cmd.index("-i") + 1] == "/in/source.mov"
    assert cmd[-1] == "/out/video.mp4"
    # codecs
    assert "libx264" in cmd and "aac" in cmd
    assert cmd[cmd.index("-crf") + 1] == "23"
    assert cmd[cmd.index("-b:a") + 1] == "128k"
    # LE détail clé : faststart (MP4 seekable en streaming progressif)
    assert cmd[cmd.index("-movflags") + 1] == "+faststart"
    # downscale > 1080p (jamais d'upscale) + strip métadonnées
    assert "scale='min(1920,iw)':-2" in cmd
    assert cmd[cmd.index("-map_metadata") + 1] == "-1"


def test_poster_command():
    cmd = build_poster_command("ff", "/in/s.mp4", "/out/poster.jpg", at_seconds=2)
    assert cmd[0] == "ff"
    # -ss avant -i = seek rapide
    assert cmd.index("-ss") < cmd.index("-i")
    assert cmd[cmd.index("-ss") + 1] == "2"
    assert cmd[cmd.index("-frames:v") + 1] == "1"
    assert cmd[-1] == "/out/poster.jpg"


def test_transcode_execute_la_commande_construite():
    seen = {}

    def fake(cmd, timeout):
        seen["cmd"] = cmd
        seen["timeout"] = timeout
        return (0, "")

    transcode_to_mp4("/in.mov", "/out.mp4", ffmpeg_bin="ffmpeg", runner=fake, timeout=99)
    assert seen["cmd"] == build_transcode_command("ffmpeg", "/in.mov", "/out.mp4")
    assert seen["timeout"] == 99


def test_transcode_leve_sur_echec():
    with pytest.raises(FfmpegError):
        transcode_to_mp4("/in", "/out", runner=lambda c, t: (1, "boom"))


def test_poster_execute_et_leve():
    calls = []

    def ok(cmd, timeout):
        calls.append(cmd)
        return (0, "")

    generate_poster("/in", "/out.jpg", runner=ok)
    assert calls and calls[0][0] == "ffmpeg"

    with pytest.raises(FfmpegError):
        generate_poster("/in", "/out.jpg", runner=lambda c, t: (1, "x"))


def test_default_timeouts_bornes():
    assert DEFAULT_TRANSCODE_TIMEOUT > DEFAULT_POSTER_TIMEOUT > 0
