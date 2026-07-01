# pyright: strict
"""forge-mvc-jobs — file de tâches de fond opt-in (JOBS-OPTIN-SCAFFOLD-001).

Déporter un travail lourd hors de la requête HTTP, via une file adossée à
MariaDB et un worker explicite. On enfile avec `enqueue` (depuis un contrôleur),
on traite dans un process séparé avec `drain` ou `run_worker`, qui appellent les
gestionnaires que l'application a enregistrés.

Pas de broker, pas de Celery/Redis, pas de runtime async : le serveur web reste
synchrone. La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
"""
from forge_mvc_jobs.errors import JobError
from forge_mvc_jobs.queue import (
    CREATE_TABLE_SQL,
    TABLE_NAME,
    Job,
    JobHandler,
    drain,
    enqueue,
    get_job,
    pending_count,
    process_one,
    run_worker,
)

__version__ = "1.0.0rc2"

__all__ = [
    "JobError",
    "Job",
    "JobHandler",
    "TABLE_NAME",
    "CREATE_TABLE_SQL",
    "enqueue",
    "process_one",
    "drain",
    "run_worker",
    "pending_count",
    "get_job",
]
