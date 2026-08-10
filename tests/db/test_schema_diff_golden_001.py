"""ENTITIES-DIFF-TYPE-FAMILIES-001 (ADR-084) — test d'or du diff de schéma.

Le contrôle décisif du ticket : une table **créée depuis le DDL que Forge
génère** doit produire un diff **vide**. Toute ligne autre que « OK » signale
que le schéma attendu et le schéma réel ne se reconnaissent pas, alors qu'ils
sortent de la même source.

Avant correctif, PostgreSQL et SQL Server signalaient chaque colonne comme
modifiée : `information_schema` rend `character varying` ou `NVARCHAR` sans
longueur, là où le générateur écrit `VARCHAR(255)` ou `NVARCHAR(255)`.

Le contrôle négatif est aussi important que le positif : une vraie dérive doit
rester détectée, sans quoi le correctif aurait simplement rendu le diff
aveugle.

MariaDB a rejoint ce test d'or après coup, et y a révélé son propre défaut :
`BOOLEAN`, écrit par le générateur, est **stocké** `TINYINT(1)`, et les deux
rendaient des familles différentes. Le backend en était absent parce que son
serveur n'était pas joignable à la livraison du diff par familles.

Marqués `db`, plus `db_pg` / `db_mssql` pour les deux backends qui ont leur
propre job de CI : sautés sans serveur, requis via FORGE_REQUIRE_DB*=1.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from core.database.table_ddl import (
    Column,
    TableDefinition,
    column_sql_type,
    render_create_table,
)
from forge_mvc_entities.migrations import (
    ExpectedColumn,
    build_schema_diff_report,
    load_table_columns,
)

pytestmark = pytest.mark.db

TABLE = "diff_golden_demo"

# Un échantillon qui traverse les familles : identité, chaîne bornée, texte
# long, booléen et horodatage. Chacune se nomme différemment selon le moteur.
SPECS: tuple[tuple[str, str, "int | None", bool], ...] = (
    ("id", "identity", None, False),
    ("titre", "string", 255, False),
    ("resume", "text", None, True),
    ("actif", "boolean", None, False),
    ("cree_le", "datetime", None, True),
)


def _backend() -> Any:
    from core.database.backend import get_backend

    return get_backend()


def _columns() -> list[Column]:
    return [
        Column(name=name, type=kind, length=length, nullable=nullable)
        for name, kind, length, nullable in SPECS
    ]


def _expected(dialect: Any) -> list[ExpectedColumn]:
    return [
        ExpectedColumn(
            name=column.name,
            sql_type=column_sql_type(column, dialect),
            nullable=column.nullable,
            auto_increment=column.type == "identity",
        )
        for column in _columns()
    ]


def _fresh_table(database: str) -> Iterator[Any]:
    """Crée la table depuis le DDL généré, la rend, puis la supprime."""
    backend = _backend()
    connection = backend.get_connection()
    cursor = connection.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {TABLE}")
    connection.commit()

    table = TableDefinition(name=TABLE, columns=_columns(), primary_key=["id"])
    for statement in render_create_table(table, backend.dialect):
        cursor.execute(statement)
    connection.commit()
    cursor.close()

    try:
        yield connection
    finally:
        cursor = connection.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {TABLE}")
        connection.commit()
        cursor.close()
        backend.close_connection(connection)


def _base_configuree() -> str:
    """Nom de la base réellement configurée par la fixture, jamais un littéral.

    Les fixtures serveur donnent une base **par worker** sous `-n`
    (`TEST-DB-WORKER-ISOLATION-001`) : « forge_test » codé en dur interrogeait
    `information_schema` sur une base où la table n'existait pas, et le diff
    rendait « table absente en base ».
    """
    import os

    return os.environ["DB_NAME"]


@pytest.fixture()
def mariadb_table(real_db: None) -> Iterator[Any]:
    yield from _fresh_table(_base_configuree())


@pytest.fixture()
def pg_table(real_pg_db: None) -> Iterator[Any]:
    yield from _fresh_table(_base_configuree())


@pytest.fixture()
def mssql_table(real_mssql_db: None) -> Iterator[Any]:
    yield from _fresh_table(_base_configuree())


def _assert_diff_vide(connection: Any) -> None:
    dialect = _backend().dialect
    actual = load_table_columns(TABLE, db=connection, database=_base_configuree())
    report = build_schema_diff_report("Golden", TABLE, _expected(dialect), actual)

    unexpected = [(row.status, row.column, row.detail) for row in report.rows if row.status != "OK"]
    assert unexpected == [], (
        "une table créée depuis le DDL généré doit donner un diff vide : "
        f"{unexpected}"
    )
    assert report.table_status == "OK"


def _assert_derive_detectee(connection: Any) -> None:
    """Contrôle négatif : une longueur qui ne correspond pas reste signalée."""
    dialect = _backend().dialect
    actual = load_table_columns(TABLE, db=connection, database=_base_configuree())

    drifted = [
        ExpectedColumn(
            name="titre",
            sql_type=dialect.string_type(64),  # la base porte 255
            nullable=False,
            auto_increment=False,
        )
    ]
    report = build_schema_diff_report(
        "Golden", TABLE, drifted, [c for c in actual if c.name == "titre"],
    )
    assert report.table_status != "OK", "une vraie dérive de longueur doit rester vue"


def test_mariadb_table_fraiche_donne_un_diff_vide(mariadb_table: Any) -> None:
    """Le backend le plus employé, et le dernier arrivé dans ce test d'or.

    Il en était absent parce que le serveur n'était pas joignable à la
    livraison du diff par familles. Un défaut y dormait donc :
    `BOOLEAN`, écrit par le générateur, est stocké `TINYINT(1)` par MariaDB, et
    les deux rendaient des familles différentes.
    """
    _assert_diff_vide(mariadb_table)


def test_mariadb_une_vraie_derive_reste_detectee(mariadb_table: Any) -> None:
    _assert_derive_detectee(mariadb_table)


@pytest.mark.db_pg
def test_postgres_table_fraiche_donne_un_diff_vide(pg_table: Any) -> None:
    _assert_diff_vide(pg_table)


@pytest.mark.db_pg
def test_postgres_une_vraie_derive_reste_detectee(pg_table: Any) -> None:
    _assert_derive_detectee(pg_table)


@pytest.mark.db_mssql
def test_mssql_table_fraiche_donne_un_diff_vide(mssql_table: Any) -> None:
    _assert_diff_vide(mssql_table)


@pytest.mark.db_mssql
def test_mssql_une_vraie_derive_reste_detectee(mssql_table: Any) -> None:
    _assert_derive_detectee(mssql_table)


@pytest.mark.db_pg
def test_postgres_introspection_porte_la_longueur(pg_table: Any) -> None:
    """La cause du défaut : `data_type` seul ne portait pas la longueur."""
    columns = {c.name: c for c in load_table_columns(TABLE, db=pg_table, database=_base_configuree())}
    assert "(255)" in columns["titre"].sql_type, columns["titre"].sql_type


@pytest.mark.db_mssql
def test_mssql_introspection_porte_la_longueur(mssql_table: Any) -> None:
    columns = {c.name: c for c in load_table_columns(TABLE, db=mssql_table, database=_base_configuree())}
    assert "(255)" in columns["titre"].sql_type, columns["titre"].sql_type
