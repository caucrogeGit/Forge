"""Intégration MariaDB de la file de jobs (JOBS-DB-INTEGRATION-001).

Vérifie la mécanique réelle face au moteur : le DDL rendu, la réservation
atomique (`UPDATE ... LIMIT 1` + jeton), l'exécution, la reprise sur échec, la
disponibilité différée (`available_in`). Marqué `db` : sauté en local sans base,
requis en CI. Connexion auto-suffisante via `FORGE_TEST_DB_*`.
"""
from __future__ import annotations

import os
import uuid
from typing import Any

import pytest

pytestmark = pytest.mark.db

forge_mvc_jobs = pytest.importorskip("forge_mvc_jobs")

from forge_mvc_jobs import (
    drain,
    enqueue,
    get_job,
    pending_count,
    process_one,
)

_REQUIRE_DB = os.environ.get("FORGE_REQUIRE_DB") == "1"


def _rendered_ddl() -> str:
    """DDL de la table, rendu pour le backend actif.

    La constante de schéma du module est supprimée
    (`OPTIN-DDL-CONSTANTS-001`) : deux façons officielles de créer la même
    table contredisaient le principe 11. La source unique est la déclaration
    `forge_mvc_jobs.tables`, rendue par le dialecte.
    """
    from core.database.backend import get_backend
    from core.database.table_ddl import render_create_table
    from forge_mvc_jobs.tables import JOBS

    return chr(10).join(render_create_table(JOBS, get_backend().dialect))

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
        rc = cur.rowcount
        cur.close()
        return rc

    def insert(self, sql: str, params: Any = ()) -> int:
        cur = self._conn.cursor()
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        self._conn.commit()
        rid = cur.lastrowid
        cur.close()
        return int(rid)

    def fetch_one(self, sql: str, params: Any = ()) -> dict[str, Any] | None:
        cur = self._conn.cursor(dictionary=True)
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        row = cur.fetchone()
        cur.close()
        return row


@pytest.fixture
def jobs_db() -> Any:
    try:
        import mariadb
    except ImportError:  # pragma: no cover
        pytest.skip("paquet python 'mariadb' non installé")

    params = _params()
    db_name = f"forge_it_jobs_{uuid.uuid4().hex[:10]}"
    try:
        admin = mariadb.connect(**params)
    except Exception as error:  # noqa: BLE001
        message = f"MariaDB de test injoignable : {error}"
        if _REQUIRE_DB:
            pytest.fail(message + " (FORGE_REQUIRE_DB=1)")
        pytest.skip(message + " (test d'intégration sauté en local)")

    cur = admin.cursor()
    cur.execute(f"CREATE DATABASE `{db_name}`")
    cur.execute(f"USE `{db_name}`")
    cur.execute(_rendered_ddl())
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


def test_enqueue_then_drain_runs_handler(jobs_db: _ConnAdapter) -> None:
    seen: list[dict[str, Any]] = []
    enqueue("greet", {"name": "Alice"}, db=jobs_db)
    enqueue("greet", {"name": "Bob"}, db=jobs_db)
    assert drain({"greet": seen.append}, db=jobs_db) == 2
    assert {d["name"] for d in seen} == {"Alice", "Bob"}
    assert pending_count(db=jobs_db) == 0


def test_done_status_is_persisted(jobs_db: _ConnAdapter) -> None:
    jid = enqueue("noop", db=jobs_db)
    drain({"noop": lambda _p: None}, db=jobs_db)
    job = get_job(jid, db=jobs_db)
    assert job is not None and job.status == "done"


def test_failure_retries_then_fails(jobs_db: _ConnAdapter) -> None:
    def boom(_p: dict[str, Any]) -> None:
        raise RuntimeError("oups")

    jid = enqueue("boom", max_attempts=2, db=jobs_db)
    assert process_one({"boom": boom}, db=jobs_db) is True
    assert get_job(jid, db=jobs_db).status == "pending"  # re-mise en file
    assert process_one({"boom": boom}, db=jobs_db) is True
    failed = get_job(jid, db=jobs_db)
    assert failed.status == "failed" and "oups" in failed.last_error


def test_unknown_task_is_failed(jobs_db: _ConnAdapter) -> None:
    jid = enqueue("inconnue", db=jobs_db)
    process_one({}, db=jobs_db)
    assert get_job(jid, db=jobs_db).status == "failed"


def test_available_in_delays_the_job(jobs_db: _ConnAdapter) -> None:
    enqueue("later", available_in=3600, db=jobs_db)
    # Le job n'est pas encore disponible : drain ne le réserve pas.
    assert drain({"later": lambda _p: None}, db=jobs_db) == 0
    assert pending_count(db=jobs_db) == 1


def test_empty_queue_process_one_false(jobs_db: _ConnAdapter) -> None:
    assert process_one({}, db=jobs_db) is False
