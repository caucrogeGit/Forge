# pyright: strict
"""Journal d'audit applicatif persisté dans MariaDB, borné et explicite.

`forge-mvc-audit` enregistre des actions importantes de l'application (élève
créé, note modifiée, QCM corrigé, utilisateur connecté, rôle changé, fichier
supprimé) dans une table `audit_log`. L'API est explicite : on écrit avec
:func:`record_audit`, on relit avec :func:`get_audit_log`. Le SQL reste visible.

Périmètre volontairement borné : c'est un **audit applicatif**, pas un SIEM de
cybersécurité. Cohérent avec ADR-008 : Forge fournit la table et le helper, la
décision de tracer reste applicative. La dépendance va de l'opt-in vers le cœur.

La table n'est PAS créée automatiquement : la migration fournie par le paquet
doit avoir été appliquée (voir `forge audit:init` puis `forge migration:apply`).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from forge_mvc_audit.errors import AuditError

#: Nom de la table d'audit.
TABLE_NAME = "audit_log"

#: Plafond strict du nombre de lignes lues d'un coup.
MAX_LIMIT = 1000


_INSERT_SQL = (
    f"INSERT INTO {TABLE_NAME} (actor, action, target_type, target_id, details) "
    "VALUES (?, ?, ?, ?, ?)"
)
# Colonnes filtrables : liste blanche stricte (jamais d'entrée utilisateur dans le SQL).
_FILTERABLE = ("actor", "action", "target_type", "target_id")
_SELECT_COLUMNS = "id, actor, action, target_type, target_id, details, created_at"


@dataclass(frozen=True)
class AuditEntry:
    """Une entrée d'audit lue depuis la table."""

    id: int
    actor: str | None
    action: str
    target_type: str | None
    target_id: str | None
    details: str | None
    created_at: str


def _db_module() -> Any:
    import core.database.db as db  # noqa: PLC0415

    return db


def record_audit(
    action: str,
    *,
    actor: str | None = None,
    target_type: str | None = None,
    target_id: str | int | None = None,
    details: str | None = None,
    db: Any = None,
) -> int:
    """Enregistre une action d'audit et renvoie l'identifiant de la ligne.

    `action` est obligatoire (par exemple ``"eleve.cree"`` ou ``"note.modifiee"``).
    `actor` est l'auteur (identifiant ou login), `target_type`/`target_id`
    désignent l'objet visé, `details` est un complément libre. Lève
    :class:`AuditError` si `action` est vide.
    """
    if not action or not action.strip():
        raise AuditError("L'action d'audit ne peut pas être vide.")
    target = None if target_id is None else str(target_id)
    return (db if db is not None else _db_module()).insert(
        _INSERT_SQL, (actor, action, target_type, target, details)
    )


def get_audit_log(
    *,
    limit: int = 100,
    actor: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    target_id: str | int | None = None,
    db: Any = None,
) -> list[AuditEntry]:
    """Renvoie les entrées d'audit les plus récentes, filtrables.

    `limit` est borné à :data:`MAX_LIMIT`. Les filtres fournis (non ``None``)
    sont combinés en ``AND`` sur des colonnes en liste blanche. Lève
    :class:`AuditError` si `limit` est négatif ou nul.
    """
    if limit < 1:
        raise AuditError(f"limit doit être >= 1. Reçu : {limit}.")
    limit = min(limit, MAX_LIMIT)

    filters: dict[str, str] = {}
    if actor is not None:
        filters["actor"] = actor
    if action is not None:
        filters["action"] = action
    if target_type is not None:
        filters["target_type"] = target_type
    if target_id is not None:
        filters["target_id"] = str(target_id)

    clauses: list[str] = []
    params: list[object] = []
    for column, value in filters.items():
        if column not in _FILTERABLE:  # garde-fou : jamais de colonne hors liste blanche
            raise AuditError(f"Filtre interdit : {column}")
        clauses.append(f"{column} = ?")
        params.append(value)

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT {_SELECT_COLUMNS} FROM {TABLE_NAME}{where} ORDER BY id DESC LIMIT ?"
    params.append(limit)

    rows = (db if db is not None else _db_module()).fetch_all(sql, params)
    return [
        AuditEntry(
            id=int(row["id"]),
            actor=row["actor"],
            action=str(row["action"]),
            target_type=row["target_type"],
            target_id=row["target_id"],
            details=row["details"],
            created_at=str(row["created_at"]),
        )
        for row in rows
    ]
