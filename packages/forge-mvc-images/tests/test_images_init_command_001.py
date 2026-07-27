"""Garde-fous de la commande `forge images:init` (OPTIN-IMAGES-INIT-001).

Vérifie que le paquet embarque la migration `media`, que la table déclarée
correspond aux colonnes écrites par le repository, et que la commande copie la
migration dans un projet sans jamais écraser un fichier divergent.
"""
from __future__ import annotations

from pathlib import Path

import pytest

forge_mvc_images = pytest.importorskip("forge_mvc_images")

from forge_mvc_images.cli.init import (
    init_images_migrations,
    iter_images_migration_resources,
)

PKG_ROOT = Path(forge_mvc_images.__file__).resolve().parent

# Colonnes écrites par media_repository (INSERT INTO media (...)).
_MEDIA_COLUMNS = (
    "EntityName",
    "EntityId",
    "Path",
    "OriginalName",
    "MimeType",
    "Size",
    "Role",
    "Position",
    "AltText",
    "CreatedAt",
)


def test_declares_media_table() -> None:
    """Le .sql fige est remplace par une declaration rendue par le dialecte
    (OPTIN-DDL-DIALECTAL) ; on verifie les colonnes sur le rendu MariaDB."""
    pytest.importorskip("forge_mvc_mariadb")
    from core.database.table_ddl import render_create_table
    from forge_mvc_images.tables import MEDIA
    from forge_mvc_mariadb.dialect import MariaDBDialect

    assert not (PKG_ROOT / "migrations").exists()
    sql = chr(10).join(render_create_table(MEDIA, MariaDBDialect()))
    assert "CREATE TABLE IF NOT EXISTS media" in sql
    for column in _MEDIA_COLUMNS:
        assert column in sql, f"colonne {column} absente de la migration media"


def test_init_copies_migration_into_project(tmp_path: Path) -> None:
    (tmp_path / "mvc").mkdir()
    rc = init_images_migrations(tmp_path)
    assert rc == 0
    copied = list((tmp_path / "mvc" / "migrations").glob("*.sql"))
    assert copied, "la migration doit être copiée dans mvc/migrations/"


def test_init_without_mvc_dir_fails(tmp_path: Path) -> None:
    assert init_images_migrations(tmp_path) == 1


def test_init_is_idempotent(tmp_path: Path) -> None:
    (tmp_path / "mvc").mkdir()
    assert init_images_migrations(tmp_path) == 0
    # Deuxième passage : aucun écrasement, toujours succès.
    assert init_images_migrations(tmp_path) == 0


def test_init_never_overwrites_divergent_file(tmp_path: Path) -> None:
    (tmp_path / "mvc" / "migrations").mkdir(parents=True)
    name = next(iter(iter_images_migration_resources()))[0]
    target = tmp_path / "mvc" / "migrations" / name
    target.write_text("-- contenu projet à préserver\n", encoding="utf-8")
    assert init_images_migrations(tmp_path) == 0
    assert target.read_text(encoding="utf-8") == "-- contenu projet à préserver\n"
