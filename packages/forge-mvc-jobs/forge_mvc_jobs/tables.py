# pyright: strict
"""Table de la file de tâches de fond, décrite une fois pour les quatre backends.

Remplace le fichier SQL figé que ce paquet livrait, inexécutable ailleurs que
sur MariaDB (audit `OPTIN-DDL-DIALECT-AUDIT-001`). `forge jobs:init` rend
désormais cette description pour le backend installé et écrit le SQL dans
`mvc/migrations/`, où il reste relisible avant `forge migration:apply`
(charte §7, ADR-071).
"""
from __future__ import annotations

from core.database.table_ddl import Column, Index, TableDefinition

__all__ = ["JOBS", "MIGRATIONS"]

JOBS = TableDefinition(
    name="jobs",
    columns=[
        Column("id", "identity"),
        Column("queue", "string", length=191, default="default"),
        Column("task", "string", length=191),
        Column("payload", "text"),
        Column("status", "string", length=16, default="pending"),
        Column("attempts", "integer", default=0),
        Column("max_attempts", "integer", default=1),
        Column("available_at", "datetime", default_now=True),
        Column("last_error", "text", nullable=True),
        Column("claim_token", "string", length=64, nullable=True),
        Column("created_at", "datetime", default_now=True),
        Column("started_at", "datetime", nullable=True),
        Column("finished_at", "datetime", nullable=True),
    ],
    primary_key=["id"],
    indexes=[Index("idx_jobs_claim", ("queue", "status", "available_at"))],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260626140000_create_jobs.sql", JOBS),
]
