"""Tests VIDEO-PROBE-METADATA-001 : extraction ffprobe + update DB.

Aucun ffprobe réel : on injecte un *runner* factice renvoyant une sortie
ffprobe canon. Aucune base réelle pour l'update (adapter factice).
"""
from __future__ import annotations

import json

import pytest

from forge_mvc_video.config import load_video_config
from forge_mvc_video.probe import (
    VideoProbeError,
    parse_probe_json,
    probe_video,
)
from forge_mvc_video.storage.repository import VideoRepository

PROBE_JSON = json.dumps({
    "streams": [
        {"codec_type": "video", "codec_name": "h264",
         "width": 1920, "height": 1080, "duration": "12.5"},
        {"codec_type": "audio", "codec_name": "aac"},
    ],
    "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2", "duration": "12.520000"},
})


# ── Parsing ──────────────────────────────────────────────────────────────────

def test_parse_complet():
    meta = parse_probe_json(PROBE_JSON)
    assert meta.duration_seconds == 12       # tronqué depuis 12.52
    assert meta.width == 1920 and meta.height == 1080
    assert meta.video_codec == "h264"
    assert meta.audio_codec == "aac"
    assert "mp4" in meta.container


def test_parse_sans_audio():
    payload = {
        "streams": [{"codec_type": "video", "codec_name": "vp9",
                     "width": 640, "height": 360}],
        "format": {"format_name": "webm", "duration": "3"},
    }
    meta = parse_probe_json(payload)
    assert meta.audio_codec is None
    assert meta.video_codec == "vp9"
    assert meta.duration_seconds == 3


def test_parse_sans_flux_video_leve():
    payload = {"streams": [{"codec_type": "audio", "codec_name": "mp3"}], "format": {}}
    with pytest.raises(VideoProbeError):
        parse_probe_json(payload)


# ── probe_video (runner injectable) ──────────────────────────────────────────

def test_probe_video_utilise_runner_et_config():
    cfg = load_video_config({"FORGE_VIDEO_FFPROBE_BIN": "myffprobe"})
    calls = []

    def fake(bin_value, path):
        calls.append((bin_value, path))
        return PROBE_JSON

    meta = probe_video("/store/source.mp4", config=cfg, runner=fake)
    assert calls == [("myffprobe", "/store/source.mp4")]
    assert meta.width == 1920


def test_probe_video_rejette_trop_long():
    cfg = load_video_config({"FORGE_VIDEO_MAX_DURATION_SECONDS": "10"})
    too_long = json.dumps({
        "streams": [{"codec_type": "video", "width": 640, "height": 480}],
        "format": {"duration": "60"},
    })
    with pytest.raises(VideoProbeError):
        probe_video("/x", config=cfg, runner=lambda b, p: too_long)


def test_probe_video_propage_erreur_runner():
    def boom(bin_value, path):
        raise VideoProbeError("ffprobe a échoué")

    with pytest.raises(VideoProbeError):
        probe_video("/x", runner=boom)


# ── Repository.update_metadata ───────────────────────────────────────────────

class _FakeDb:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params):
        self.calls.append(("execute", sql, params))

    def insert(self, sql, params):  # pragma: no cover - non utilisé ici
        return 1

    def fetch_one(self, sql, params):  # pragma: no cover
        return None

    def fetch_all(self, sql, params):  # pragma: no cover
        return []


def test_update_metadata_construit_le_sql():
    fake = _FakeDb()
    VideoRepository(fake).update_metadata(
        5, duration_seconds=12, width=1920, height=1080
    )
    kind, sql, params = fake.calls[-1]
    assert kind == "execute"
    assert "UPDATE videos SET duration_seconds" in sql
    assert params[0] == 12 and params[1] == 1920 and params[2] == 1080
    assert params[-1] == 5
