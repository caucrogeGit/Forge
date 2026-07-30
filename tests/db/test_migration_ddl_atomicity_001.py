"""MIGRATION-DDL-NON-TRANSACTIONAL-REVEAL-001, mesure sur serveurs réels.

`Dialect.supports_transactional_ddl()` est une affirmation sur le moteur, pas
sur du SQL rendu : elle ne peut se vérifier qu'en la confrontant au serveur.
Ce fichier est cette confrontation, sur les trois SGBD serveur.

Le protocole est celui d'une migration qui casse en cours de route : deux
`CREATE TABLE` valides, un troisième fautif, un `ROLLBACK`, puis la question
« que reste-t-il en base ? ».

Sans ces tests, une régression de la capacité passerait inaperçue : elle ne
casse aucun SQL généré, elle ne change qu'un message d'erreur, et seul un
échec réel de migration la révélerait, en production.

Le pendant hors base est `tests/test_migration_failure_report_001.py`.
"""
from __future__ import annotations

from typing import Any

import pytest

pytestmark = pytest.mark.db


TABLES = ("forge_atomicity_a", "forge_atomicity_b")


def _nettoyer(cursor: Any, connection: Any) -> None:
    for table in TABLES:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    connection.commit()


def _restes(connection: Any) -> "list[str]":
    """Sonde chaque table, une transaction par sonde.

    Sur PostgreSQL, un `SELECT` sur une table absente annule la transaction en
    cours et fait ignorer toutes les commandes suivantes jusqu'au `ROLLBACK` :
    sonder les deux tables d'affilée rendrait la seconde toujours absente, et
    le test « prouverait » l'atomicité même en son absence.
    """
    presentes: "list[str]" = []
    for table in TABLES:
        cursor = connection.cursor()
        try:
            cursor.execute(f"SELECT * FROM {table}")
            cursor.fetchall()
            presentes.append(table)
        except Exception:  # noqa: BLE001 — l'absence est justement le résultat
            pass
        finally:
            cursor.close()
            try:
                connection.rollback()
            except Exception:  # noqa: BLE001 — remise à zéro best-effort
                pass
    return presentes


def _mesurer(connection: Any, *, ouvrir: str) -> "list[str]":
    """Joue la migration fautive et rend ce qui a survécu au ROLLBACK."""
    cursor = connection.cursor()
    _nettoyer(cursor, connection)
    try:
        if ouvrir:
            cursor.execute(ouvrir)
        cursor.execute(f"CREATE TABLE {TABLES[0]} (id INT)")
        cursor.execute(f"CREATE TABLE {TABLES[1]} (id INT)")
        cursor.execute("CREATE TABLE forge_atomicity_c (id FORGE_TYPE_INEXISTANT)")
        connection.commit()
        pytest.fail("la troisième instruction aurait dû échouer")
    except Exception:  # noqa: BLE001 — l'échec est le scénario
        try:
            connection.rollback()
        except Exception:  # noqa: BLE001 — annulation best-effort, comme le runner
            pass

    cursor.close()
    survivantes = _restes(connection)

    menage = connection.cursor()
    _nettoyer(menage, connection)
    menage.close()
    return survivantes


def _capacite(module: str, classe: str) -> bool:
    importe = pytest.importorskip(module)
    return bool(getattr(importe, classe)().supports_transactional_ddl())


# ── MariaDB : le seul non atomique ───────────────────────────────────────────

def test_mariadb_garde_la_ddl_deja_passee(real_db: None) -> None:
    """Le fait qui motive tout le ticket, mesuré et non déduit d'une lecture."""
    from core.database.backend import get_backend

    connection = get_backend().get_connection()
    try:
        survivantes = _mesurer(connection, ouvrir="START TRANSACTION")
    finally:
        get_backend().close_connection(connection)

    assert survivantes == list(TABLES), (
        "MariaDB devrait garder les deux tables : si elles ont disparu, le "
        "moteur a changé de comportement et la capacité doit être revue"
    )


def test_le_dialecte_mariadb_dit_la_verite(real_db: None) -> None:
    assert _capacite("forge_mvc_mariadb.dialect", "MariaDBDialect") is False


# ── PostgreSQL et SQL Server : atomiques ─────────────────────────────────────

@pytest.mark.db_pg
def test_postgres_annule_toute_la_migration(real_pg_db: None) -> None:
    from core.database.backend import get_backend

    connection = get_backend().get_connection()
    try:
        survivantes = _mesurer(connection, ouvrir="")
    finally:
        get_backend().close_connection(connection)

    assert survivantes == []


@pytest.mark.db_pg
def test_le_dialecte_postgres_dit_la_verite(real_pg_db: None) -> None:
    assert _capacite("forge_mvc_postgres.dialect", "PostgreSQLDialect") is True


@pytest.mark.db_mssql
def test_mssql_annule_toute_la_migration(real_mssql_db: None) -> None:
    from core.database.backend import get_backend

    connection = get_backend().get_connection()
    try:
        survivantes = _mesurer(connection, ouvrir="BEGIN TRANSACTION")
    finally:
        get_backend().close_connection(connection)

    assert survivantes == []


@pytest.mark.db_mssql
def test_le_dialecte_mssql_dit_la_verite(real_mssql_db: None) -> None:
    assert _capacite("forge_mvc_mssql.dialect", "MSSQLDialect") is True
