"""Tests VIDEO-CLI-001 : commande `forge video:process`.

Aucun ffmpeg ni base réelle : repository factice + fonction de traitement
injectée. On teste le parsing, le routage <id>/--pending, les codes retour.
"""
from __future__ import annotations

from forge_mvc_video.cli.process import run_process
from forge_mvc_video.process import VideoProcessError
from forge_mvc_video.storage.repository import VideoRepository


class FakeRepo:
    def __init__(self, pending_rows=None):
        self.pending = pending_rows or []
        self.list_calls = []

    def list_by_status(self, status, limit=100):
        self.list_calls.append((status, limit))
        return self.pending


def _ready(vid, **kwargs):
    return {"status": "ready", "mp4_path": f"mp4/{vid}.mp4"}


def _failed(vid, **kwargs):
    return {"status": "failed", "error": "transcode KO"}


# ── <id> ─────────────────────────────────────────────────────────────────────

def test_process_id_ready():
    assert run_process(["5"], repository=FakeRepo(), process_fn=_ready) == 0


def test_process_id_failed_returns_1():
    assert run_process(["5"], repository=FakeRepo(), process_fn=_failed) == 1


def test_process_not_found_returns_1():
    def proc(vid, **kwargs):
        raise VideoProcessError("introuvable")

    assert run_process(["9"], repository=FakeRepo(), process_fn=proc) == 1


# ── --pending ────────────────────────────────────────────────────────────────

def test_process_pending_drains_uploaded():
    repo = FakeRepo(pending_rows=[{"id": 1}, {"id": 2}])
    seen = []

    def proc(vid, **kwargs):
        seen.append(vid)
        return {"status": "ready", "mp4_path": "m"}

    rc = run_process(["--pending"], repository=repo, process_fn=proc)
    assert rc == 0
    assert seen == [1, 2]
    assert repo.list_calls == [("uploaded", 100)]


def test_process_pending_partial_failure_returns_1():
    repo = FakeRepo(pending_rows=[{"id": 1}, {"id": 2}])

    def proc(vid, **kwargs):
        return _ready(vid) if vid == 1 else _failed(vid)

    assert run_process(["--pending"], repository=repo, process_fn=proc) == 1


def test_process_pending_empty():
    assert run_process(["--pending"], repository=FakeRepo([]), process_fn=_ready) == 0


# ── Usage ────────────────────────────────────────────────────────────────────

def test_process_no_args_returns_2():
    assert run_process([], repository=FakeRepo()) == 2


def test_process_invalid_id_returns_2():
    assert run_process(["abc"], repository=FakeRepo()) == 2


# ── repository.list_by_status ────────────────────────────────────────────────

class _FakeDb:
    def __init__(self):
        self.fetch_calls = []

    def fetch_all(self, sql, params):
        self.fetch_calls.append((sql, params))
        return []

    def execute(self, sql, params):  # pragma: no cover
        pass

    def insert(self, sql, params):  # pragma: no cover
        return 1

    def fetch_one(self, sql, params):  # pragma: no cover
        return None


def test_list_by_status_sql():
    fake = _FakeDb()
    VideoRepository(fake).list_by_status("uploaded")
    sql, params = fake.fetch_calls[-1]
    assert "WHERE status = %s" in sql
    assert params[0] == "uploaded"
