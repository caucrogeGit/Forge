# pyright: strict
"""Validation métier déclarable (`ENTITIES-BUSINESS-VALIDATION-001`).

Le contrat d'entité décrit des **types** et des contraintes de forme, longueur
minimale, motif, bornes numériques. Il ne peut rien dire de « la date de fin
doit suivre la date de début », ni de « une remise au delà de trente pour cent
demande une validation », qui sont pourtant les règles qui comptent.

Elles vivaient donc dans les contrôleurs, réécrites à chaque point d'entrée.
Une entité créée par l'écran passait le contrôle ; la même créée par un import
CSV ou par une commande ne le passait pas, et rien ne le signalait.

## Pourquoi une fonction enregistrée, et non une expression au contrat

Une règle métier a besoin de la base, de l'heure, parfois d'un service. Une
mini-langue d'expressions dans le JSON en couvrirait un dixième et demanderait
un interpréteur, que le principe 3 refuse : du code caché dans de la donnée.

Une fonction Python est lisible, testable et déboguable. Le contrat déclare
qu'une entité **a** des règles ; le code dit lesquelles.

## Un validateur qui échoue refuse l'écriture

Un validateur qui lève ne dit **pas** que la donnée est valide, il ne dit rien.
Le jour où le service qu'il interroge tombe, tout passerait.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast

__all__ = [
    "EntityValidationError",
    "ValidationIssue",
    "ValidationReport",
    "EntityValidator",
    "register_entity_validator",
    "unregister_entity_validator",
    "registered_validators",
    "clear_entity_validators",
    "validate_entity_data",
    "ensure_entity_data",
]

logger = logging.getLogger("forge.entities")

#: Un validateur reçoit les données nettoyées et le contexte, et rend une liste
#: de problèmes. Une liste vide vaut acceptation.
EntityValidator = Callable[["dict[str, Any]", "dict[str, Any]"], "list[ValidationIssue] | None"]


class EntityValidationError(ValueError):
    """Les données ne satisfont pas les règles métier."""

    def __init__(self, report: "ValidationReport") -> None:
        super().__init__(report.summary)
        self.report = report


@dataclass(frozen=True)
class ValidationIssue:
    """Un problème, rattaché à un champ quand c'est possible.

    `field` à `None` pour une règle qui porte sur plusieurs champs : « la date
    de fin doit suivre la date de début » n'appartient à aucun des deux, et la
    rattacher arbitrairement à l'un ferait pointer le formulaire au mauvais
    endroit.
    """

    message: str
    field: "str | None" = None

    def __str__(self) -> str:
        return f"{self.field} : {self.message}" if self.field else self.message


@dataclass(frozen=True)
class ValidationReport:
    """Tous les problèmes trouvés, pas seulement le premier."""

    issues: "tuple[ValidationIssue, ...]" = field(default=())

    @property
    def ok(self) -> bool:
        return not self.issues

    @property
    def summary(self) -> str:
        return " ".join(str(probleme) for probleme in self.issues)

    def by_field(self) -> "dict[str | None, list[str]]":
        """Problèmes groupés par champ, pour les rendre dans un formulaire."""
        groupes: dict[str | None, list[str]] = {}
        for probleme in self.issues:
            groupes.setdefault(probleme.field, []).append(probleme.message)
        return groupes


_validators: "dict[str, list[EntityValidator]]" = {}


def register_entity_validator(entity: str, validator: EntityValidator) -> None:
    """Enregistre une règle pour une entité.

    Plusieurs règles cohabitent, consultées dans l'ordre d'enregistrement, et
    **toutes** sont évaluées : rendre le premier problème seul obligerait
    l'utilisateur à corriger son formulaire une erreur à la fois.
    """
    if not callable(validator):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(f"Un validateur doit être appelable. Reçu : {validator!r}.")
    nom = (entity or "").strip()
    if not nom:
        raise ValueError("le nom d'entité ne peut pas être vide.")
    liste = _validators.setdefault(nom, [])
    if validator not in liste:
        liste.append(validator)


def unregister_entity_validator(entity: str, validator: EntityValidator) -> bool:
    """Retire une règle. Vrai si elle était enregistrée."""
    liste = _validators.get((entity or "").strip())
    if liste and validator in liste:
        liste.remove(validator)
        return True
    return False


def registered_validators(entity: str) -> "tuple[EntityValidator, ...]":
    """Règles enregistrées pour une entité, dans l'ordre d'évaluation."""
    return tuple(_validators.get((entity or "").strip(), ()))


def clear_entity_validators(entity: "str | None" = None) -> None:
    """Retire les règles d'une entité, ou toutes. Utile aux tests."""
    if entity is None:
        _validators.clear()
    else:
        _validators.pop((entity or "").strip(), None)


def validate_entity_data(
    entity: str, data: "dict[str, Any]", context: "dict[str, Any] | None" = None
) -> ValidationReport:
    """Évalue toutes les règles. Ne lève jamais.

    Sert à **afficher** les problèmes dans un formulaire. `ensure_entity_data`
    sert à refuser.

    Un validateur qui lève, ou qui rend autre chose qu'une liste de problèmes,
    produit un problème de son propre chef : le jour où le service qu'il
    interroge tombe, tout passerait sinon.
    """
    donnees = dict(context or {})
    problemes: list[ValidationIssue] = []

    for validateur in registered_validators(entity):
        try:
            rendus = validateur(data, donnees)
        except Exception as exc:
            logger.exception(
                "Forge Entities - validateur en échec pour %s, écriture "
                "refusée par précaution", entity,
            )
            problemes.append(
                ValidationIssue(f"une règle n'a pas pu être évaluée : {exc}")
            )
            continue
        if rendus is None:
            continue
        if isinstance(rendus, ValidationIssue):
            problemes.append(rendus)
            continue
        if isinstance(rendus, str):
            problemes.append(ValidationIssue(rendus))
            continue
        try:
            for brut in cast("list[Any]", rendus):
                if isinstance(brut, ValidationIssue):
                    problemes.append(brut)
                elif isinstance(brut, str):
                    problemes.append(ValidationIssue(brut))
                else:
                    problemes.append(
                        ValidationIssue(f"règle au verdict illisible : {brut!r}")
                    )
        except TypeError:
            problemes.append(
                ValidationIssue(f"règle au verdict illisible : {rendus!r}")
            )

    return ValidationReport(tuple(problemes))


def ensure_entity_data(
    entity: str, data: "dict[str, Any]", context: "dict[str, Any] | None" = None
) -> None:
    """Refuse l'écriture si une règle s'y oppose.

    Raises:
        EntityValidationError: le rapport complet est porté par l'exception,
            de sorte qu'un contrôleur puisse rendre chaque problème en face de
            son champ.
    """
    rapport = validate_entity_data(entity, data, context)
    if not rapport.ok:
        raise EntityValidationError(rapport)
