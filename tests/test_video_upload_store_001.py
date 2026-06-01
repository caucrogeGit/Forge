"""Tests VIDEO-UPLOAD-STORE-001 : persistance + stockage + ingest.

Aucune base réelle : la persistance est testée via un ``DbAdapter`` factice.
Le stockage écrit dans ``tmp_path``. Aucun ffmpeg/ffprobe lancé.
"""
from __future__ import annotations

import pytest
pytest.importorskip("forge_mvc_video")

from forge_mvc_video.config import load_video_config
from forge_mvc_video.ingest import VideoIngestError, ingest_video
from forge_mvc_video.storage.files import (
    ALLOWED_EXTENSIONS,
    original_relpath,
    safe_extension,
    store_original,
)
from forge_mvc_video.storage.repository import (
    STATUS_UPLOADED,
    VideoRepository,
)


class FakeDb:
    """Adapter DB factice : enregistre les appels, renvoie des valeurs canon."""

    def __init__(self):
        self.calls = []
        self.next_id = 7
        self.rows = {}

    def insert(self, sql, params):
        self.calls.append(("insert", sql, params))
        return self.next_id

    def execute(self, sql, params):
        self.calls.append(("execute", sql, params))

    def fetch_one(self, sql, params):
        self.calls.append(("fetch_one", sql, params))
        return self.rows.get(params[0])

    def fetch_all(self, sql, params):
        self.calls.append(("fetch_all", sql, params))
        return []


# ── Repository ───────────────────────────────────────────────────────────────

def test_insert_uploaded_builds_sql_and_returns_id():
    fake = FakeDb()
    repo = VideoRepository(fake)
    new_id = repo.insert_uploaded(
        uuid="u-123", original_path="originals/2026/06/u-123/source.mp4",
        size_bytes=4242, mime_type="video/mp4",
    )
    assert new_id == 7
    kind, sql, params = fake.calls[-1]
    assert kind == "insert"
    assert "INSERT INTO videos" in sql
    assert params[0] == "u-123"                 # uuid
    assert params[3] == 4242                    # size_bytes
    assert params[5] == STATUS_UPLOADED         # status


def test_update_status_rejects_invalid():
    repo = VideoRepository(FakeDb())
    with pytest.raises(ValueError):
        repo.update_status(1, "bogus")


def test_update_status_executes_update():
    fake = FakeDb()
    VideoRepository(fake).update_status(1, "ready")
    kind, sql, params = fake.calls[-1]
    assert kind == "execute"
    assert "UPDATE videos SET status" in sql
    assert params[0] == "ready" and params[-1] == 1


def test_get_by_uuid_queries():
    fake = FakeDb()
    fake.rows["u-9"] = {"id": 9, "uuid": "u-9"}
    assert VideoRepository(fake).get_by_uuid("u-9") == {"id": 9, "uuid": "u-9"}


# ── Stockage uuid-based ──────────────────────────────────────────────────────

def test_safe_extension():
    assert safe_extension("Ma Vidéo.MP4") == ".mp4"
    assert safe_extension("clip.MOV") == ".mov"
    assert safe_extension("sansext") == ""


def test_original_relpath_is_uuid_based():
    rel = original_relpath("the-uuid", ".mp4")
    assert rel.startswith("originals/")
    assert "the-uuid" in rel
    assert rel.endswith("/source.mp4")


def test_store_original_writes_and_hides_user_filename(tmp_path):
    rel = store_original(b"\x00\x01", "abc-uuid", ".mp4", storage_root=str(tmp_path))
    stored = tmp_path / rel
    assert stored.read_bytes() == b"\x00\x01"
    assert "abc-uuid" in rel
    assert ".mp4" in ALLOWED_EXTENSIONS  # garde-fou liste blanche


# ── Ingest ───────────────────────────────────────────────────────────────────

def test_ingest_valid(tmp_path):
    cfg = load_video_config({"FORGE_VIDEO_STORAGE_ROOT": str(tmp_path)})
    fake = FakeDb()
    result = ingest_video(
        b"\x00\x01\x02\x03", "Ma Vidéo.MP4",
        config=cfg, repository=VideoRepository(fake),
    )
    assert result["status"] == "uploaded"
    assert result["id"] == 7
    assert len(result["uuid"]) == 36
    rel = result["original_path"]
    # Nom utilisateur jamais dans le chemin (uuid-based).
    assert "Ma Vidéo" not in rel and "MP4" not in rel
    assert (tmp_path / rel).read_bytes() == b"\x00\x01\x02\x03"
    assert any(c[0] == "insert" for c in fake.calls)


def test_ingest_rejects_empty(tmp_path):
    cfg = load_video_config({"FORGE_VIDEO_STORAGE_ROOT": str(tmp_path)})
    with pytest.raises(VideoIngestError):
        ingest_video(b"", "clip.mp4", config=cfg, repository=VideoRepository(FakeDb()))


def test_ingest_rejects_bad_extension(tmp_path):
    cfg = load_video_config({"FORGE_VIDEO_STORAGE_ROOT": str(tmp_path)})
    with pytest.raises(VideoIngestError):
        ingest_video(b"x", "malware.exe", config=cfg, repository=VideoRepository(FakeDb()))


def test_ingest_rejects_oversize(tmp_path):
    cfg = load_video_config({
        "FORGE_VIDEO_STORAGE_ROOT": str(tmp_path),
        "FORGE_VIDEO_MAX_UPLOAD_MB": "1",
    })
    too_big = b"\x00" * (1024 * 1024 + 1)  # > 1 Mo
    with pytest.raises(VideoIngestError):
        ingest_video(too_big, "big.mp4", config=cfg, repository=VideoRepository(FakeDb()))
