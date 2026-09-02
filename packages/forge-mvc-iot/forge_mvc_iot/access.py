# pyright: strict
"""Contrôle d'accès applicatif sur l'API de lecture (`IOT-RBAC-READ-001`).

Le jeton dit **ce qu'un porteur peut lire**, par site ou par équipement
(`IOT-DEVICE-AUTH-001`). Il ne dit rien de **qui** le porte, ni de ce que cette
personne a le droit de faire dans l'application.

Une console interne où un opérateur consulte les relevés a besoin des deux :
un jeton qui borne la portée, et la vérification que l'utilisateur connecté a
la permission de lire.

## Pourquoi une prise et non une dépendance à `forge-mvc-rbac`

Aucun opt-in Forge n'importe un autre opt-in, et un garde-fou le vérifie. Un
paquet IoT qui dépendrait du RBAC obligerait à installer le RBAC pour recevoir
des mesures MQTT, ce que le principe 8 refuse.

L'application branche donc son contrôle, comme elle branche un analyseur
antivirus dans `forge-mvc-files`. Trois lignes suffisent quand `forge-mvc-rbac`
est installé, et le paquet IoT n'en sait rien.

## Une vérification qui échoue refuse la lecture

Un contrôle qui lève, ou qui rend autre chose qu'un booléen, ne dit **pas** que
l'accès est permis, il ne dit rien. Traiter ce silence comme une autorisation
est la faute classique de ce genre de branchement : le jour où le service de
permissions tombe, tout s'ouvre, et rien ne le signale.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from forge_mvc_iot.tokens import IotScope

__all__ = [
    "ACTION_READ_EVENTS",
    "ACTION_READ_AGGREGATES",
    "IOT_ACTIONS",
    "IotPermissionCheck",
    "register_iot_permission_check",
    "unregister_iot_permission_check",
    "registered_permission_checks",
    "clear_iot_permission_checks",
    "is_read_allowed",
]

logger = logging.getLogger(__name__)

#: Lecture des mesures brutes.
ACTION_READ_EVENTS = "iot.read_events"
#: Lecture des agrégats.
ACTION_READ_AGGREGATES = "iot.read_aggregates"

#: Les actions que le paquet soumet au contrôle. Fermée : un contrôle branché
#: sait ainsi exactement ce qu'il peut recevoir.
IOT_ACTIONS = frozenset({ACTION_READ_EVENTS, ACTION_READ_AGGREGATES})

#: Un contrôle reçoit la requête, la portée du jeton et l'action visée.
IotPermissionCheck = Callable[[Any, IotScope, str], bool]

_checks: "list[IotPermissionCheck]" = []


def register_iot_permission_check(check: IotPermissionCheck) -> None:
    """Branche un contrôle, consulté avant chaque lecture.

    Plusieurs contrôles peuvent cohabiter : **tous** doivent accepter, et le
    premier refus arrête la série. Une politique d'accès s'ajoute, elle ne se
    remplace pas.

    Sans contrôle branché, seule la portée du jeton s'applique, ce qui est le
    comportement du paquet avant ce ticket.
    """
    if not callable(check):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(f"Un contrôle doit être appelable. Reçu : {check!r}.")
    if check not in _checks:
        _checks.append(check)


def unregister_iot_permission_check(check: IotPermissionCheck) -> bool:
    """Débranche un contrôle. Vrai s'il était branché."""
    if check in _checks:
        _checks.remove(check)
        return True
    return False


def registered_permission_checks() -> "tuple[IotPermissionCheck, ...]":
    """Contrôles branchés, dans l'ordre de consultation."""
    return tuple(_checks)


def clear_iot_permission_checks() -> None:
    """Débranche tout. Utile aux tests, et à un redémarrage à chaud."""
    _checks.clear()


def is_read_allowed(request: Any, scope: IotScope, action: str) -> bool:
    """Vrai si tous les contrôles branchés autorisent l'action.

    Sans contrôle branché, rend vrai sans rien évaluer : le paquet n'invente
    pas une politique que personne n'a demandée.

    Un contrôle qui lève ou qui rend autre chose qu'un booléen fait **refuser**
    la lecture, et l'incident est journalisé pour l'exploitant. Le refus est
    ici la seule réponse sûre : le contrôle n'a pas dit oui.
    """
    if action not in IOT_ACTIONS:
        raise ValueError(
            f"action inconnue : {action!r}. Attendu l'une de "
            f"{', '.join(sorted(IOT_ACTIONS))}."
        )
    if not _checks:
        return True

    for check in _checks:
        try:
            verdict = check(request, scope, action)
        except Exception:
            logger.exception(
                "Forge IoT - contrôle de permission en échec, lecture refusée "
                "par précaution (action %s, portée %s)",
                action, scope.describe(),
            )
            return False
        if verdict is not True:
            if verdict is not False:
                logger.warning(
                    "Forge IoT - un contrôle de permission a rendu %r au lieu "
                    "d'un booléen ; lecture refusée par précaution.",
                    verdict,
                )
            return False
    return True
