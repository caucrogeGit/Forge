"""Logique de la file de jobs (JOBS-OPTIN-SCAFFOLD-001).

Un FakeDb émule la file en mémoire : on teste enqueue, la réservation, le
dispatch vers les gestionnaires et la reprise sur échec, sans MariaDB. La
mécanique SQL atomique réelle est vérifiée par le test d'intégration `db`.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

forge_mvc_jobs = pytest.importorskip("forge_mvc_jobs")

from forge_mvc_jobs import (
    JobError,
    drain,
    enqueue,
    get_job,
    pending_count,
    process_one,
)


class FakeDb:
    """Émule la table `jobs` en mémoire (réservation par jeton incluse)."""

    def __init__(self) -> None:
        self.jobs: dict[int, dict[str, Any]] = {}
        self._next = 1

    def insert(self, sql: str, params: Any = ()) -> int:
        queue, task, payload, max_attempts, available_in = params
        jid = self._next
        self._next += 1
        self.jobs[jid] = {
            "id": jid, "queue": queue, "task": task, "payload": payload,
            "status": "pending", "attempts": 0, "max_attempts": max_attempts,
            "claim_token": None, "last_error": None, "available_in": available_in,
        }
        return jid

    def execute(self, sql: str, params: Any = ()) -> int:
        if "attempts=attempts+1" in sql:  # réservation, sous garde de statut
            # OPTIN-DML-DIALECT-001 : la réservation se fait en deux temps,
            # `UPDATE ... ORDER BY ... LIMIT 1` n'étant accepté que par MariaDB.
            # La candidate est choisie par `fetch_one`, puis réservée ici.
            token, jid = params
            job = self.jobs.get(jid)
            if job is None or job["status"] != "pending":
                return 0
            job.update(status="running", claim_token=token, attempts=job["attempts"] + 1)
            return 1
        if "status='done'" in sql:
            self.jobs[params[0]]["status"] = "done"
            return 1
        if "status='failed'" in sql:
            err, jid = params
            self.jobs[jid].update(status="failed", last_error=err)
            return 1
        if "status='pending', claim_token=NULL" in sql:  # reprise
            # JOBS-STALE-RECLAIM-001 : la remise en file porte désormais un
            # délai croissant, annoncé AVANT l'identifiant dans les paramètres
            # (le marqueur du SET précède celui du WHERE).
            delai, jid = params
            self.jobs[jid].update(
                status="pending", claim_token=None, available_in=delai
            )
            return 1
        return 0

    def fetch_one(self, sql: str, params: Any = ()) -> dict[str, Any] | None:
        if sql.startswith("SELECT id FROM"):  # candidate à réserver
            queue = params[0]
            for jid in sorted(self.jobs):
                job = self.jobs[jid]
                if (job["queue"] == queue and job["status"] == "pending"
                        and job["available_in"] <= 0):
                    return {"id": jid}
            return None
        if "claim_token=? AND status='running'" in sql:
            for jid in sorted(self.jobs):
                job = self.jobs[jid]
                if job["claim_token"] == params[0] and job["status"] == "running":
                    return {k: job[k] for k in ("id", "task", "payload", "attempts", "max_attempts")}
            return None
        if "COUNT(*)" in sql:
            n = sum(1 for j in self.jobs.values() if j["queue"] == params[0] and j["status"] == "pending")
            return {"n": n}
        if "last_error" in sql:
            job = self.jobs.get(params[0])
            if job is None:
                return None
            return {k: job[k] for k in ("id", "queue", "task", "status", "attempts", "max_attempts", "last_error")}
        return None


@pytest.fixture
def db() -> FakeDb:
    return FakeDb()


def test_enqueue_returns_id_and_serializes_payload(db: FakeDb) -> None:
    jid = enqueue("email.envoi", {"to": "x@y.fr"}, db=db)
    assert jid == 1
    assert json.loads(db.jobs[1]["payload"]) == {"to": "x@y.fr"}
    assert db.jobs[1]["task"] == "email.envoi" and db.jobs[1]["status"] == "pending"


@pytest.mark.parametrize("bad", ["", "   "])
def test_enqueue_empty_task_raises(db: FakeDb, bad: str) -> None:
    with pytest.raises(JobError):
        enqueue(bad, db=db)


def test_enqueue_bad_max_attempts_raises(db: FakeDb) -> None:
    with pytest.raises(JobError):
        enqueue("t", max_attempts=0, db=db)


def test_enqueue_non_json_payload_raises(db: FakeDb) -> None:
    with pytest.raises(JobError):
        enqueue("t", {"bad": object()}, db=db)  # type: ignore[dict-item]


def test_process_one_runs_handler_and_marks_done(db: FakeDb) -> None:
    seen: list[dict[str, Any]] = []
    enqueue("greet", {"name": "Alice"}, db=db)
    assert process_one({"greet": seen.append}, db=db) is True
    assert seen == [{"name": "Alice"}]
    assert db.jobs[1]["status"] == "done"


def test_process_one_empty_queue_returns_false(db: FakeDb) -> None:
    assert process_one({}, db=db) is False


def test_unknown_task_is_failed(db: FakeDb) -> None:
    enqueue("inconnue", db=db)
    assert process_one({}, db=db) is True
    assert db.jobs[1]["status"] == "failed" and "inconnue" in db.jobs[1]["last_error"]


def test_handler_failure_retries_then_fails(db: FakeDb) -> None:
    def boom(_payload: dict[str, Any]) -> None:
        raise RuntimeError("oups")

    enqueue("boom", max_attempts=2, db=db)
    process_one({"boom": boom}, db=db)        # tentative 1 -> reprise
    assert db.jobs[1]["status"] == "pending" and db.jobs[1]["attempts"] == 1

    # JOBS-STALE-RECLAIM-001 : la reprise n'est plus immédiate. Sans délai, une
    # tâche qui échoue vite consommait toutes ses tentatives en une fraction de
    # seconde, ce qui ne laissait aucune chance à une panne passagère.
    assert db.jobs[1]["available_in"] == 10
    assert process_one({"boom": boom}, db=db) is False, "le délai doit être respecté"

    db.jobs[1]["available_in"] = 0            # le temps passe
    process_one({"boom": boom}, db=db)        # tentative 2 -> failed
    assert db.jobs[1]["status"] == "failed" and "oups" in db.jobs[1]["last_error"]


def test_drain_processes_all_available(db: FakeDb) -> None:
    for i in range(3):
        enqueue("noop", {"i": i}, db=db)
    assert drain({"noop": lambda _p: None}, db=db) == 3
    assert all(j["status"] == "done" for j in db.jobs.values())


def test_pending_count_and_get_job(db: FakeDb) -> None:
    enqueue("a", db=db)
    enqueue("b", db=db)
    assert pending_count(db=db) == 2
    job = get_job(1, db=db)
    assert job is not None and job.task == "a" and job.status == "pending"
    assert get_job(999, db=db) is None
