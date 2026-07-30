# pyright: strict
"""File de tâches de fond adossée à MariaDB, sans broker ni runtime async.

`forge-mvc-jobs` permet de déporter un travail lourd hors de la requête HTTP
(envoi d'emails en nombre, transcodage, génération de QR Codes, import massif).
Le modèle est volontairement simple et fidèle à Forge :

- une table `jobs` sert de file (le SQL reste visible) ;
- on **enfile** une tâche avec :func:`enqueue` (par exemple depuis un contrôleur) ;
- un **process worker séparé** la traite avec :func:`drain` ou :func:`run_worker`,
  en appelant un gestionnaire que l'application a explicitement enregistré.

Aucune dépendance lourde (pas de Celery ni de Redis), aucune boucle async : le
serveur web reste synchrone (WSGI). La réservation d'une tâche est atomique via
un `UPDATE ... ORDER BY id LIMIT 1` avec jeton de réservation, donc plusieurs
workers peuvent tourner sans se marcher dessus.

Limite assumée V1 : pas de reprise automatique d'une tâche restée `running`
après un crash worker (pas de délai de visibilité). La dépendance va de l'opt-in
vers le cœur, jamais l'inverse.
"""
from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from forge_mvc_jobs.errors import JobError

#: Nom de la table de file.
TABLE_NAME = "jobs"

#: Un gestionnaire de tâche : reçoit la charge utile (dict) désérialisée.
JobHandler = Callable[[dict[str, Any]], object]


def _dialect() -> Any:
    """Dialecte du backend actif, source des expressions non portables."""
    from core.database.backend import get_backend

    return get_backend().dialect


def _now() -> str:
    """Expression de l'instant courant, propre au backend (OPTIN-DML-DIALECT-001).

    `NOW()` était écrit en dur : mesuré, SQL Server et SQLite ne le connaissent
    pas, et la file de tâches y était inutilisable malgré une DDL déjà
    dialectale.
    """
    return _dialect().now_expression()


def _insert_sql() -> str:
    maintenant = _now()
    return (
        f"INSERT INTO {TABLE_NAME} (queue, task, payload, max_attempts, available_at) "
        f"VALUES (?, ?, ?, ?, {_dialect().interval_seconds_expression(maintenant)})"
    )


def _candidate_sql() -> str:
    """Prochaine tâche prête de la file, la plus ancienne d'abord.

    La réservation se fait ensuite en deux temps plutôt qu'en un
    `UPDATE ... ORDER BY ... LIMIT 1`, extension que seul MariaDB accepte. On
    choisit une candidate, puis on la réserve sous garde `status='pending'` :
    deux ouvriers qui visent la même ligne ne peuvent pas gagner tous les deux,
    le second voyant `rowcount` à zéro. Le motif n'ajoute rien au contrat, il
    réemploie `limit_clause()`, déjà dialectale.
    """
    return (
        f"SELECT id FROM {TABLE_NAME} "
        f"WHERE queue=? AND status='pending' AND available_at <= {_now()} "
        f"ORDER BY id {_dialect().limit_clause()}"
    )


def _claim_sql() -> str:
    return (
        f"UPDATE {TABLE_NAME} SET status='running', claim_token=?, "
        f"started_at={_now()}, attempts=attempts+1 "
        "WHERE id=? AND status='pending'"
    )


_SELECT_CLAIMED_SQL = (
    f"SELECT id, task, payload, attempts, max_attempts FROM {TABLE_NAME} "
    "WHERE claim_token=? AND status='running'"
)


def _done_sql() -> str:
    return (f"UPDATE {TABLE_NAME} SET status='done', finished_at={_now()}, "
            "claim_token=NULL WHERE id=?")


def _fail_sql() -> str:
    return (f"UPDATE {TABLE_NAME} SET status='failed', last_error=?, "
            f"finished_at={_now()}, claim_token=NULL WHERE id=?")


def _retry_sql() -> str:
    return (f"UPDATE {TABLE_NAME} SET status='pending', claim_token=NULL, "
            f"started_at=NULL, available_at={_now()} WHERE id=?")
_PENDING_COUNT_SQL = f"SELECT COUNT(*) AS n FROM {TABLE_NAME} WHERE queue=? AND status='pending'"
_SELECT_JOB_SQL = (
    f"SELECT id, queue, task, status, attempts, max_attempts, last_error FROM {TABLE_NAME} WHERE id=? LIMIT 1"
)


@dataclass(frozen=True)
class Job:
    """État d'une tâche, pour inspection."""

    id: int
    queue: str
    task: str
    status: str
    attempts: int
    max_attempts: int
    last_error: str | None


def _db_module() -> Any:
    import core.database.db as db  # noqa: PLC0415

    return db


