"""DB-INTROSPECTION-SCHEMA-FILTER-001 (ADR-084) — introspection bornée au schéma.

`introspect_columns` de PostgreSQL et de SQL Server ne filtrait que sur le NOM
de la table : `information_schema` exposant toutes les tables visibles de la
base, une homonyme dans un autre schéma faisait remonter ses colonnes en plus
des bonnes, **entrelacées** par la position ordinale.

Mesuré avant correctif, pour une table de deux colonnes et une homonyme de
trois : `['id', 'autre_a', 'autre_b', 'titre', 'autre_c']`. Le diff de
migration voyait donc des colonnes fantômes et proposait de les supprimer.

MariaDB filtrait déjà, par `TABLE_SCHEMA`. SQLite n'a pas de schémas.

Marqués `db` + `db_pg` / `db_mssql` : sautés sans serveur, requis en CI via
FORGE_REQUIRE_DB_PG=1 / FORGE_REQUIRE_DB_MSSQL=1.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

pytestmark = pytest.mark.db

TABLE = "b6_filter_demo"
OTHER_SCHEMA = "b6_filter_autre"

EXPECTED_COLUMNS = ["id", "titre"]
INTRUDER_COLUMNS = ["autre_a", "autre_b", "autre_c"]


def _backend() -> Any:
    from core.database.backend import get_backend

    return get_backend()


def _drop_all(cursor: Any, *, postgres: bool) -> None:
    for statement in (
        f"DROP TABLE IF EXISTS {OTHER_SCHEMA}.{TABLE}",
        f"DROP TABLE IF EXISTS {TABLE}",
    ):
        try:
            cursor.execute(statement)
        except Exception:  # noqa: BLE001 - nettoyage best effort
            pass
    drop_schema = (
        f"DROP SCHEMA IF EXISTS {OTHER_SCHEMA}"
        if postgres else
        f"IF SCHEMA_ID('{OTHER_SCHEMA}') IS NOT NULL DROP SCHEMA {OTHER_SCHEMA}"
    )
    try:
        cursor.execute(drop_schema)
    except Exception:  # noqa: BLE001 - nettoyage best effort
        pass


def _homonymes(connection: Any, *, postgres: bool) -> None:
    """Crée la table visée et une homonyme dans un autre schéma."""
    cursor = connection.cursor()
    _drop_all(cursor, postgres=postgres)
    connection.commit()

    if postgres:
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {OTHER_SCHEMA}")
    else:
        cursor.execute(
            f"IF SCHEMA_ID('{OTHER_SCHEMA}') IS NULL EXEC('CREATE SCHEMA {OTHER_SCHEMA}')"
        )
    connection.commit()

    cursor.execute(
        f"CREATE TABLE {TABLE} (id INT NOT NULL PRIMARY KEY, titre VARCHAR(50) NULL)"
    )
    columns = ", ".join(f"{name} INT NULL" for name in INTRUDER_COLUMNS)
    cursor.execute(f"CREATE TABLE {OTHER_SCHEMA}.{TABLE} ({columns})")
    connection.commit()
    cursor.close()


@pytest.fixture()
def pg_homonymes(real_pg_db: None) -> Iterator[Any]:
    connection = _backend().get_connection()
    _homonymes(connection, postgres=True)
    try:
        yield connection
    finally:
        cursor = connection.cursor()
        _drop_all(cursor, postgres=True)
        connection.commit()
        cursor.close()
        _backend().close_connection(connection)


@pytest.fixture()
def mssql_homonymes(real_mssql_db: None) -> Iterator[Any]:
    connection = _backend().get_connection()
    _homonymes(connection, postgres=False)
    try:
        yield connection
    finally:
        cursor = connection.cursor()
        _drop_all(cursor, postgres=False)
        connection.commit()
        cursor.close()
        _backend().close_connection(connection)


@pytest.mark.db_pg
def test_postgres_ignore_une_homonyme_d_un_autre_schema(pg_homonymes: Any) -> None:
    columns = _backend().dialect.introspect_columns(pg_homonymes, TABLE, "forge_test")
    names = [column[0] for column in columns]

    assert names == EXPECTED_COLUMNS, f"colonnes polluées : {names}"
    for intruder in INTRUDER_COLUMNS:
        assert intruder not in names


@pytest.mark.db_mssql
def test_mssql_ignore_une_homonyme_d_un_autre_schema(mssql_homonymes: Any) -> None:
    columns = _backend().dialect.introspect_columns(mssql_homonymes, TABLE, "forge_test")
    names = [column[0] for column in columns]

    assert names == EXPECTED_COLUMNS, f"colonnes polluées : {names}"
    for intruder in INTRUDER_COLUMNS:
        assert intruder not in names


@pytest.mark.db_pg
def test_postgres_rend_bien_les_attributs_de_la_bonne_table(pg_homonymes: Any) -> None:
    """Au-delà des noms : nullabilité et identité restent celles de la vraie table."""
    columns = {c[0]: c for c in _backend().dialect.introspect_columns(
        pg_homonymes, TABLE, "forge_test",
    )}

    assert columns["id"][2] is False, "id est NOT NULL"
    assert columns["titre"][2] is True, "titre est NULL"


@pytest.mark.db_mssql
def test_mssql_rend_bien_les_attributs_de_la_bonne_table(mssql_homonymes: Any) -> None:
    columns = {c[0]: c for c in _backend().dialect.introspect_columns(
        mssql_homonymes, TABLE, "forge_test",
    )}

    assert columns["id"][2] is False, "id est NOT NULL"
    assert columns["titre"][2] is True, "titre est NULL"
