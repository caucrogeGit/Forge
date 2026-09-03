# pyright: strict
"""Historique des transitions (`WORKFLOW-HISTORY-001`).

Le SQL reste **visible** ici ; l'exécution est déléguée à un accès injectable,
ce qui rend le module testable sans base réelle et laisse l'application décider
de sa transaction.

## L'enregistrement est explicite

`apply_transition` n'écrit rien de soi même. L'application enregistre quand
elle le veut, dans **sa** transaction, avec l'écriture du nouvel état.

Écrire depuis le paquet imposerait une connexion à un module qui n'en avait pas
besoin, et surtout séparerait l'historique de l'écriture qu'il décrit : une
transaction annulée laisserait une ligne d'historique pour une transition qui
n'a pas eu lieu.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from forge_mvc_workflow.tables import WORKFLOW_HISTORY_TABLE

__all__ = [
    "WorkflowHistoryError",
    "TransitionRecord",
    "record_transition",
    "history_for",
    "last_transition",
    "INSERT_SQL",
]

INSERT_SQL = (
    f"INSERT INTO {WORKFLOW_HISTORY_TABLE} "
    "(entity_name, entity_id, from_status, to_status, actor_kind, actor_id, "
    "comment, created_at) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
)
_SELECT_SQL = (
    "SELECT id, entity_name, entity_id, from_status, to_status, actor_kind, "
    f"actor_id, comment, created_at FROM {WORKFLOW_HISTORY_TABLE} "
    "WHERE entity_name = ? AND entity_id = ? ORDER BY id DESC"
)


class WorkflowHistoryError(ValueError):
    """Entrée d'historique invalide."""


class _Db(Protocol):
    def execute(self, sql: str, params: "tuple[Any, ...]") -> Any: ...
    def fetch_all(
        self, sql: str, params: "tuple[Any, ...]"
    ) -> "list[dict[str, Any]]": ...


@dataclass(frozen=True)
class TransitionRecord:
    """Une transition passée, telle qu'un écran d'historique la rend."""

    from_status: "str | None"
    to_status: str
    actor_kind: "str | None" = None
    actor_id: "str | None" = None
    comment: "str | None" = None
    created_at: "datetime | None" = None

    @property
    def is_automatic(self) -> bool:
        """Vrai si la transition n'a pas d'auteur.

        Une transition automatique n'en a pas, et c'est une **information** :
        inventer « system » la ferait passer pour un geste humain.
        """
        return self.actor_id is None

    @property
    def is_initial(self) -> bool:
        """Vrai s'il s'agit de la première transition, venue d'aucun état."""
        return self.from_status is None


def _texte(valeur: object, quoi: str, *, obligatoire: bool = True) -> "str | None":
    if valeur is None:
        if obligatoire:
            raise WorkflowHistoryError(f"{quoi} est obligatoire.")
        return None
    texte = str(valeur).strip()
    if not texte:
        if obligatoire:
            raise WorkflowHistoryError(f"{quoi} ne peut pas être vide.")
        return None
    return texte


def record_transition(
    entity_name: str,
    entity_id: object,
    to_status: str,
    *,
    from_status: "str | None" = None,
    actor_kind: "str | None" = None,
    actor_id: object = None,
    comment: "str | None" = None,
    db: "_Db | None" = None,
    now: "datetime | None" = None,
) -> None:
    """Enregistre une transition.

    À appeler dans la **même transaction** que l'écriture du nouvel état :
    séparer les deux laisserait une ligne d'historique pour une transition
    annulée, ou l'inverse.

    Raises:
        WorkflowHistoryError: entité ou état d'arrivée manquants, ou couple
            acteur incomplet.
    """
    nom = _texte(entity_name, "entity_name")
    identifiant = _texte(entity_id, "entity_id")
    arrivee = _texte(to_status, "to_status")
    depart = _texte(from_status, "from_status", obligatoire=False)

    nature = _texte(actor_kind, "actor_kind", obligatoire=False)
    acteur = _texte(actor_id, "actor_id", obligatoire=False)
    if (nature is None) != (acteur is None):
        raise WorkflowHistoryError(
            "actor_kind et actor_id vont de pair : fournir les deux, ou aucun. "
            "Un identifiant sans nature ne désigne personne."
        )

    acces = db if db is not None else _defaut()
    acces.execute(
        INSERT_SQL,
        (
            nom, identifiant, depart, arrivee, nature, acteur,
            _texte(comment, "comment", obligatoire=False),
            now or datetime.now(UTC).replace(tzinfo=None),
        ),
    )


def history_for(
    entity_name: str, entity_id: object, *, db: "_Db | None" = None
) -> "list[TransitionRecord]":
    """Historique d'une entité, du plus récent au plus ancien.

    Trié par identifiant décroissant et non par date : deux transitions de la
    même seconde se départageraient sinon au hasard, et l'ordre d'un historique
    est ce qu'on vient y lire.
    """
    nom = _texte(entity_name, "entity_name")
    identifiant = _texte(entity_id, "entity_id")
    acces = db if db is not None else _defaut()
    return [
        TransitionRecord(
            from_status=_lire(ligne.get("from_status")),
            to_status=str(ligne.get("to_status") or ""),
            actor_kind=_lire(ligne.get("actor_kind")),
            actor_id=_lire(ligne.get("actor_id")),
            comment=_lire(ligne.get("comment")),
            created_at=ligne.get("created_at"),
        )
        for ligne in acces.fetch_all(_SELECT_SQL, (nom, identifiant))
    ]


def last_transition(
    entity_name: str, entity_id: object, *, db: "_Db | None" = None
) -> "TransitionRecord | None":
    """Dernière transition connue, ou `None` si l'entité n'a pas d'historique."""
    entrees = history_for(entity_name, entity_id, db=db)
    return entrees[0] if entrees else None


def _lire(valeur: object) -> "str | None":
    return None if valeur is None else str(valeur)


def _defaut() -> "_Db":
    from core.database import db

    return db  # pyright: ignore[reportReturnType]
