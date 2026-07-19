"""PG-MIGRATIONS-INTEGRATION-001 (ADR-084) — runner de migrations sur un vrai PostgreSQL.

Miroir de test_db_init_migrations_001 (MariaDB) pour le chemin migrations :
application réelle et enregistrement dans forge_migrations, idempotence,
dry-run sans écriture, refus d'une migration modifiée (CHANGED), rollback
transactionnel réel en cas d'échec SQL, et introspection réelle du schéma
(load_table_columns via information_schema). Dernier critère 4 de la
promotion (ADR-084).

Marqué `db` + `db_pg` : sauté sans serveur, requis en CI via FORGE_REQUIRE_DB_PG=1.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest

from forge_mvc_entities import migrations as mig

pytestmark = [pytest.mark.db, pytest.mark.db_pg]


def _widgets_sql(table: str) -> str:
    return (
        f"CREATE TABLE {table} (\n"
        "    id SERIAL PRIMARY KEY,\n"
        "    label VARCHAR(50) NOT NULL\n"
        ");\n"
    )


def _connect() -> Any:
    from core.database.backend import get_backend

    return get_backend().get_connection()


@pytest.fixture()
def pg_registry(real_pg_db: None) -> Any:
    """Registre forge_migrations recréé à neuf (isolation entre tests)."""
    from core.database.backend import get_backend

    backend = get_backend()
    connection = backend.get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS forge_migrations")
        cursor.execute(backend.dialect.forge_migrations_ddl())
        connection.commit()
        cursor.close()
    finally:
        backend.close_connection(connection)
    yield


def _table() -> str:
    return f"forge_it_pg_widgets_{uuid.uuid4().hex[:10]}"


def _exec(sql: str) -> None:
    connection = _connect()
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        connection.commit()
        cursor.close()
    finally:
        connection.close()


def _apply(migrations_dir: Path, *, dry_run: bool = False) -> list[mig.MigrationFile]:
    connection = _connect()
    try:
        return mig.apply_pending_migrations(migrations_dir, db=connection, dry_run=dry_run)
    finally:
        connection.close()


def _applied_versions() -> list[str]:
    connection = _connect()
    try:
        return [m.version for m in mig.load_applied_migrations(db=connection)]
    finally:
        connection.close()


def _scalar(sql: str, params: "tuple[Any, ...]" = ()) -> Any:
    connection = _connect()
    try:
        cursor = connection.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        connection.commit()
        cursor.close()
        return row
    finally:
        connection.close()


def test_apply_creates_table_and_records_migration(pg_registry: None, tmp_path: Path) -> None:
    table = _table()
    (tmp_path / "20260101000000_create_widgets.sql").write_text(_widgets_sql(table), encoding="utf-8")
    try:
        applied = _apply(tmp_path)

        assert [m.version for m in applied] == ["20260101000000"]
        exists = _scalar(
            "SELECT table_name FROM information_schema.tables WHERE table_name = ?",
            (table,),
        )
        assert exists is not None, "la table doit être créée en base"
        assert _applied_versions() == ["20260101000000"]
    finally:
        _exec(f"DROP TABLE IF EXISTS {table}")


def test_apply_is_idempotent(pg_registry: None, tmp_path: Path) -> None:
    table = _table()
    (tmp_path / "20260101000000_create_widgets.sql").write_text(_widgets_sql(table), encoding="utf-8")
    try:
        _apply(tmp_path)
        again = _apply(tmp_path)
        assert again == [], "une migration déjà appliquée ne doit pas être ré-exécutée"
    finally:
        _exec(f"DROP TABLE IF EXISTS {table}")


def test_apply_dry_run_writes_nothing(pg_registry: None, tmp_path: Path) -> None:
    table = _table()
    (tmp_path / "20260101000000_create_widgets.sql").write_text(_widgets_sql(table), encoding="utf-8")

    planned = _apply(tmp_path, dry_run=True)

    assert [m.version for m in planned] == ["20260101000000"]
    assert _applied_versions() == [], "dry-run ne doit rien enregistrer"
    exists = _scalar(
        "SELECT table_name FROM information_schema.tables WHERE table_name = ?",
        (table,),
    )
    assert exists is None, "dry-run ne doit pas créer la table"


def test_apply_refuses_changed_migration(pg_registry: None, tmp_path: Path) -> None:
    table = _table()
    path = tmp_path / "20260101000000_create_widgets.sql"
    path.write_text(_widgets_sql(table), encoding="utf-8")
    try:
        _apply(tmp_path)
        # Le fichier local change de checksum après application : CHANGED.
        path.write_text(_widgets_sql(table).replace("VARCHAR(50)", "VARCHAR(99)"), encoding="utf-8")
        with pytest.raises(mig.MigrationError, match="modifiée"):
            _apply(tmp_path)
    finally:
        _exec(f"DROP TABLE IF EXISTS {table}")


def test_apply_rolls_back_on_sql_failure(pg_registry: None, tmp_path: Path) -> None:
    """Une migration dont une instruction échoue est annulée (rollback réel)."""
    table = _table()
    (tmp_path / "20260101000000_create_widgets.sql").write_text(_widgets_sql(table), encoding="utf-8")
    try:
        _apply(tmp_path)

        # v2 : un INSERT valide suivi d'un INSERT sur une colonne inexistante.
        (tmp_path / "20260202000000_seed_then_fail.sql").write_text(
            f"INSERT INTO {table} (label) VALUES ('temp');\n"
            f"INSERT INTO {table} (nope) VALUES ('x');\n",
            encoding="utf-8",
        )
        with pytest.raises(mig.MigrationError, match="erreur SQL"):
            _apply(tmp_path)

        count = _scalar(f"SELECT COUNT(*) FROM {table}")
        assert count[0] == 0, "l'INSERT valide doit être annulé par le rollback"
        assert "20260202000000" not in _applied_versions(), (
            "une migration échouée ne doit pas être enregistrée"
        )
    finally:
        _exec(f"DROP TABLE IF EXISTS {table}")


def test_introspection_reelle_du_schema(pg_registry: None, tmp_path: Path) -> None:
    """load_table_columns lit le vrai information_schema PostgreSQL."""
    table = _table()
    _exec(_widgets_sql(table))
    try:
        connection = _connect()
        try:
            columns = mig.load_table_columns(table, db=connection, database="forge_test")
        finally:
            connection.close()

        by_name = {c.name: c for c in columns}
        assert set(by_name) == {"id", "label"}
        assert by_name["id"].auto_increment is True, "SERIAL doit être vu comme auto"
        assert by_name["label"].nullable is False
    finally:
        _exec(f"DROP TABLE IF EXISTS {table}")
