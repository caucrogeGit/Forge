"""Intégration réelle de VideoRepository contre MariaDB (audit tests).

Le repository vidéo n'était testé qu'avec un faux connecteur capturant le SQL
(les placeholders `%s` du repository n'étaient donc jamais exercés contre le vrai
connecteur MariaDB). Ces tests exercent le CRUD complet contre une MariaDB réelle :
insert_uploaded (retour d'id), lectures, transitions de statut, mark_ready, delete,
all_relpaths. La table `videos` est provisionnée depuis le DDL réellement livré.

Marqués `db` : sautés en local sans base, imposés en CI.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.db

forge_mvc_video = pytest.importorskip("forge_mvc_video")

from forge_mvc_video.storage.repository import (
    STATUS_PROCESSING,
    STATUS_READY,
    STATUS_UPLOADED,
    VideoRepository,
)


def _ddl_statements() -> list[str]:
    migrations = Path(forge_mvc_video.__file__).resolve().parent / "migrations"
    sql_file = next(iter(sorted(migrations.glob("*.sql"))))
    raw = sql_file.read_text(encoding="utf-8")
    sql = "\n".join(l for l in raw.splitlines() if not l.strip().startswith("--"))
    return [s.strip() for s in sql.split(";") if s.strip()]


@pytest.fixture()
def videos_table(real_db):
    from core.database import db

    db.execute("DROP TABLE IF EXISTS videos", ())
    for statement in _ddl_statements():
        db.execute(statement, ())
    yield db
    db.execute("DROP TABLE IF EXISTS videos", ())


def _insert(repo: VideoRepository, uuid: str = "11111111-1111-1111-1111-111111111111") -> int:
    return repo.insert_uploaded(
        uuid=uuid,
        original_path="uploads/videos/src.mov",
        size_bytes=1024,
        mime_type="video/quicktime",
        title="Démo",
    )


def test_insert_uploaded_returns_id_and_roundtrip(videos_table):
    repo = VideoRepository()
    vid = _insert(repo)
    assert isinstance(vid, int) and vid > 0, "insert_uploaded doit renvoyer l'id (lastrowid)"
    row = repo.get_by_id(vid)
    assert row is not None
    assert row["uuid"] == "11111111-1111-1111-1111-111111111111"
    assert row["status"] == STATUS_UPLOADED
    assert row["size_bytes"] == 1024
    assert repo.get_by_uuid("11111111-1111-1111-1111-111111111111")["id"] == vid


def test_status_transitions_and_mark_ready(videos_table):
    repo = VideoRepository()
    vid = _insert(repo)
    repo.update_status(vid, STATUS_PROCESSING)
    assert repo.get_by_id(vid)["status"] == STATUS_PROCESSING
    repo.mark_ready(vid, mp4_path="uploads/videos/out.mp4", poster_path="uploads/videos/poster.jpg")
    ready = repo.get_by_id(vid)
    assert ready["status"] == STATUS_READY
    assert ready["mp4_path"] == "uploads/videos/out.mp4"
    assert ready["poster_path"] == "uploads/videos/poster.jpg"


def test_list_recent_and_by_status(videos_table):
    repo = VideoRepository()
    a = _insert(repo, "aaaaaaaa-1111-1111-1111-111111111111")
    b = _insert(repo, "bbbbbbbb-1111-1111-1111-111111111111")
    repo.mark_ready(b, mp4_path="out.mp4", poster_path=None)
    recent = repo.list_recent(limit=10)
    assert {r["id"] for r in recent} == {a, b}
    ready = repo.list_by_status(STATUS_READY, limit=10)
    assert [r["id"] for r in ready] == [b]


def test_delete_and_all_relpaths(videos_table):
    repo = VideoRepository()
    vid = _insert(repo)
    repo.mark_ready(vid, mp4_path="uploads/videos/out.mp4", poster_path=None)
    paths = repo.all_relpaths()
    assert "uploads/videos/src.mov" in paths
    assert "uploads/videos/out.mp4" in paths
    repo.delete(vid)
    assert repo.get_by_id(vid) is None
