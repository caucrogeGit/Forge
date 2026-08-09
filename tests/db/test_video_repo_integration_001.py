"""Intégration réelle de VideoRepository sur les trois serveurs (audit tests).

Le repository vidéo n'était testé qu'avec un faux connecteur capturant le SQL,
donc ses marqueurs de paramètre n'étaient jamais exercés contre un vrai pilote.
Ces tests exercent le CRUD complet contre des serveurs réels : `insert_uploaded`
et son retour d'id, les lectures, les transitions de statut, `mark_ready`,
`delete`, `all_relpaths`. La table est provisionnée depuis la déclaration
`forge_mvc_video.tables`, rendue par le dialecte.

## Ce qui a changé (`VIDEO-DML-PORTABLE-001`)

Ce fichier ne tournait que sur MariaDB, et c'est ce qui laissait passer un
défaut franc : le repository écrivait ses marqueurs en `%s`, le format natif du
connecteur MariaDB, quand Forge écrit `?`. Le cœur traduit `?` vers le format de
chaque pilote et **double tout `%` littéral** au passage, si bien qu'un `%s`
déjà écrit devenait `%%s` sur PostgreSQL, un texte et non un marqueur. Mesuré
avant correctif, sur les deux moteurs promus au niveau plein par l'ADR-084 :

    PostgreSQL   psycopg.ProgrammingError: the query has 0 placeholders
                 but 8 parameters were passed
    SQL Server   pyodbc.ProgrammingError: The SQL contains 0 parameter markers,
                 but 8 parameters were supplied

Le défaut avait été relevé par le cliquet DML sans être corrigé, et inscrit en
dette listée le temps d'un ticket dédié. C'est ce ticket.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

pytest.importorskip("forge_mvc_video")

from forge_mvc_video.storage.repository import (
    STATUS_PROCESSING,
    STATUS_READY,
    STATUS_UPLOADED,
    VideoRepository,
)

from forge_mvc_testing.real_db import tables_temporaires


@pytest.fixture()
def videos_table(real_backend_db: str) -> Iterator[Any]:
    """Table `videos` créée par sa DDL dialectale, sur le serveur du cas."""
    from forge_mvc_video.tables import VIDEOS

    with tables_temporaires(VIDEOS) as db:
        yield db


def _insert(
    repo: VideoRepository, uuid: str = "11111111-1111-1111-1111-111111111111"
) -> int:
    return repo.insert_uploaded(
        uuid=uuid,
        original_path="uploads/videos/src.mov",
        size_bytes=1024,
        mime_type="video/quicktime",
        title="Démo",
    )


def test_insert_uploaded_returns_id_and_roundtrip(videos_table: Any) -> None:
    repo = VideoRepository()
    vid = _insert(repo)
    assert isinstance(vid, int) and vid > 0, "insert_uploaded doit renvoyer l'id"
    row = repo.get_by_id(vid)
    assert row is not None
    assert row["uuid"] == "11111111-1111-1111-1111-111111111111"
    assert row["status"] == STATUS_UPLOADED
    assert row["size_bytes"] == 1024
    par_uuid = repo.get_by_uuid("11111111-1111-1111-1111-111111111111")
    assert par_uuid is not None and par_uuid["id"] == vid


def test_status_transitions_and_mark_ready(videos_table: Any) -> None:
    repo = VideoRepository()
    vid = _insert(repo)
    repo.update_status(vid, STATUS_PROCESSING)
    en_cours = repo.get_by_id(vid)
    assert en_cours is not None and en_cours["status"] == STATUS_PROCESSING
    repo.mark_ready(
        vid,
        mp4_path="uploads/videos/out.mp4",
        poster_path="uploads/videos/poster.jpg",
    )
    ready = repo.get_by_id(vid)
    assert ready is not None
    assert ready["status"] == STATUS_READY
    assert ready["mp4_path"] == "uploads/videos/out.mp4"
    assert ready["poster_path"] == "uploads/videos/poster.jpg"


def test_update_metadata_traverse_le_moteur(videos_table: Any) -> None:
    """Les métadonnées ffprobe empruntent le même chemin, avec quatre marqueurs."""
    repo = VideoRepository()
    vid = _insert(repo)
    repo.update_metadata(vid, duration_seconds=42, width=1920, height=1080)
    ligne = repo.get_by_id(vid)
    assert ligne is not None
    assert (ligne["duration_seconds"], ligne["width"], ligne["height"]) == (
        42, 1920, 1080,
    )


def test_list_recent_and_by_status(videos_table: Any) -> None:
    """Les deux listes portent la borne du dialecte : `LIMIT` en dur cassait T-SQL."""
    repo = VideoRepository()
    a = _insert(repo, "aaaaaaaa-1111-1111-1111-111111111111")
    b = _insert(repo, "bbbbbbbb-1111-1111-1111-111111111111")
    repo.mark_ready(b, mp4_path="out.mp4", poster_path=None)
    recent = repo.list_recent(limit=10)
    assert {r["id"] for r in recent} == {a, b}
    ready = repo.list_by_status(STATUS_READY, limit=10)
    assert [r["id"] for r in ready] == [b]


def test_la_borne_des_listes_est_reellement_appliquee(videos_table: Any) -> None:
    """Sans quoi la borne pourrait être ignorée en silence par un dialecte."""
    repo = VideoRepository()
    for index in range(5):
        _insert(repo, f"cccccccc-1111-1111-1111-00000000000{index}")
    assert len(repo.list_recent(limit=2)) == 2
    assert len(repo.list_by_status(STATUS_UPLOADED, limit=3)) == 3


def test_delete_and_all_relpaths(videos_table: Any) -> None:
    repo = VideoRepository()
    vid = _insert(repo)
    repo.mark_ready(vid, mp4_path="uploads/videos/out.mp4", poster_path=None)
    paths = repo.all_relpaths()
    assert "uploads/videos/src.mov" in paths
    assert "uploads/videos/out.mp4" in paths
    repo.delete(vid)
    assert repo.get_by_id(vid) is None
