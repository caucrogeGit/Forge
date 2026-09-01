# pyright: strict
"""Application d'une transition, avec points d'accroche (WORKFLOW-HOOKS-001).

Le paquet savait dire si une transition est **permise**, jamais l'appliquer.
Chaque application réécrivait donc le même enchaînement à la main : vérifier,
agir avant, écrire, agir après. Rien ne garantissait l'ordre, et rien
n'empêchait d'appeler l'action d'après quand celle d'avant avait refusé.

`apply_transition` orchestre cet ordre, et rien d'autre. Le paquet ne persiste
toujours rien : c'est l'appelant qui fournit l'écriture, et lui seul sait où
son statut est rangé.

## Ce que le veto veut dire

Un point d'accroche « avant » qui lève **empêche** la transition. Ni l'écriture
ni l'accroche « après » n'ont lieu, et l'exception remonte telle quelle. C'est
ce qui donne sa valeur au mécanisme : une règle métier peut refuser, et son
refus est visible.

Un point d'accroche « après » qui lève ne défait rien. L'écriture a eu lieu, et
prétendre le contraire en avalant l'exception cacherait un état déjà changé.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .transitions import WorkflowTransition, WorkflowTransitionError, can_transition

__all__ = [
    "TransitionEvent",
    "TransitionHook",
    "TransitionCommit",
    "apply_transition",
]


@dataclass(frozen=True)
class TransitionEvent:
    """Ce qui est transmis aux points d'accroche.

    `context` est libre : le paquet n'y touche pas et ne sait pas ce qu'il
    contient. L'application y range ce dont ses règles ont besoin, l'objet
    concerné ou l'auteur du geste par exemple.
    """

    from_status: str
    to_status: str
    context: dict[str, Any] = field(default_factory=dict[str, Any])


#: Un point d'accroche reçoit l'événement et ne rend rien. Pour refuser une
#: transition, il lève : un booléen de retour obligerait à inventer un message
#: d'erreur à sa place, alors que l'exception porte déjà le sien.
TransitionHook = Callable[[TransitionEvent], None]

#: L'écriture du nouveau statut, fournie par l'application.
TransitionCommit = Callable[[TransitionEvent], None]


def apply_transition(
    transitions: list[WorkflowTransition],
    from_status: str,
    to_status: str,
    *,
    before: "TransitionHook | None" = None,
    commit: "TransitionCommit | None" = None,
    after: "TransitionHook | None" = None,
    context: "dict[str, Any] | None" = None,
) -> str:
    """Applique une transition dans l'ordre, et rend le statut atteint.

    L'ordre est le suivant, et chaque étape conditionne la suivante.

    1. La transition est vérifiée contre `transitions`.
    2. `before` est appelé. S'il lève, tout s'arrête ici.
    3. `commit` est appelé, s'il est fourni. C'est l'écriture de l'application.
    4. `after` est appelé.

    Sans `commit`, `after` suit immédiatement `before` : le paquet n'a alors
    aucun moyen de savoir si l'écriture a eu lieu, et le dire vaut mieux que de
    laisser croire à une garantie qui n'existe pas.

    Raises:
        WorkflowTransitionError: la transition n'est pas déclarée.
        Exception: celle qu'un point d'accroche ou l'écriture a levée, telle
            quelle. Le paquet n'en enveloppe aucune, un message maquillé
            faisant perdre la cause.
    """
    if not can_transition(transitions, from_status, to_status):
        raise WorkflowTransitionError(
            f"Transition non déclarée : '{from_status}' vers '{to_status}'."
        )

    evenement = TransitionEvent(
        from_status=from_status,
        to_status=to_status,
        context=dict(context or {}),
    )

    if before is not None:
        before(evenement)

    if commit is not None:
        commit(evenement)

    if after is not None:
        after(evenement)

    return evenement.to_status
