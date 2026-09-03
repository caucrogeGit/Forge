# pyright: strict
"""Table de l'historique des transitions (`WORKFLOW-HISTORY-001`).

Le paquet appliquait les transitions sans en garder trace : on savait dans quel
état une entité se trouve, jamais comment elle y est arrivée, ni quand, ni par
qui.

C'est pourtant la question qu'on pose à un workflow dès qu'un dossier pose
problème. « Qui a validé cette commande, et à quelle date » n'avait aucune
réponse, et chaque application réinventait sa table.

`forge workflow:init` rend cette description pour le backend installé et écrit
le SQL dans `mvc/migrations/`, où il reste relisible avant
`forge migration:apply` (charte §7, ADR-071).
"""
from __future__ import annotations

from core.database.table_ddl import Column, Index, TableDefinition

__all__ = ["WORKFLOW_HISTORY", "WORKFLOW_HISTORY_TABLE", "MIGRATIONS"]

WORKFLOW_HISTORY_TABLE = "workflow_history"

WORKFLOW_HISTORY = TableDefinition(
    name=WORKFLOW_HISTORY_TABLE,
    columns=[
        Column("id", "identity"),
        # Sur quoi porte la transition. Le couple est libre : le paquet ne sait
        # pas ce qu'est une entité de l'application, et ne cherche pas à le
        # savoir. Pas de clé étrangère non plus, pour la même raison, et parce
        # qu'un historique doit survivre à la suppression de son sujet.
        Column("entity_name", "string", length=100),
        Column("entity_id", "string", length=191),
        # `NULL` au départ : la toute première transition d'une entité vient
        # d'un état qui n'existait pas.
        Column("from_status", "string", length=64, nullable=True),
        Column("to_status", "string", length=64),
        # Qui. `NULL` est une information et non un manque : une transition
        # automatique, déclenchée par une tâche de fond, n'a pas d'auteur, et
        # inventer « system » masquerait la différence.
        Column("actor_kind", "string", length=64, nullable=True),
        Column("actor_id", "string", length=191, nullable=True),
        # Pourquoi. Un motif de refus, une note de validation.
        Column("comment", "text", nullable=True),
        Column("created_at", "datetime", default_now=True),
    ],
    primary_key=["id"],
    indexes=[
        # La question la plus fréquente : l'historique d'une entité donnée.
        Index("idx_workflow_history_entity", ("entity_name", "entity_id")),
        Index("idx_workflow_history_created", "created_at"),
    ],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260903100000_create_workflow_history.sql", WORKFLOW_HISTORY),
]
