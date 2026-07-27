# pyright: strict
"""Table de journal d'audit applicatif, décrite une fois pour les quatre backends.

Remplace le fichier SQL figé que ce paquet livrait, inexécutable ailleurs que
sur MariaDB (audit `OPTIN-DDL-DIALECT-AUDIT-001`). `forge audit:init` rend
désormais cette description pour le backend installé et écrit le SQL dans
`mvc/migrations/`, où il reste relisible avant `forge migration:apply`
(charte §7, ADR-071).
"""
from __future__ import annotations

from core.database.table_ddl import Column, Index, TableDefinition

__all__ = ["AUDIT_LOG", "MIGRATIONS"]

AUDIT_LOG = TableDefinition(
    name="audit_log",
    columns=[
        Column("id", "identity"),
        Column("actor", "string", length=191, nullable=True),
        Column("action", "string", length=191),
        Column("target_type", "string", length=191, nullable=True),
        Column("target_id", "string", length=191, nullable=True),
        Column("details", "text", nullable=True),
        Column("created_at", "datetime", default_now=True),
    ],
    primary_key=["id"],
    indexes=[
        Index("idx_audit_action", "action"),
        Index("idx_audit_target", ("target_type", "target_id")),
        Index("idx_audit_created", "created_at"),
    ],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260626130000_create_audit_log.sql", AUDIT_LOG),
]
