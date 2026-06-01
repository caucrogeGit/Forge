"""Tests VIDEO-CONFIG-001 : table `videos` (migration SQL packagée).

La migration est embarquée dans `forge_mvc_video/migrations/` et shippée via
`[tool.setuptools.package-data]`. Test documentaire : lit le SQL, ne touche
aucune base.
"""
from __future__ import annotations

from importlib import resources


def _migration_sql() -> str:
    anchor = resources.files("forge_mvc_video") / "migrations"
    files = [e for e in anchor.iterdir() if e.name.endswith("_create_videos.sql")]
    assert len(files) == 1, f"une seule migration videos attendue, trouvé {files}"
    return files[0].read_text(encoding="utf-8")


def test_migration_creates_videos_table_idempotent():
    sql = _migration_sql()
    assert "CREATE TABLE IF NOT EXISTS videos" in sql      # idempotente
    assert "ENGINE=InnoDB" in sql
    assert "utf8mb4" in sql


def test_migration_has_lifecycle_columns():
    sql = _migration_sql()
    for column in (
        "uuid", "original_path", "mp4_path", "poster_path",
        "size_bytes", "duration_seconds", "width", "height",
        "status", "error_message", "created_at", "updated_at",
    ):
        assert column in sql, f"colonne manquante : {column}"


def test_migration_keys_and_indexes():
    sql = _migration_sql()
    assert "PRIMARY KEY (id)" in sql
    assert "UNIQUE KEY uq_videos_uuid (uuid)" in sql
    assert "INDEX idx_videos_status (status)" in sql


def test_doctor_reports_migration_present():
    from forge_mvc_video.cli.doctor import check_migration_present

    result = check_migration_present()
    assert result.status == "ok"
    assert result.name == "migration"
    assert result.detail.endswith("_create_videos.sql")
