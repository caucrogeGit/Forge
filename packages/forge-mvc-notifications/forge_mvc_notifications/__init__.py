# pyright: strict
"""forge-mvc-notifications — notifications in-app opt-in (NOTIFICATIONS-OPTIN-SCAFFOLD-001).

Brique générique : créer des notifications destinées aux utilisateurs (élève
inscrit, note publiée, devoir à rendre) dans une table `notifications`, les lire,
les marquer comme lues. API explicite `notify`/`get_notifications`/`mark_read`.

Périmètre V1 : notifications in-app (lignes en base). La livraison hors
application (email, push) reste applicative, et `on_notification_created`
lui donne un point d'accroche : le paquet **annonce** ce qu'il écrit, sans
parler à personne (NOTIF-MAIL-BRIDGE-001). La dépendance va de l'opt-in vers le
cœur, jamais l'inverse.
"""
from forge_mvc_notifications.relays import (
    NotificationEvent,
    NotificationRelay,
    clear_notification_relays,
    notification_relays,
    on_notification_created,
)
from forge_mvc_notifications.errors import NotificationError
from forge_mvc_notifications.store import (
    MAX_LIMIT,
    TABLE_NAME,
    Notification,
    get_notifications,
    mark_all_read,
    mark_read,
    notify,
    validate_target_url,
    unread_count,
)

__version__ = "1.0.0rc7"

__all__ = [
    # Relais vers d'autres canaux (NOTIF-MAIL-BRIDGE-001)
    "on_notification_created",
    "clear_notification_relays",
    "notification_relays",
    "NotificationEvent",
    "NotificationRelay",
    "validate_target_url",
    "NotificationError",
    "Notification",
    "TABLE_NAME",
    "MAX_LIMIT",
    "notify",
    "get_notifications",
    "unread_count",
    "mark_read",
    "mark_all_read",
]
