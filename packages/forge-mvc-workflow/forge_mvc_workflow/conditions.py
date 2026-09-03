# pyright: strict
"""Conditions de transition (`WORKFLOW-CONDITIONS-001`).

`can_transition` répond à une seule question : cette transition est elle
**déclarée** ? Elle ne peut pas répondre à « cette commande a t elle au moins
une ligne », ni à « ce dossier a t il été relu », qui sont pourtant les vraies
conditions d'un passage d'état.

L'application les vérifiait donc avant d'appeler, chacune à sa façon, et la
règle vivait dans les contrôleurs plutôt que dans le workflow. Deux chemins
menant au même état s'oubliaient l'un l'autre, et le second passait sans
contrôle.

## Une condition dit pourquoi elle refuse

Une condition qui rendrait `False` laisserait l'utilisateur devant « transition
impossible », message qui n'indique rien à corriger. Elle rend donc soit `None`
pour accepter, soit un **motif**, qui remonte jusqu'à l'écran.

## Une condition qui échoue refuse la transition

Une condition qui lève ne dit **pas** que la transition est permise, elle ne
dit rien. Traiter ce silence comme une autorisation est la faute classique de
ce genre de branchement, et elle est ici particulièrement coûteuse : le jour
où le service qu'interroge la condition tombe, toutes les transitions passent.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from forge_mvc_workflow.transitions import WorkflowTransitionError

__all__ = [
    "ConditionResult",
    "TransitionCondition",
    "register_condition",
    "unregister_condition",
    "registered_conditions",
    "clear_conditions",
    "check_conditions",
    "ensure_conditions",
]

logger = logging.getLogger("forge.workflow")

#: Une condition reçoit le couple d'états et le contexte, et rend `None` pour
#: accepter, ou un motif de refus.
TransitionCondition = Callable[[str, str, "dict[str, Any]"], "str | None"]


@dataclass(frozen=True)
class ConditionResult:
    """Verdict de l'ensemble des conditions applicables."""

    allowed: bool
    reasons: "tuple[str, ...]" = ()

    @property
    def reason(self) -> str:
        """Motifs réunis en une phrase, pour un message d'écran."""
        return " ".join(self.reasons)


#: Conditions enregistrées, indexées par couple d'états. `None` en clé de départ
#: ou d'arrivée signifie « quel que soit cet état ».
_conditions: "dict[tuple[str | None, str | None], list[TransitionCondition]]" = {}


def register_condition(
    condition: TransitionCondition,
    *,
    from_status: "str | None" = None,
    to_status: "str | None" = None,
) -> None:
    """Enregistre une condition.

    Sans `from_status` ni `to_status`, la condition s'applique à **toutes** les
    transitions. Avec l'un des deux, elle s'applique à celles qui le portent :
    « rien ne sort de brouillon sans relecture » se déclare une fois, plutôt
    qu'une fois par transition sortante.

    Plusieurs conditions cohabitent, et **toutes** doivent accepter. Une règle
    métier s'ajoute, elle ne se remplace pas.
    """
    if not callable(condition):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(f"Une condition doit être appelable. Reçu : {condition!r}.")
    cle = (from_status, to_status)
    liste = _conditions.setdefault(cle, [])
    if condition not in liste:
        liste.append(condition)


def unregister_condition(
    condition: TransitionCondition,
    *,
    from_status: "str | None" = None,
    to_status: "str | None" = None,
) -> bool:
    """Retire une condition. Vrai si elle était enregistrée."""
    liste = _conditions.get((from_status, to_status))
    if liste and condition in liste:
        liste.remove(condition)
        return True
    return False


def registered_conditions(
    from_status: str, to_status: str
) -> "tuple[TransitionCondition, ...]":
    """Conditions applicables à une transition, dans l'ordre de consultation.

    De la plus générale à la plus précise : une règle globale s'applique avant
    une règle propre au couple, de sorte qu'un refus général l'emporte sans
    qu'une règle précise ait à le répéter.
    """
    cles = (
        (None, None),
        (from_status, None),
        (None, to_status),
        (from_status, to_status),
    )
    retenues: list[TransitionCondition] = []
    for cle in cles:
        for condition in _conditions.get(cle, []):
            if condition not in retenues:
                retenues.append(condition)
    return tuple(retenues)


def clear_conditions() -> None:
    """Retire toutes les conditions. Utile aux tests."""
    _conditions.clear()


def check_conditions(
    from_status: str, to_status: str, context: "dict[str, Any] | None" = None
) -> ConditionResult:
    """Consulte les conditions applicables. Ne lève jamais.

    Sert à **afficher** ce qui bloque, par exemple pour griser un bouton et
    dire pourquoi. `ensure_conditions` sert à refuser.

    Une condition qui lève, ou qui rend autre chose qu'une chaîne ou `None`,
    fait **refuser** la transition. Le jour où le service qu'elle interroge
    tombe, toutes les transitions passeraient sinon.
    """
    donnees = dict(context or {})
    motifs: list[str] = []
    for condition in registered_conditions(from_status, to_status):
        try:
            verdict = condition(from_status, to_status, donnees)
        except Exception as exc:
            logger.exception(
                "Forge Workflow - condition en échec, transition refusée par "
                "précaution (%s vers %s)", from_status, to_status,
            )
            motifs.append(f"une condition n'a pas pu être évaluée : {exc}")
            break
        if verdict is None:
            continue
        if not isinstance(verdict, str):  # pyright: ignore[reportUnnecessaryIsInstance]
            logger.warning(
                "Forge Workflow - une condition a rendu %r au lieu d'un motif "
                "ou de None ; transition refusée par précaution.", verdict,
            )
            motifs.append("une condition a rendu un verdict illisible")
            break
        motifs.append(verdict)
        break
    return ConditionResult(allowed=not motifs, reasons=tuple(motifs))


def ensure_conditions(
    from_status: str, to_status: str, context: "dict[str, Any] | None" = None
) -> None:
    """Refuse la transition si une condition s'y oppose.

    Raises:
        WorkflowTransitionError: le message porte le **motif** rendu par la
            condition. « Transition impossible » n'indique rien à corriger.
    """
    resultat = check_conditions(from_status, to_status, context)
    if not resultat.allowed:
        raise WorkflowTransitionError(
            f"Transition '{from_status}' vers '{to_status}' refusée : "
            f"{resultat.reason}"
        )
