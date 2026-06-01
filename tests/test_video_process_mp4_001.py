"""Tests VIDEO-PROCESS-MP4-001 : orchestration du traitement vidéo.

Aucun ffmpeg/ffprobe réel (briques injectées), aucune base réelle (repo
factice). Le stockage écrit dans tmp_path.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from forge_mvc_video.config import VideoConfig
from forge_mvc_video.probe import VideoMetadata, VideoProbeError
from forge_mvc_video.process import VideoProcessError, process_video
from forge_mvc_video.storage.repository import VideoRepository
from forge_mvc_video.transcode import FfmpegError

NOW = datetime(2026, 6, 1, 12, 0, 0)
META = VideoMetadata(
    duration_seconds=12, width=1920, height=1080,
    video_codec="h264", audio_codec="aac", container="mp4",
)


class FakeRepo:
    def __init__(self, row):
        self.row = row
        self.calls = []

    def get_by_id(self, vid):
        self.calls.append(("get_by_id", vid))
        return self.row

    def update_status(self, vid, status, *, error_message=None, now=None):
        self.calls.append(("update_status", vid, status, error_message))

    def update_metadata(self, vid, *, duration_seconds, width, height, now=None):
        self.calls.append(("update_metadata", vid, duration_seconds, width, height))

    def mark_ready(self, vid, *, mp4_path, poster_path, now=None):
        self.calls.append(("mark_ready", vid, mp4_path, poster_path))


def _project(tmp_path):
    src = tmp_path / "originals/u1/source.mov"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"SRC")
    row = {"id": 5, "uuid": "u1", "original_path": "originals/u1/source.mov"}
    return VideoConfig(storage_root=str(tmp_path)), FakeRepo(row)


# ── Succès ───────────────────────────────────────────────────────────────────

def test_process_success(tmp_path):
    cfg, repo = _project(tmp_path)
    result = process_video(
        5, config=cfg, repository=repo, now=NOW,
        probe_fn=lambda p: META,
        poster_fn=lambda src, dst: Path(dst).write_bytes(b"JPG"),
        transcode_fn=lambda src, dst: Path(dst).write_bytes(b"MP4"),
    )
    assert result["status"] == "ready"
    assert result["mp4_path"] == "mp4/2026/06/u1/video.mp4"
    assert result["poster_path"] == "posters/2026/06/u1/poster.jpg"
    # séquence : processing → metadata → ready
    kinds = [c[0] for c in repo.calls]
    assert kinds == ["get_by_id", "update_status", "update_metadata", "mark_ready"]
    assert repo.calls[1] == ("update_status", 5, "processing", None)
    assert repo.calls[2] == ("update_metadata", 5, 12, 1920, 1080)
    assert repo.calls[3] == ("mark_ready", 5, result["mp4_path"], result["poster_path"])
    # fichiers de sortie écrits
    assert (tmp_path / result["mp4_path"]).read_bytes() == b"MP4"
    assert (tmp_path / result["poster_path"]).read_bytes() == b"JPG"


# ── Échecs ───────────────────────────────────────────────────────────────────

def test_process_probe_failure(tmp_path):
    cfg, repo = _project(tmp_path)

    def bad_probe(p):
        raise VideoProbeError("pas une vidéo")

    result = process_video(
        5, config=cfg, repository=repo, now=NOW,
        probe_fn=bad_probe,
        poster_fn=lambda s, d: None, transcode_fn=lambda s, d: None,
    )
    assert result["status"] == "failed"
    assert ("update_status", 5, "failed", "pas une vidéo") in repo.calls
    # metadata jamais écrite si le probe échoue
    assert not any(c[0] == "update_metadata" for c in repo.calls)


def test_process_transcode_failure_nettoie(tmp_path):
    cfg, repo = _project(tmp_path)

    def boom(src, dst):
        raise FfmpegError("transcode KO")

    result = process_video(
        5, config=cfg, repository=repo, now=NOW,
        probe_fn=lambda p: META,
        poster_fn=lambda src, dst: Path(dst).write_bytes(b"JPG"),
        transcode_fn=boom,
    )
    assert result["status"] == "failed"
    assert ("update_status", 5, "failed", "transcode KO") in repo.calls
    # le poster partiel est nettoyé
    assert not (tmp_path / "posters/2026/06/u1/poster.jpg").exists()


def test_process_introuvable_leve(tmp_path):
    with pytest.raises(VideoProcessError):
        process_video(
            99, config=VideoConfig(storage_root=str(tmp_path)), repository=FakeRepo(None)
        )


def test_process_sans_source_leve(tmp_path):
    repo = FakeRepo({"id": 5, "uuid": "u1", "original_path": None})
    with pytest.raises(VideoProcessError):
        process_video(5, config=VideoConfig(storage_root=str(tmp_path)), repository=repo)


# ── repository.mark_ready ────────────────────────────────────────────────────

class _FakeDb:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))

    def insert(self, sql, params):  # pragma: no cover
        return 1

    def fetch_one(self, sql, params):  # pragma: no cover
        return None

    def fetch_all(self, sql, params):  # pragma: no cover
        return []


def test_repo_mark_ready_sql():
    fake = _FakeDb()
    VideoRepository(fake).mark_ready(5, mp4_path="m.mp4", poster_path="p.jpg")
    sql, params = fake.calls[-1]
    assert "mp4_path" in sql and "poster_path" in sql
    assert params[0] == "ready"
    assert params[1] == "m.mp4" and params[2] == "p.jpg"
    assert params[-1] == 5
