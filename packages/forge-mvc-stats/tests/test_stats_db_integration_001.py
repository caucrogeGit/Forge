"""Intégration MariaDB de forge-mvc-stats (STATS-RETENTION-001).

Le paquet n'avait aucun test d'intégration : il rendait du SQL que personne
n'exécutait jamais. Rendre un DDL et l'appliquer sont deux choses, et le second
est le seul qui prouve quoi que ce soit à l'exploitant.

Ce fichier applique réellement la migration déclarée par `tables.py`, écrit des
événements, puis vérifie la purge par âge. Marqué `db` : sauté en local sans
base, requis en CI.
"""
from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from typing import Any

import pytest

pytestmark = pytest.mark.db

pytest.importorskip("forge_mvc_stats")

from forge_mvc_stats.retention import (
    count_stats_events_before,
    cutoff_for_days,
    purge_stats_events_before,
)
from forge_mvc_stats.tracking import track_event

from forge_mvc_testing.db_probe import connection_failure_message

_REQUIRE_DB = os.environ.get("FORGE_REQUIRE_DB") == "1"


def _rendered_ddl() -> str:
    """DDL de la table, rendu pour le backend actif (source unique, ADR-071)."""
    from core.database.backend import get_backend
    from core.database.table_ddl import render_create_table
    from forge_mvc_stats.tables import STATS_EVENTS

    return chr(10).join(render_create_table(STATS_EVENTS, get_backend().dialect))


def _params() -> dict[str, Any]:
    return {
        "host": os.environ.get("FORGE_TEST_DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("FORGE_TEST_DB_PORT", "3306")),
        "user": os.environ.get("FORGE_TEST_DB_USER", "root"),
        "password": os.environ.get("FORGE_TEST_DB_PASSWORD", ""),
    }


class _ConnAdapter:
    def __init__(self, conn: Any, database: str) -> None:
        self._conn = conn
        self._database = database

    def execute(self, sql: str, params: Any = ()) -> int:
        cur = self._conn.cursor()
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        self._conn.commit()
        compte = cur.rowcount
        cur.close()
        return int(compte)

    def fetch_one(self, sql: str, params: Any = ()) -> "dict[str, Any] | None":
        cur = self._conn.cursor(dictionary=True)
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        row = cur.fetchone()
        cur.close()
        return row


@pytest.fixture
def stats_db() -> Iterator[_ConnAdapter]:
    try:
        import mariadb
    except ImportError:  # pragma: no cover
        pytest.skip("paquet python 'mariadb' non installé")

    params = _params()
    db_name = f"forge_it_stats_{uuid.uuid4().hex[:10]}"
    try:
        admin = mariadb.connect(**params)
    except Exception as error:  # noqa: BLE001
        message = connection_failure_message(
            "MariaDB", error, env_prefix="FORGE_TEST_DB"
        )
        if _REQUIRE_DB:
            pytest.fail(message + " (FORGE_REQUIRE_DB=1)")
        pytest.skip(message + " (test d'intégration sauté en local)")

    cur = admin.cursor()
    cur.execute(f"CREATE DATABASE `{db_name}`")
    cur.execute(f"USE `{db_name}`")
    for instruction in _rendered_ddl().split(";"):
        if instruction.strip():
            cur.execute(instruction)
    admin.commit()
    cur.close()
    try:
        yield _ConnAdapter(admin, db_name)
    finally:
        cur = admin.cursor()
        cur.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
        admin.commit()
        cur.close()
        admin.close()


def _inserer_date(db: _ConnAdapter, nom: str, created_at: str) -> None:
    db.execute(
        "INSERT INTO forge_stats_events (name, label, category, created_at) "
        "VALUES (?, ?, ?, ?)",
        (nom, nom, "general", created_at),
    )


def test_la_migration_declaree_s_applique_vraiment(stats_db: _ConnAdapter) -> None:
    """La fixture a appliqué le DDL : si elle a tenu, la table existe.

    C'est le test qui manquait le plus. Le paquet rendait un DDL que rien
    n'exécutait jamais, donc une erreur de rendu ne se serait vue qu'en
    production.
    """
    row = stats_db.fetch_one("SELECT COUNT(*) AS total FROM forge_stats_events", ())

    assert row is not None
    assert row["total"] == 0


def test_un_evenement_suivi_atterrit_dans_la_table(stats_db: _ConnAdapter) -> None:
    track_event(stats_db.execute, "page_vue", label="Page vue")

    row = stats_db.fetch_one("SELECT COUNT(*) AS total FROM forge_stats_events", ())
    assert row is not None
    assert row["total"] == 1


def test_la_purge_ne_retire_que_les_evenements_anterieurs(stats_db: _ConnAdapter) -> None:
    """LE test du ticket : la borne discrimine, elle ne vide pas la table."""
    _inserer_date(stats_db, "vieux", "2020-01-01 00:00:00")
    _inserer_date(stats_db, "recent", "2026-08-01 00:00:00")
    borne = "2026-01-01 00:00:00"

    assert count_stats_events_before(stats_db.fetch_one, borne) == 1
    assert purge_stats_events_before(stats_db.execute, borne) == 1

    restant = stats_db.fetch_one("SELECT name FROM forge_stats_events", ())
    assert restant is not None
    assert restant["name"] == "recent"


def test_le_comptage_ne_supprime_rien(stats_db: _ConnAdapter) -> None:
    _inserer_date(stats_db, "vieux", "2020-01-01 00:00:00")
    borne = "2026-01-01 00:00:00"

    assert count_stats_events_before(stats_db.fetch_one, borne) == 1
    assert count_stats_events_before(stats_db.fetch_one, borne) == 1


def test_la_borne_calculee_en_jours_s_applique_reellement(stats_db: _ConnAdapter) -> None:
    """Point de jonction entre le calcul Python et la colonne SQL.

    Un format d'horodatage divergent passerait les tests unitaires et
    n'échouerait qu'ici.
    """
    from datetime import datetime, timedelta, timezone

    maintenant = datetime.now(timezone.utc)
    _inserer_date(
        stats_db, "vieux", (maintenant - timedelta(days=400)).strftime("%Y-%m-%d %H:%M:%S")
    )
    _inserer_date(
        stats_db, "recent", (maintenant - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
    )

    assert purge_stats_events_before(stats_db.execute, cutoff_for_days(365)) == 1
    restant = stats_db.fetch_one("SELECT name FROM forge_stats_events", ())
    assert restant is not None
    assert restant["name"] == "recent"
