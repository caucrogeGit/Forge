"""Tests VIDEO-INIT-001 : commande `forge video:init`.

Copie la migration packagée vers `mvc/migrations/`. N'exécute aucun SQL.
Appelle `init_video_migrations(project_root=tmp)` — aucun fichier réel du
dépôt n'est touché.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_video")

from forge_mvc_video.cli.init import (
    init_video_migrations,
    iter_video_migration_resources,
)


def test_resources_contiennent_la_migration_videos():
    names = [name for name, _ in iter_video_migration_resources()]
    assert any(n.endswith("_create_videos.sql") for n in names)
    assert all(n.endswith(".sql") for n in names)


def _make_project(tmp_path: Path) -> Path:
    (tmp_path / "mvc").mkdir()
    return tmp_path


def test_copie_la_migration(tmp_path):
    root = _make_project(tmp_path)
    rc = init_video_migrations(root)
    assert rc == 0
    copied = list((root / "mvc" / "migrations").glob("*_create_videos.sql"))
    assert len(copied) == 1
    assert "CREATE TABLE IF NOT EXISTS videos" in copied[0].read_text(encoding="utf-8")


def test_idempotent(tmp_path):
    root = _make_project(tmp_path)
    assert init_video_migrations(root) == 0
    before = {
        p.name: p.read_bytes()
        for p in (root / "mvc" / "migrations").iterdir()
    }
    assert init_video_migrations(root) == 0  # 2e passage : rien ne change
    after = {
        p.name: p.read_bytes()
        for p in (root / "mvc" / "migrations").iterdir()
    }
    assert before == after


def test_fichier_divergent_non_ecrase(tmp_path):
    root = _make_project(tmp_path)
    name = next(n for n, _ in iter_video_migration_resources())
    target = root / "mvc" / "migrations"
    target.mkdir(parents=True)
    (target / name).write_text("-- version locale modifiée\n", encoding="utf-8")
    rc = init_video_migrations(root)
    assert rc == 0
    # Le fichier modifié à la main est conservé (charte §9).
    assert (target / name).read_text(encoding="utf-8") == "-- version locale modifiée\n"


def test_pas_un_projet_forge(tmp_path):
    # Pas de dossier mvc/ → erreur claire, rc=1.
    assert init_video_migrations(tmp_path) == 1
