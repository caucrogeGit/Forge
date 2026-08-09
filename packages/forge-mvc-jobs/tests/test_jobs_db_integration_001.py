"""Intégration de la file de jobs sur les trois serveurs (JOBS-DB-INTEGRATION-001).

Vérifie la mécanique réelle face au moteur : la DDL rendue, la réservation
atomique, l'exécution, la reprise sur échec, la disponibilité différée
(`available_in`) et la reprise des tâches orphelines.

## Ce qui a changé (`TEST-PACKAGE-INTEGRATION-REAL-LAYER-001`)

Ce fichier montait sa propre connexion MariaDB dans un adaptateur écrit à la
main. Il ne tournait donc que sur MariaDB, et court-circuitait la vraie couche
d'accès `core.database.db`, celle que l'application utilise en production.
Les tests passent désormais par `real_backend_db` : chacun s'exécute trois
fois, une par serveur, à travers la couche réelle.

Ses trois helpers écrivaient `NOW()` et `INTERVAL ? SECOND`, les constructions
mêmes que le relevé de portabilité bannit. Le vieillissement d'une réservation
lit maintenant l'heure **au serveur** et soustrait en Python, ce qui évite à la
fois l'arithmétique dialectale et le piège de l'intervalle négatif, que SQLite
rend en `NULL` sans rien signaler.
"""
from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta
from typing import Any

import pytest

pytest.importorskip("forge_mvc_jobs")

from forge_mvc_jobs import (
    drain,
    enqueue,
    get_job,
    pending_count,
    process_one,
)

from forge_mvc_testing.real_db import tables_temporaires


@pytest.fixture
def jobs_db(real_backend_db: str) -> Iterator[Any]:
    """Table des tâches créée par sa DDL dialectale, sur le serveur du cas."""
    from forge_mvc_jobs.tables import JOBS

    with tables_temporaires(JOBS) as db:
        yield db


def _maintenant_au_serveur(db: Any) -> datetime:
    """L'heure vue par le moteur, dans son propre référentiel.

    Comparer une heure Python à une heure serveur suppose la même horloge et le
    même fuseau. SQL Server pose ses colonnes en UTC quand MariaDB reste sur
    l'heure locale du serveur : on lit donc l'heure là où elle sera comparée.
    """
    from core.database.backend import get_backend

    expression = get_backend().dialect.now_expression()
    ligne = db.fetch_one(f"SELECT {expression} AS maintenant", ())
    assert ligne is not None
    return ligne["maintenant"]


def _poser_reservation(db: Any, job_id: int, *, il_y_a: int) -> None:
    """Reproduit un worker qui meurt entre la réservation et le verdict.

    `il_y_a` recule `started_at` du nombre de secondes voulu, ce qui revient à
    laisser le temps passer sans l'attendre.
    """
    debut = _maintenant_au_serveur(db) - timedelta(seconds=il_y_a)
    db.execute(
        "UPDATE jobs SET status='running', claim_token='jeton-mort', "
        "started_at=?, attempts=attempts+1 WHERE id=?",
        (debut, job_id),
    )


def _rendre_disponible(db: Any, job_id: int) -> None:
    """Annule le délai croissant d'une remise en file, pour ne pas l'attendre."""
    db.execute(
        "UPDATE jobs SET available_at = ? WHERE id = ?",
        (_maintenant_au_serveur(db), job_id),
    )


def test_enqueue_then_drain_runs_handler(jobs_db: Any) -> None:
    seen: list[dict[str, Any]] = []
    enqueue("greet", {"name": "Alice"})
    enqueue("greet", {"name": "Bob"})
    assert drain({"greet": seen.append}) == 2
    assert {d["name"] for d in seen} == {"Alice", "Bob"}
    assert pending_count() == 0


def test_done_status_is_persisted(jobs_db: Any) -> None:
    jid = enqueue("noop")
    drain({"noop": lambda _p: None})
    job = get_job(jid)
    assert job is not None and job.status == "done"


def test_failure_retries_then_fails(jobs_db: Any) -> None:
    def boom(_p: dict[str, Any]) -> None:
        raise RuntimeError("oups")

    jid = enqueue("boom", max_attempts=2)
    assert process_one({"boom": boom}) is True
    assert get_job(jid).status == "pending"  # re-mise en file

    # JOBS-STALE-RECLAIM-001 : la remise en file porte un délai croissant, donc
    # la tâche n'est pas immédiatement reprise. On avance l'horloge de la file
    # plutôt que d'attendre, puis on vérifie la seconde tentative.
    assert process_one({"boom": boom}) is False, "le délai doit être respecté"
    _rendre_disponible(jobs_db, jid)

    assert process_one({"boom": boom}) is True
    failed = get_job(jid)
    assert failed.status == "failed" and "oups" in failed.last_error


def test_unknown_task_is_failed(jobs_db: Any) -> None:
    jid = enqueue("inconnue")
    process_one({})
    assert get_job(jid).status == "failed"


