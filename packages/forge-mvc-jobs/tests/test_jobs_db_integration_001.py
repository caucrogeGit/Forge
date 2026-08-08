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

    # JOBS-STALE-RECLAIM-001 : la remise en file porte un délai croissant, donc
    # la tâche n'est pas immédiatement reprise. On avance l'horloge de la file
    # plutôt que d'attendre, puis on vérifie la seconde tentative.
    assert process_one({"boom": boom}, db=jobs_db) is False, "le délai doit être respecté"
    jobs_db.execute("UPDATE jobs SET available_at = NOW() WHERE id = ?", (jid,))

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


# ── Reprise des tâches orphelines (JOBS-STALE-RECLAIM-001) ───────────────────
#
# Simuler un worker tué demande de réserver une tâche puis de n'y plus toucher,
# et de vieillir sa réservation. `_vieillir` recule `started_at` du nombre de
# secondes voulu, ce qui revient à laisser le temps passer sans l'attendre.


def _vieillir(db: _ConnAdapter, job_id: int, secondes: int) -> None:
    db.execute(
        "UPDATE jobs SET started_at = started_at - INTERVAL ? SECOND WHERE id = ?",
        (secondes, job_id),
    )


def _reserver_sans_finir(db: _ConnAdapter, job_id: int) -> None:
    """Reproduit un worker qui meurt entre la réservation et le verdict."""
    db.execute(
        "UPDATE jobs SET status='running', claim_token='jeton-mort', "
        "started_at=NOW(), attempts=attempts+1 WHERE id=?",
        (job_id,),
    )


def test_une_tache_orpheline_repart_en_file(jobs_db: _ConnAdapter) -> None:
    """LE test du ticket : sans reprise, elle restait 'running' pour toujours."""
    from forge_mvc_jobs.queue import get_job, reclaim_stale

    job_id = enqueue("lent", {"x": 1}, max_attempts=3, db=jobs_db)
    _reserver_sans_finir(jobs_db, job_id)
    _vieillir(jobs_db, job_id, 1000)

    effet = reclaim_stale(lease_seconds=900, db=jobs_db)

    assert (effet.requeued, effet.failed) == (1, 0)
    reprise = get_job(job_id, db=jobs_db)
    assert reprise is not None
    assert reprise.status == "pending"


def test_une_tache_orpheline_sans_tentative_restante_part_en_echec(
    jobs_db: _ConnAdapter,
) -> None:
    from forge_mvc_jobs.queue import RECLAIM_FAILURE_MESSAGE, get_job, reclaim_stale

    job_id = enqueue("lent", {}, max_attempts=1, db=jobs_db)
    _reserver_sans_finir(jobs_db, job_id)
    _vieillir(jobs_db, job_id, 1000)

    effet = reclaim_stale(lease_seconds=900, db=jobs_db)

    assert (effet.requeued, effet.failed) == (0, 1)
    echouee = get_job(job_id, db=jobs_db)
    assert echouee is not None
    assert echouee.status == "failed"
    assert echouee.last_error == RECLAIM_FAILURE_MESSAGE


def test_une_tache_dans_son_bail_n_est_pas_reprise(jobs_db: _ConnAdapter) -> None:
    """Le point qui fait la différence entre une reprise et un doublon."""
    from forge_mvc_jobs.queue import get_job, reclaim_stale

    job_id = enqueue("lent", {}, max_attempts=3, db=jobs_db)
    _reserver_sans_finir(jobs_db, job_id)
    _vieillir(jobs_db, job_id, 60)

    effet = reclaim_stale(lease_seconds=900, db=jobs_db)

    assert effet.total == 0
    intacte = get_job(job_id, db=jobs_db)
    assert intacte is not None
    assert intacte.status == "running"


def test_une_tache_en_attente_n_est_jamais_reprise(jobs_db: _ConnAdapter) -> None:
    """`started_at IS NULL` désigne une tâche jamais réservée, pas une orpheline."""
    from forge_mvc_jobs.queue import get_job, reclaim_stale

    job_id = enqueue("jamais_prise", {}, db=jobs_db)

    assert reclaim_stale(lease_seconds=1, db=jobs_db).total == 0
    attente = get_job(job_id, db=jobs_db)
    assert attente is not None
    assert attente.status == "pending"


def test_la_reprise_ne_touche_pas_les_autres_files(jobs_db: _ConnAdapter) -> None:
    from forge_mvc_jobs.queue import get_job, reclaim_stale

    job_id = enqueue("lent", {}, queue="emails", max_attempts=3, db=jobs_db)
    _reserver_sans_finir(jobs_db, job_id)
    _vieillir(jobs_db, job_id, 1000)

    assert reclaim_stale(queue="default", lease_seconds=900, db=jobs_db).total == 0
    assert reclaim_stale(queue="emails", lease_seconds=900, db=jobs_db).requeued == 1
    reprise = get_job(job_id, db=jobs_db)
    assert reprise is not None
    assert reprise.status == "pending"


def test_une_tache_reprise_redevient_traitable(jobs_db: _ConnAdapter) -> None:
    """La reprise doit rendre la tâche au circuit normal, pas seulement au statut.

    Elle repart avec un délai croissant : on l'annule pour vérifier que le
    worker la reprend bien ensuite.
    """
    from forge_mvc_jobs.queue import get_job, reclaim_stale

    vues: list[dict[str, Any]] = []
    job_id = enqueue("lent", {"x": 7}, max_attempts=3, db=jobs_db)
    _reserver_sans_finir(jobs_db, job_id)
    _vieillir(jobs_db, job_id, 1000)
    reclaim_stale(lease_seconds=900, db=jobs_db)

    jobs_db.execute("UPDATE jobs SET available_at = NOW() WHERE id = ?", (job_id,))
    traitees = drain({"lent": lambda p: vues.append(p)}, db=jobs_db)

    assert traitees == 1
    assert vues == [{"x": 7}]
    finie = get_job(job_id, db=jobs_db)
    assert finie is not None
    assert finie.status == "done"
