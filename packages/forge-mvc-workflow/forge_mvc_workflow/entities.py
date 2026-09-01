# pyright: strict
"""Statuts lus depuis un contrat d'entité (WORKFLOW-ENTITY-STATUS-001).

Une application qui gère un cycle de vie déclare sa liste de statuts **deux
fois**. Une fois dans le contrat d'entité, en `choices` du champ, pour que le
formulaire propose un choix et que la base accepte la valeur. Une autre fois en
Python, en `make_status`, pour que le workflow connaisse ses transitions.

Rien ne gardait les deux identiques. Ajouter un statut au contrat sans toucher
au workflow donne un choix que le formulaire propose et que la transition
refuse ; le retirer du contrat sans toucher au workflow donne une transition
vers un statut que la base n'accepte plus. Dans les deux cas, la panne
n'apparaît qu'à l'usage, et sur un seul chemin.

Ce module fait du contrat la source, et supprime la seconde déclaration.

## Sans dépendance vers le moteur d'entités

Un contrat d'entité est un dictionnaire JSON, dont la forme est documentée.
Le lire ne demande pas d'importer `forge-mvc-entities`, et ce module ne le fait
pas : un projet qui décrit ses entités autrement peut lui passer la même
structure.
"""
from __future__ import annotations

from typing import Any, cast

from .status import WorkflowStatus, WorkflowStatusError, make_status

__all__ = [
    "EntityStatusError",
    "statuses_from_choices",
    "statuses_from_entity_field",
    "status_values",
]


class EntityStatusError(ValueError):
    """Le champ demandé est absent, ou ne déclare aucun choix exploitable."""


def statuses_from_choices(
    choices: "list[dict[str, Any]] | Any",
    *,
    initial: "str | None" = None,
    final: "tuple[str, ...] | list[str] | None" = None,
) -> list[WorkflowStatus]:
    """Convertit les `choices` d'un champ en statuts de workflow.

    L'ordre du contrat est conservé : c'est celui que le formulaire affiche, et
    en changer ferait diverger deux vues de la même liste.

    `initial` et `final` ne se devinent pas. Un contrat d'entité dit quelles
    valeurs sont permises, jamais laquelle commence un cycle ni lesquelles le
    terminent : le supposer, en prenant la première par exemple, serait une
    règle inventée par Forge.

    Raises:
        EntityStatusError: `choices` n'est pas exploitable, ou `initial` et
            `final` désignent des valeurs absentes. Une faute de frappe y
            produirait sinon un cycle sans début, que rien ne signalerait.
    """
    if not isinstance(choices, list):
        raise EntityStatusError(
            f"choices doit être une liste. Reçu : {type(choices).__name__}."
        )

    finaux = set(final or ())
    statuts: list[WorkflowStatus] = []
    vus: set[str] = set()

    for index, brut in enumerate(cast("list[Any]", choices)):
        if not isinstance(brut, dict):
            raise EntityStatusError(
                f"choices[{index}] doit être un objet {{value, label}}."
            )
        choix = cast("dict[str, Any]", brut)
        valeur = choix.get("value")
        if not isinstance(valeur, str) or not valeur.strip():
            raise EntityStatusError(f"choices[{index}].value manquant ou vide.")
        if valeur in vus:
            raise EntityStatusError(f"choices[{index}].value en double : {valeur!r}.")
        vus.add(valeur)

        libelle = choix.get("label")
        try:
            statuts.append(make_status(
                valeur,
                label=libelle if isinstance(libelle, str) else "",
                is_initial=valeur == initial,
                is_final=valeur in finaux,
            ))
        except WorkflowStatusError as exc:
            raise EntityStatusError(
                f"choices[{index}].value inutilisable comme statut : {exc}"
            ) from exc

    if initial is not None and initial not in vus:
        raise EntityStatusError(
            f"initial={initial!r} ne figure pas dans les choix "
            f"({', '.join(sorted(vus)) or 'aucun'})."
        )
    manquants = sorted(finaux - vus)
    if manquants:
        raise EntityStatusError(
            f"final contient des valeurs absentes des choix : {', '.join(manquants)}."
        )
    return statuts


def statuses_from_entity_field(
    entity: "dict[str, Any]",
    field_name: str,
    *,
    initial: "str | None" = None,
    final: "tuple[str, ...] | list[str] | None" = None,
) -> list[WorkflowStatus]:
    """Statuts déduits du champ `field_name` d'un contrat d'entité.

    Le champ est **nommé** par l'appelant, jamais deviné. Repérer « le champ qui
    ressemble à un statut » supposerait une convention de nommage que Forge
    n'impose pas, et se tromperait sur une entité qui en porte deux.

    Raises:
        EntityStatusError: le champ est absent du contrat, ou ne déclare pas de
            `choices`.
    """
    champs = entity.get("fields")
    if not isinstance(champs, list):
        raise EntityStatusError("le contrat ne déclare aucun champ.")

    for brut in cast("list[Any]", champs):
        if not isinstance(brut, dict):
            continue
        champ = cast("dict[str, Any]", brut)
        if champ.get("name") != field_name:
            continue
        choix = champ.get("choices")
        if choix is None:
            raise EntityStatusError(
                f"le champ {field_name!r} ne déclare pas de choices : "
                "un statut sans valeurs permises n'est pas un cycle de vie."
            )
        return statuses_from_choices(choix, initial=initial, final=final)

    noms: list[str] = []
    for brut in cast("list[Any]", champs):
        if isinstance(brut, dict):
            nom = cast("dict[str, Any]", brut).get("name")
            if isinstance(nom, str) and nom:
                noms.append(nom)
    raise EntityStatusError(
        f"champ {field_name!r} absent du contrat. Déclarés : "
        f"{', '.join(noms) or 'aucun'}."
    )


def status_values(statuses: "list[WorkflowStatus]") -> list[str]:
    """Noms des statuts, dans l'ordre. Utile pour comparer deux sources."""
    return [statut.name for statut in statuses]
