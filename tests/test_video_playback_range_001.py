"""Tests VIDEO-PLAYBACK-RANGE-001 : route de lecture vidéo (Response.file/Range).

Aucune base réelle (repository factice) ; le fichier est écrit dans tmp_path.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_video")

from forge_mvc_video.config import VideoConfig, load_video_config
from forge_mvc_video.http import (
    ROUTE_PLAYBACK,
    VideoHttpController,
    register_video_routes,
)


class FakeRequest:
    def __init__(self, params=None, headers=None):
        self._params = params or {}
        self._headers = headers or {}

    def route(self, name):
        return self._params.get(name)

    def header(self, name, default=None):
        return self._headers.get(name, default)


class FakeRepo:
    def __init__(self, row):
        self.row = row
        self.raise_exc = False

    def get_by_uuid(self, uuid):
        if self.raise_exc:
            raise RuntimeError("db down")
        return self.row


class FakeRouter:
    def __init__(self):
        self.routes = []

    def add(self, method, pattern, handler, *, name=None, public=None, csrf=None, api=None):
        self.routes.append({
            "method": method, "pattern": pattern, "handler": handler,
            "name": name, "public": public, "csrf": csrf, "api": api,
        })
        return self


def _ctrl(row, tmp_path, *, api_token=None):
    cfg = VideoConfig(storage_root=str(tmp_path), api_token=api_token)
    return VideoHttpController(FakeRepo(row), cfg, api_token=api_token)


def _store(tmp_path, rel, data=b"VIDEODATA"):
    f = tmp_path / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(data)
    return rel


# ── Enregistrement de route ──────────────────────────────────────────────────

def test_register_adds_playback_route(tmp_path):
    router = FakeRouter()
    register_video_routes(
        router, repository=FakeRepo(None),
        config=VideoConfig(storage_root=str(tmp_path)),
    )
    # Le test exigeait auparavant `len(router.routes) == 1`, ce qui figeait un
    # compte et non la fin qu'il annonce : que la route de lecture soit posée
    # avec les bons attributs. Le paquet en enregistre trois depuis
    # VIDEO-STATUS-UI-001 et VIDEO-SUBTITLES-001.
    lecture = [r for r in router.routes if r["pattern"] == ROUTE_PLAYBACK]
    assert len(lecture) == 1, "la route de lecture doit être posée une fois"
    r = lecture[0]
    assert r["method"] == "GET"
    assert r["pattern"] == ROUTE_PLAYBACK == "/videos/{uuid}"
    assert r["public"] is True and r["csrf"] is False and r["api"] is False


# ── stream() ─────────────────────────────────────────────────────────────────

def test_stream_not_found(tmp_path):
    resp = _ctrl(None, tmp_path).stream(FakeRequest(params={"uuid": "u1"}))
    assert resp.status == 404


def test_stream_no_path_conflict(tmp_path):
    row = {"uuid": "u1", "mp4_path": None, "original_path": None}
    resp = _ctrl(row, tmp_path).stream(FakeRequest(params={"uuid": "u1"}))
    assert resp.status == 409


def test_stream_file_missing(tmp_path):
    row = {"uuid": "u1", "mp4_path": None, "original_path": "originals/x/source.mp4"}
    resp = _ctrl(row, tmp_path).stream(FakeRequest(params={"uuid": "u1"}))
    assert resp.status == 404


def test_stream_db_error(tmp_path):
    ctrl = _ctrl({"uuid": "u1"}, tmp_path)
    ctrl._repo.raise_exc = True
    resp = ctrl.stream(FakeRequest(params={"uuid": "u1"}))
    assert resp.status == 500


def test_stream_serves_full_file(tmp_path):
    rel = _store(tmp_path, "originals/2026/06/u1/source.mp4")
    row = {"uuid": "u1", "mp4_path": None, "original_path": rel}
    resp = _ctrl(row, tmp_path).stream(FakeRequest(params={"uuid": "u1"}))
    assert resp.status == 200
    assert resp.content_length == len(b"VIDEODATA")
    assert b"".join(resp.stream) == b"VIDEODATA"


def test_stream_serves_range(tmp_path):
    rel = _store(tmp_path, "originals/2026/06/u1/source.mp4")
    row = {"uuid": "u1", "mp4_path": None, "original_path": rel}
    req = FakeRequest(params={"uuid": "u1"}, headers={"Range": "bytes=0-3"})
    resp = _ctrl(row, tmp_path).stream(req)
    assert resp.status == 206
    assert b"".join(resp.stream) == b"VIDE"


def test_stream_prefers_mp4_when_ready(tmp_path):
    _store(tmp_path, "mp4/u1/video.mp4", b"MP4")
    _store(tmp_path, "originals/u1/source.mov", b"ORIGINAL")
    row = {"uuid": "u1", "mp4_path": "mp4/u1/video.mp4",
           "original_path": "originals/u1/source.mov"}
    resp = _ctrl(row, tmp_path).stream(FakeRequest(params={"uuid": "u1"}))
    assert b"".join(resp.stream) == b"MP4"


# ── Auth optionnelle par Bearer ──────────────────────────────────────────────

def test_stream_unauthorized_without_token(tmp_path):
    rel = _store(tmp_path, "originals/u1/source.mp4")
    row = {"uuid": "u1", "mp4_path": None, "original_path": rel}
    resp = _ctrl(row, tmp_path, api_token="secret").stream(
        FakeRequest(params={"uuid": "u1"})
    )
    assert resp.status == 401


def test_stream_authorized_with_token(tmp_path):
    rel = _store(tmp_path, "originals/u1/source.mp4")
    row = {"uuid": "u1", "mp4_path": None, "original_path": rel}
    req = FakeRequest(params={"uuid": "u1"}, headers={"Authorization": "Bearer secret"})
    resp = _ctrl(row, tmp_path, api_token="secret").stream(req)
    assert resp.status == 200


def test_stream_open_when_no_token(tmp_path):
    rel = _store(tmp_path, "originals/u1/source.mp4")
    row = {"uuid": "u1", "mp4_path": None, "original_path": rel}
    resp = _ctrl(row, tmp_path, api_token=None).stream(
        FakeRequest(params={"uuid": "u1"})
    )
    assert resp.status == 200


# ── Config ───────────────────────────────────────────────────────────────────

def test_config_api_token_optional():
    assert load_video_config({}).api_token is None
    assert load_video_config({"FORGE_VIDEO_API_TOKEN": "abc"}).api_token == "abc"


# ── Confinement du chemin issu de la base (défense en profondeur, audit) ──────

def test_stream_rejects_path_escaping_storage_root(tmp_path):
    """Une ligne DB corrompue avec `../` ne doit pas servir un fichier hors storage."""
    secret = tmp_path.parent / "secret_outside.mp4"
    secret.write_bytes(b"SECRET")
    row = {"uuid": "u1", "mp4_path": None, "original_path": f"../{secret.name}"}
    resp = _ctrl(row, tmp_path).stream(FakeRequest(params={"uuid": "u1"}))
    assert resp.status == 404, "chemin sortant de storage_root refusé"


def test_stream_rejects_absolute_path(tmp_path):
    """Un chemin absolu en base ne doit pas être servi tel quel."""
    secret = tmp_path.parent / "abs_secret.mp4"
    secret.write_bytes(b"SECRET")
    row = {"uuid": "u1", "mp4_path": None, "original_path": str(secret)}
    resp = _ctrl(row, tmp_path).stream(FakeRequest(params={"uuid": "u1"}))
    assert resp.status == 404
