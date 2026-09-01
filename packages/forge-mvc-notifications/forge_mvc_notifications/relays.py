# pyright: strict
"""Relais d'une notification vers d'autres canaux (NOTIF-MAIL-BRIDGE-001).

Une notification in-app n'est vue que si son destinataire revient sur le site.
Pour une alerte qui compte, une facture impayée ou un incident, c'est trop tard
et l'opt-in n'offrait aucun moyen de doubler le canal.

Chaque application réécrivait donc la même chose à côté de `notify`, et l'y
oubliait à un endroit sur trois : la notification partait, l'email non, et
personne ne s'en apercevait avant la réclamation.

## Ce module ne parle à personne

Il **annonce** les notifications créées, et l'application décide de ce qu'elle
en fait. `forge-mvc-mail` et `forge-mvc-jobs` sont les destinataires évidents
sans être imposés, et aucun n'est importé ici.

    from forge_mvc_jobs import enqueue
    from forge_mvc_mail import MAIL_JOB_TASK, MailMessage, message_to_payload
    from forge_mvc_notifications import on_notification_created

    @on_notification_created
    def doubler_par_email(notification):
        if notification.type != "alerte":
            return
        enqueue(MAIL_JOB_TASK, message_to_payload(MailMessage(
            subject="Alerte", to=adresse_de(notification.recipient),
            body_text=notification.message,
        )))

## Un relais ne peut pas annuler une notification

L'annonce suit l'écriture. Si un relais lève, l'exception est avalée et
journalisée : la notification est déjà en base, et faire échouer `notify` après
coup laisserait l'appelant croire qu'elle n'existe pas alors qu'elle s'affiche.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "NotificationEvent",
    "NotificationRelay",
    "on_notification_created",
    "clear_notification_relays",
    "notification_relays",
    "notify_relays",
]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NotificationEvent:
    """Une notification qui vient d'être écrite.

    `notification_id` permet de la retrouver, et `data` porte ce que
    l'application y a mis : un relais a souvent besoin de ce complément pour
    composer son message, une référence de facture par exemple.
    """

    notification_id: int
    recipient: str
    message: str
    type: str = "info"
    data: dict[str, Any] = field(default_factory=dict[str, Any])


#: Un relais reçoit la notification écrite et ne rend rien.
NotificationRelay = Callable[[NotificationEvent], None]

_relays: list[NotificationRelay] = []


def on_notification_created(relay: NotificationRelay) -> NotificationRelay:
    """Enregistre un relais, et le rend pour permettre l'usage en décorateur.

    L'enregistrement est explicite : une notification ne part sur aucun autre
    canal tant que l'application ne l'a pas demandé.
    """
    _relays.append(relay)
    return relay


def clear_notification_relays() -> None:
    """Retire tous les relais.

    Sert aux tests, qu'un relais laissé en place ferait dépendre les uns des
    autres, et à une application qui recompose ses canaux au démarrage.
    """
    _relays.clear()


def notification_relays() -> "tuple[NotificationRelay, ...]":
    """Relais enregistrés, dans leur ordre d'enregistrement."""
    return tuple(_relays)


def notify_relays(event: NotificationEvent) -> None:
    """Annonce une notification écrite. N'échoue jamais.

    Appelée par `notify` après l'écriture. Chaque relais est isolé : l'un qui
    lève n'empêche pas les suivants, et aucun ne peut faire échouer une
    notification déjà enregistrée.
    """
    for relais in tuple(_relays):
        try:
            relais(event)
        except Exception:  # noqa: BLE001 — la notification est déjà écrite
            logger.warning(
                "Relais de notification en erreur, notification %s tout de même "
                "enregistrée.", event.notification_id, exc_info=True,
            )