def test_available_in_delays_the_job(jobs_db: Any) -> None:
    enqueue("later", available_in=3600)
    # Le job n'est pas encore disponible : drain ne le réserve pas.
    assert drain({"later": lambda _p: None}) == 0
    assert pending_count() == 1


def test_empty_queue_process_one_false(jobs_db: Any) -> None:
    assert process_one({}) is False


def test_la_lecture_unitaire_traverse_le_moteur(jobs_db: Any) -> None:
    """`get_job` portait un `LIMIT 1` qui le cassait sur SQL Server.

    Il figurait pourtant dans ce fichier, mais seul MariaDB l'exerçait
    (`ADMIN-JOBS-LIMIT-PORTABLE-001`).
    """
    jid = enqueue("lecture", {"x": 1}, queue="q", max_attempts=3)
    lu = get_job(jid)
    assert lu is not None
    assert (lu.task, lu.queue, lu.status) == ("lecture", "q", "pending")
    assert get_job(jid + 10_000) is None


# ── Reprise des tâches orphelines (JOBS-STALE-RECLAIM-001) ───────────────────


def test_une_tache_orpheline_repart_en_file(jobs_db: Any) -> None:
    """LE test du ticket : sans reprise, elle restait 'running' pour toujours."""
    from forge_mvc_jobs.queue import get_job, reclaim_stale

    job_id = enqueue("lent", {"x": 1}, max_attempts=3)
    _poser_reservation(jobs_db, job_id, il_y_a=1000)

    effet = reclaim_stale(lease_seconds=900)

    assert (effet.requeued, effet.failed) == (1, 0)
    reprise = get_job(job_id)
    assert reprise is not None
    assert reprise.status == "pending"


def test_une_tache_orpheline_sans_tentative_restante_part_en_echec(
    jobs_db: Any,
) -> None:
    from forge_mvc_jobs.queue import RECLAIM_FAILURE_MESSAGE, get_job, reclaim_stale

    job_id = enqueue("lent", {}, max_attempts=1)
    _poser_reservation(jobs_db, job_id, il_y_a=1000)

    effet = reclaim_stale(lease_seconds=900)

    assert (effet.requeued, effet.failed) == (0, 1)
    echouee = get_job(job_id)
    assert echouee is not None
    assert echouee.status == "failed"
    assert echouee.last_error == RECLAIM_FAILURE_MESSAGE


def test_une_tache_dans_son_bail_n_est_pas_reprise(jobs_db: Any) -> None:
    """Le point qui fait la différence entre une reprise et un doublon."""
    from forge_mvc_jobs.queue import get_job, reclaim_stale

    job_id = enqueue("lent", {}, max_attempts=3)
    _poser_reservation(jobs_db, job_id, il_y_a=60)

    effet = reclaim_stale(lease_seconds=900)

    assert effet.total == 0
    intacte = get_job(job_id)
    assert intacte is not None
    assert intacte.status == "running"


def test_une_tache_en_attente_n_est_jamais_reprise(jobs_db: Any) -> None:
    """`started_at IS NULL` désigne une tâche jamais réservée, pas une orpheline."""
    from forge_mvc_jobs.queue import get_job, reclaim_stale

    job_id = enqueue("jamais_prise", {})

    assert reclaim_stale(lease_seconds=1).total == 0
    attente = get_job(job_id)
    assert attente is not None
    assert attente.status == "pending"


def test_la_reprise_ne_touche_pas_les_autres_files(jobs_db: Any) -> None:
    from forge_mvc_jobs.queue import get_job, reclaim_stale

    job_id = enqueue("lent", {}, queue="emails", max_attempts=3)
    _poser_reservation(jobs_db, job_id, il_y_a=1000)

    assert reclaim_stale(queue="default", lease_seconds=900).total == 0
    assert reclaim_stale(queue="emails", lease_seconds=900).requeued == 1
    reprise = get_job(job_id)
    assert reprise is not None
    assert reprise.status == "pending"


def test_une_tache_reprise_redevient_traitable(jobs_db: Any) -> None:
    """La reprise doit rendre la tâche au circuit normal, pas seulement au statut.

    Elle repart avec un délai croissant : on l'annule pour vérifier que le
    worker la reprend bien ensuite.
    """
    from forge_mvc_jobs.queue import get_job, reclaim_stale

    vues: list[dict[str, Any]] = []
    job_id = enqueue("lent", {"x": 7}, max_attempts=3)
    _poser_reservation(jobs_db, job_id, il_y_a=1000)
    reclaim_stale(lease_seconds=900)

    _rendre_disponible(jobs_db, job_id)
    traitees = drain({"lent": lambda p: vues.append(p)})

    assert traitees == 1
    assert vues == [{"x": 7}]
    finie = get_job(job_id)
    assert finie is not None
    assert finie.status == "done"
