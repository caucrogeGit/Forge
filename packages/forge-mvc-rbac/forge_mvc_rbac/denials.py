# pyright: strict
"""Observation des refus d'accès (RBAC-DENIAL-AUDIT-001).

Un refus rendait une 403 et rien de plus. Aucune trace nulle part, si bien
qu'une énumération de droits, quelqu'un qui essaie une à une les routes
protégées, ne laissait rien derrière elle. L'exploitant n'avait aucun moyen de
la voir, ni même de savoir qu'un compte butait sur une permission mal
attribuée.

## Ni journal, ni dépendance

Ce module ne journalise rien lui même et n'importe aucun opt-in. Il **annonce**
les refus, et l'application décide de ce qu'elle en fait, `forge-mvc-audit`
étant le destinataire évident sans être imposé.

    from forge_mvc_audit import record_audit
    from forge_mvc_rbac import on_permission_denied

    on_permission_denied(lambda refus: record_audit(
        "acces.refuse", actor=refus.actor, details=refus.permission,
    ))

## Un observateur ne peut pas casser une réponse

Un refus est déjà un chemin d'erreur. Si l'observateur lève, l'exception est
avalée et journalisée : transformer un 403 en 500 parce que la base d'audit est
indisponible ferait d'un contrôle d'accès qui fonctionne une panne du site.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

__all__ = [
    "DenialEvent",
    "DenialObserver",
    "on_permission_denied",
    "clear_denial_observers",
    "denial_observers",
    "notify_permission_denied",
]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DenialEvent:
    """Un refus d'accès, tel que les gardes le rapportent.

    `actor` peut être `None` : un visiteur non authentifié qui touche une route
    protégée est refusé lui aussi, et c'est souvent celui qu'on veut voir.

    `source` nomme la garde qui a refusé, pour distinguer un refus contractuel
    d'un refus de permissions chargées en base : les deux ne se corrigent pas au
    même endroit.
    """

    permission: str
    actor: "str | None" = None
    path: "str | None" = None
    method: "str | None" = None
    source: str = ""


#: Un observateur reçoit le refus et ne rend rien.
DenialObserver = Callable[[DenialEvent], None]

_observers: list[DenialObserver] = []


def on_permission_denied(observer: DenialObserver) -> DenialObserver:
    """Enregistre un observateur, et le rend pour permettre l'usage en décorateur.

    L'enregistrement est explicite : rien n'observe les refus tant que
    l'application ne l'a pas demandé.
    """
    _observers.append(observer)
    return observer


def clear_denial_observers() -> None:
    """Retire tous les observateurs.

    Sert aux tests, qu'un observateur laissé en place ferait dépendre les uns
    des autres.
    """
    _observers.clear()


def denial_observers() -> "tuple[DenialObserver, ...]":
    """Observateurs enregistrés, dans leur ordre d'enregistrement."""
    return tuple(_observers)


def notify_permission_denied(
    permission: str,
    *,
    request: Any = None,
    source: str = "",
) -> None:
    """Annonce un refus aux observateurs. N'échoue jamais.

    Appelée par les gardes du paquet. L'événement est construit **une fois**
    pour tous les observateurs, et chacun est isolé : l'un qui lève n'empêche
    pas les suivants, et aucun ne peut transformer le 403 en 500.
    """
    if not _observers:
        return

    evenement = DenialEvent(
        permission=permission,
        actor=_acteur(request),
        path=_attribut(request, "path"),
        method=_attribut(request, "method"),
        source=source,
    )
    for observateur in tuple(_observers):
        try:
            observateur(evenement)
        except Exception:  # noqa: BLE001 — un refus ne doit jamais devenir une panne
            logger.warning(
                "Observateur de refus d'accès en erreur, refus tout de même "
                "appliqué (permission %r).", permission, exc_info=True,
            )


def _acteur(request: Any) -> "str | None":
    """Identifiant de l'utilisateur, ou `None` s'il n'est pas authentifié."""
    if request is None:
        return None
    try:
        from core.auth.session import get_authenticated_user_id

        identifiant = get_authenticated_user_id(request)
    except Exception:  # noqa: BLE001 — session absente ou cœur indisponible
        return None
    return None if identifiant is None else str(identifiant)


def _attribut(request: Any, nom: str) -> "str | None":
    """Attribut de requête, quand elle en a un. Les doubles de test varient."""
    if request is None:
        return None
    valeur = getattr(request, nom, None)
    return None if valeur is None else str(valeur)
