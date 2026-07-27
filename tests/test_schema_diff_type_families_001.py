"""ENTITIES-DIFF-TYPE-FAMILIES-001 (ADR-084) : diff de schéma portable.

`_column_changes` comparait deux **chaînes** de types. Hors MariaDB, elles ne
coïncident jamais : l'introspection de PostgreSQL rend `character varying` là
où le générateur écrit `VARCHAR(255)`, et SQL Server `NVARCHAR` sans longueur.
`forge migration:diff` déclarait donc **chaque colonne modifiée** sur une table
pourtant conforme, et `migration:make --from-diff` refusait de produire quoi
que ce soit en criant au « diff risqué ».

Trois défauts distincts, corrigés ensemble :
- la comparaison porte sur la **famille** du type, exposée par le contrat
  `Dialect`, puis sur ses arguments ;
- l'introspection de PostgreSQL et de SQL Server recompose la **longueur**,
  que `information_schema` publie dans une colonne séparée ;
- SQLite déclare `notnull = 0` sur un `INTEGER PRIMARY KEY` alors qu'il refuse
  les NULL : la clé primaire n'est plus rapportée nullable.

Le contrôle décisif est ailleurs, dans `tests/db/` : une table fraîchement
créée depuis le DDL généré doit donner un diff **vide** sur chaque moteur.
"""
from __future__ import annotations

import sqlite3
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from forge_mvc_entities.migrations import (
    ActualColumn,
    ExpectedColumn,
    _same_type,
    _type_arguments,
    build_schema_diff_report,
)


@pytest.fixture()
def backend_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    from core.database import backend as backend_module

    def use(name: str, **env: str) -> None:
        monkeypatch.setenv("DB_BACKEND", name)
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        backend_module.reset_backend()

    try:
        yield use
    finally:
        backend_module.reset_backend()


# ── Extraction des arguments ─────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("sql_type", "expected"),
    [
        ("VARCHAR(255)", "255"),
        ("character varying(255)", "255"),
        ("DECIMAL(10, 2)", "10,2"),
        ("NVARCHAR(MAX)", "MAX"),
        ("TEXT", ""),
        ("BIGINT UNSIGNED", ""),
    ],
)
def test_arguments_extraits_et_normalises(sql_type: str, expected: str) -> None:
    assert _type_arguments(sql_type) == expected


# ── Comparaison par famille ──────────────────────────────────────────────────

def test_postgres_reconnait_son_propre_vocabulaire(backend_env: Any) -> None:
    """`VARCHAR(255)` généré et `character varying(255)` introspecté : même type."""
    backend_env("postgres")
    assert _same_type("VARCHAR(255)", "character varying(255)")
    assert _same_type("TIMESTAMP", "timestamp without time zone")


def test_mssql_reconnait_son_propre_vocabulaire(backend_env: Any) -> None:
    backend_env("mssql")
    assert _same_type("NVARCHAR(255)", "NVARCHAR(255)")
    assert _same_type("DECIMAL(10,2)", "DECIMAL(10,2)")


@pytest.mark.parametrize("name", ("mariadb", "sqlite", "postgres", "mssql"))
def test_une_vraie_difference_de_famille_reste_vue(name: str, backend_env: Any) -> None:
    """Le correctif ne doit pas rendre le diff aveugle."""
    backend_env("sqlite" if name == "sqlite" else name)
    from core.database.backend import get_backend

    dialect = get_backend().dialect
    assert not _same_type(dialect.string_type(50), dialect.simple_type("integer"))


def test_une_longueur_differente_reste_vue(backend_env: Any) -> None:
    backend_env("postgres")
    assert not _same_type("VARCHAR(255)", "character varying(100)")


def test_longueur_absente_d_un_cote_ne_conclut_pas(backend_env: Any) -> None:
    """Un type sans parenthèses n'apprend rien sur la longueur de l'autre."""
    backend_env("postgres")
    assert _same_type("VARCHAR(255)", "character varying")


# ── SQLite : la clé primaire n'est plus rapportée nullable ───────────────────

def test_sqlite_ne_declare_plus_la_cle_primaire_nullable(backend_env: Any) -> None:
    """`PRAGMA table_info` dit `notnull = 0`, SQLite refuse pourtant les NULL."""
    with tempfile.TemporaryDirectory() as tmp:
        database = Path(tmp) / "diff.sqlite3"
        backend_env("sqlite", DB_NAME=str(database))
        from core.database.backend import get_backend

        connection = sqlite3.connect(database)
        connection.execute(
            "CREATE TABLE articles (id INTEGER PRIMARY KEY, titre VARCHAR(50) NOT NULL)"
        )
        connection.commit()

        columns = {
            row[0]: row
            for row in get_backend().dialect.introspect_columns(connection, "articles", "")
        }
        connection.close()

    assert columns["id"][2] is False, "un INTEGER PRIMARY KEY n'est jamais nullable"
    assert columns["id"][3] is True, "et c'est lui que SQLite auto-incrémente"
    assert columns["titre"][2] is False


def test_sqlite_diff_d_une_cle_primaire_est_vide(backend_env: Any) -> None:
    """Bout en bout : plus de fausse différence sur la clé primaire."""
    with tempfile.TemporaryDirectory() as tmp:
        database = Path(tmp) / "diff.sqlite3"
        backend_env("sqlite", DB_NAME=str(database))
        from core.database.backend import get_backend

        dialect = get_backend().dialect
        connection = sqlite3.connect(database)
        connection.execute("CREATE TABLE articles (id INTEGER PRIMARY KEY)")
        connection.commit()
        rows = dialect.introspect_columns(connection, "articles", "")
        connection.close()

        actual = [
            ActualColumn(name=r[0], sql_type=r[1], nullable=r[2], auto_increment=r[3])
            for r in rows
        ]
        expected = [
            ExpectedColumn(
                name="id", sql_type=dialect.identity_type(),
                nullable=False, auto_increment=True,
            )
        ]

    report = build_schema_diff_report("Article", "articles", expected, actual)
    assert report.table_status == "OK", [(r.status, r.detail) for r in report.rows]
