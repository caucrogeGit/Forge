# pyright: strict
"""Permission portant sur une instance (RBAC-INSTANCE-PERMISSIONS-001).

Les trois niveaux d'autorisation du paquet répondent tous à la même forme de
question : « cet utilisateur peut il modifier des articles ». Aucun ne répond à
« cet utilisateur peut il modifier **cet** article, parce qu'il en est
l'auteur ».

Chaque application réécrivait donc la même condition à la main, et la
réécrivait souvent de travers : oublier que le modérateur passe outre la
propriété, ou vérifier la propriété avant la permission, donne un contrôle qui
laisse passer ou qui bloque à tort.

## Ce module n'est pas un quatrième niveau

Il n'a pas sa propre source de permissions et n'en devient pas une. Il
**compose** au dessus de celle que l'appelant choisit, par `can`, et la voie
par défaut reste le contrat RBAC, comme le veut le docstring du paquet.

## Forge ne sait pas ce qu'est un propriétaire

C'est du métier, et l'application le dit par `is_owner`. Un opt-in qui
devinerait la propriété, en cherchant une colonne `user_id` par exemple,
supposerait un schéma qu'il n'a pas choisi.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

__all__ = [
    "OwnershipCheck",
    "PermissionCheck",
    "has_instance_permission",
    "require_instance_permission",
    "InstancePermissionDenied",
]

#: Répond « cet utilisateur est il propriétaire de cet objet ». Fourni par
#: l'application, seule à le savoir.
OwnershipCheck = Callable[[Any, Any], bool]

#: Répond « cet utilisateur a t il cette permission ». C'est le point
#: d'insertion des trois niveaux existants du paquet.
PermissionCheck = Callable[[str], bool]


class InstancePermissionDenied(Exception):
    """L'utilisateur n'a de droit ni global ni de propriétaire sur l'objet."""


def has_instance_permission(
    request: Any,
    instance: Any,
    *,
    can: PermissionCheck,
    any_permission: "str | None" = None,
    own_permission: "str | None" = None,
    is_owner: "OwnershipCheck | None" = None,
) -> bool:
    """Vrai si l'utilisateur peut agir sur `instance`.

    L'ordre est délibéré, et c'est lui qui évite les deux erreurs courantes.

    1. `any_permission` accordée rend vrai **sans regarder la propriété**.
       C'est le sens de « n'importe lequel » : un modérateur passe outre, et le
       lui refuser parce qu'il n'est pas l'auteur serait un contresens.
    2. `own_permission` accordée **et** `is_owner` vrai rend vrai.
    3. Sinon faux.

    La propriété n'est vérifiée qu'après la permission. L'inverse ferait
    appeler `is_owner`, donc souvent la base, pour un utilisateur qui n'a de
    toute façon aucun droit.

    Sans `own_permission` ni `is_owner`, la fonction se réduit à
    `can(any_permission)` : la composition reste utilisable pour un contrôle
    global, sans cas particulier à écrire.

    Raises:
        ValueError: ni `any_permission` ni `own_permission` n'est déclarée, ce
            qui rendrait toujours faux et cacherait une faute de frappe.
            `own_permission` déclarée sans `is_owner` est refusée pour la même
            raison, la propriété ne pouvant alors jamais être établie.
    """
    if any_permission is None and own_permission is None:
        raise ValueError(
            "déclarer au moins une permission, globale ou de propriétaire : "
            "sans elle le contrôle refuserait toujours."
        )
    if own_permission is not None and is_owner is None:
        raise ValueError(
            f"own_permission={own_permission!r} déclarée sans is_owner : la "
            "propriété ne pourrait jamais être établie, et le droit jamais "
            "accordé. Forge ne devine pas ce qu'est un propriétaire."
        )

    if any_permission is not None and can(any_permission):
        return True

    if own_permission is not None and is_owner is not None:
        return can(own_permission) and bool(is_owner(request, instance))

    return False


def require_instance_permission(
    request: Any,
    instance: Any,
    *,
    can: PermissionCheck,
    any_permission: "str | None" = None,
    own_permission: "str | None" = None,
    is_owner: "OwnershipCheck | None" = None,
) -> None:
    """Lève :class:`InstancePermissionDenied` si le droit manque.

    Même contrôle que :func:`has_instance_permission`, pour un contrôleur qui
    préfère laisser remonter plutôt que tester. Ne rend aucune réponse HTTP :
    la forme du refus, page ou JSON, appartient à l'application.
    """
    if not has_instance_permission(
        request, instance,
        can=can,
        any_permission=any_permission,
        own_permission=own_permission,
        is_owner=is_owner,
    ):
        demandees = [p for p in (any_permission, own_permission) if p]
        raise InstancePermissionDenied(
            f"droit refusé sur l'objet : aucune des permissions "
            f"{', '.join(demandees)} ne s'applique."
        )
