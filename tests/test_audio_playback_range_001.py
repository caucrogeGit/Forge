"""Tests AUDIO-PLAYBACK-RANGE-001 : route de lecture audio (Response.file/Range).

Sans état (lookup disque par uuid) ; les fichiers sont écrits dans tmp_path.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_audio")

from forge_mvc_audio.config import AudioConfig, load_audio_config
from forge_mvc_audio.http import (
    ROUTE_PLAYBACK,
    AudioHttpController,
    register_audio_routes,
)

_UUID = "11111111-1111-4111-8111-111111111111"


class FakeRequest:
    def __init__(self, params=None, headers=None):
        self._params = params or {}
        self._headers = headers or {}

    def route_param(self, name):
        return self._params.get(name)

    def header(self, name, default=None):
        return self._headers.get(name, default)


class FakeRouter:
    def __init__(self):
        self.routes = []

    def add(self, method, pattern, handler, *, name=None, public=None, csrf=None, api=None):
        self.routes.append({
            "method": method, "pattern": pattern, "handler": handler,
            "name": name, "public": public, "csrf": csrf, "api": api,
        })
        return self


def _ctrl(tmp_path, *, api_token=None):
    cfg = AudioConfig(storage_root=str(tmp_path), api_token=api_token)
    return AudioHttpController(cfg, api_token=api_token)


def _store(tmp_path, rel, data=b"AUDIODATA"):
    f = tmp_path / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(data)
    return rel


# ── Enregistrement de route ──────────────────────────────────────────────────

def test_register_adds_playback_route(tmp_path):
    router = FakeRouter()
    register_audio_routes(router, config=AudioConfig(storage_root=str(tmp_path)))
    assert len(router.routes) == 1
    r = router.routes[0]
    assert r["method"] == "GET"
    assert r["pattern"] == ROUTE_PLAYBACK == "/audio/{uuid}"
    assert r["public"] is True and r["csrf"] is False and r["api"] is False


# ── stream() ─────────────────────────────────────────────────────────────────

def test_stream_not_found(tmp_path):
    resp = _ctrl(tmp_path).stream(FakeRequest(params={"uuid": _UUID}))
    assert resp.status == 404


def test_stream_rejects_bad_uuid(tmp_path):
    # uuid non canonique → pas de lookup, 404 (anti-traversal).
    resp = _ctrl(tmp_path).stream(FakeRequest(params={"uuid": "../secret"}))
    assert resp.status == 404


def test_stream_serves_full_file(tmp_path):
    _store(tmp_path, f"originals/{_UUID}/source.mp3")
    resp = _ctrl(tmp_path).stream(FakeRequest(params={"uuid": _UUID}))
    assert resp.status == 200
    assert resp.content_length == len(b"AUDIODATA")
    assert b"".join(resp.stream) == b"AUDIODATA"


def test_stream_serves_range(tmp_path):
    _store(tmp_path, f"originals/{_UUID}/source.mp3")
    req = FakeRequest(params={"uuid": _UUID}, headers={"Range": "bytes=0-3"})
    resp = _ctrl(tmp_path).stream(req)
    assert resp.status == 206
    assert b"".join(resp.stream) == b"AUDI"


def test_stream_prefers_transcoded(tmp_path):
    _store(tmp_path, f"transcoded/{_UUID}/audio.mp3", b"MP3")
    _store(tmp_path, f"originals/{_UUID}/source.wav", b"ORIGINAL")
    resp = _ctrl(tmp_path).stream(FakeRequest(params={"uuid": _UUID}))
    assert b"".join(resp.stream) == b"MP3"


# ── Auth optionnelle par Bearer ──────────────────────────────────────────────

def test_stream_unauthorized_without_token(tmp_path):
    _store(tmp_path, f"originals/{_UUID}/source.mp3")
    resp = _ctrl(tmp_path, api_token="secret").stream(
        FakeRequest(params={"uuid": _UUID})
    )
    assert resp.status == 401


def test_stream_authorized_with_token(tmp_path):
    _store(tmp_path, f"originals/{_UUID}/source.mp3")
    req = FakeRequest(params={"uuid": _UUID}, headers={"Authorization": "Bearer secret"})
    resp = _ctrl(tmp_path, api_token="secret").stream(req)
    assert resp.status == 200


def test_stream_open_when_no_token(tmp_path):
    _store(tmp_path, f"originals/{_UUID}/source.mp3")
    resp = _ctrl(tmp_path, api_token=None).stream(FakeRequest(params={"uuid": _UUID}))
    assert resp.status == 200


# ── Config ───────────────────────────────────────────────────────────────────

def test_config_api_token_optional():
    assert load_audio_config({}).api_token is None
    assert load_audio_config({"FORGE_AUDIO_API_TOKEN": "abc"}).api_token == "abc"