def enqueue(
    task: str,
    payload: dict[str, Any] | None = None,
    *,
    queue: str = "default",
    max_attempts: int = 1,
    available_in: int = 0,
    db: Any = None,
) -> int:
    """Enfile une tâche `task` avec sa charge utile et renvoie son identifiant.

    `payload` est sérialisé en JSON. `max_attempts` borne les tentatives (une
    tâche qui échoue est re-mise en file tant que `attempts < max_attempts`).
    `available_in` retarde la disponibilité de N secondes (0 = immédiat). Lève
    :class:`JobError` si `task` est vide, `max_attempts < 1`, ou si `payload`
    n'est pas sérialisable en JSON.
    """
    if not task or not task.strip():
        raise JobError("Le nom de tâche ne peut pas être vide.")
    if max_attempts < 1:
        raise JobError(f"max_attempts doit être >= 1. Reçu : {max_attempts}.")
    try:
        payload_json = json.dumps(payload or {})
    except (TypeError, ValueError) as exc:
        raise JobError(f"Charge utile non sérialisable en JSON : {exc}") from exc
    return (db if db is not None else _db_module()).insert(
        _insert_sql(), (queue, task, payload_json, max_attempts, available_in)
    )


def process_one(handlers: Mapping[str, JobHandler], *, queue: str = "default", db: Any = None) -> bool:
    """Réserve et exécute une tâche disponible de `queue`. Renvoie `True` si une
    tâche a été traitée, `False` si la file est vide.

    En cas d'échec du gestionnaire, la tâche est re-mise en file si
    `attempts < max_attempts`, sinon marquée `failed`. Une tâche sans
    gestionnaire enregistré est marquée `failed`.
    """
    database = db if db is not None else _db_module()
    token = uuid4().hex
    candidate = database.fetch_one(_candidate_sql(), (queue, 1))
    if candidate is None:
        return False
    if not database.execute(_claim_sql(), (token, int(candidate["id"]))):
        # Un autre ouvrier a réservé cette ligne entre-temps : ce n'est pas une
        # file vide, mais on rend la main plutôt que de boucler ici.
        return False
    row = database.fetch_one(_SELECT_CLAIMED_SQL, (token,))
    if row is None:
        return False

    job_id = int(row["id"])
    task = str(row["task"])
    attempts = int(row["attempts"])
    max_attempts = int(row["max_attempts"])
    payload: dict[str, Any] = json.loads(row["payload"])

    handler = handlers.get(task)
    if handler is None:
        database.execute(_fail_sql(), (f"tâche inconnue : {task}", job_id))
        return True

    try:
        handler(payload)
    except Exception as exc:  # noqa: BLE001 — toute erreur du gestionnaire est rapportée
        if attempts < max_attempts:
            database.execute(_retry_sql(), (job_id,))
        else:
            database.execute(_fail_sql(), (str(exc), job_id))
        return True

    database.execute(_done_sql(), (job_id,))
    return True


def drain(
    handlers: Mapping[str, JobHandler],
    *,
    queue: str = "default",
    max_jobs: int | None = None,
    db: Any = None,
) -> int:
    """Traite les tâches disponibles de `queue` jusqu'à épuisement (ou `max_jobs`).

    Renvoie le nombre de tâches traitées. C'est une passe unique : pas d'attente.
    """
    processed = 0
    while max_jobs is None or processed < max_jobs:
        if not process_one(handlers, queue=queue, db=db):
            break
        processed += 1
    return processed


def run_worker(
    handlers: Mapping[str, JobHandler],
    *,
    queue: str = "default",
    poll_interval: float = 1.0,
    db: Any = None,
    stop: Callable[[], bool] | None = None,
) -> None:
    """Boucle de worker : vide la file, puis attend `poll_interval` si vide.

    L'application lance cette fonction depuis son propre point d'entrée (un
    script worker), en fournissant ses gestionnaires : le worker est donc une
    commande explicite, jamais déclenchée par la requête HTTP. `stop` est une
    condition d'arrêt optionnelle vérifiée à chaque cycle.
    """
    while True:
        if stop is not None and stop():
            return
        processed = drain(handlers, queue=queue, db=db)
        if processed == 0:
            time.sleep(poll_interval)


def pending_count(*, queue: str = "default", db: Any = None) -> int:
    """Nombre de tâches en attente dans `queue`."""
    row = (db if db is not None else _db_module()).fetch_one(_PENDING_COUNT_SQL, (queue,))
    return int(row["n"]) if row else 0


def get_job(job_id: int, *, db: Any = None) -> Job | None:
    """Renvoie l'état d'une tâche par son identifiant, ou `None` si absente."""
    row = (db if db is not None else _db_module()).fetch_one(_SELECT_JOB_SQL, (job_id,))
    if row is None:
        return None
    return Job(
        id=int(row["id"]),
        queue=str(row["queue"]),
        task=str(row["task"]),
        status=str(row["status"]),
        attempts=int(row["attempts"]),
        max_attempts=int(row["max_attempts"]),
        last_error=row["last_error"],
    )
