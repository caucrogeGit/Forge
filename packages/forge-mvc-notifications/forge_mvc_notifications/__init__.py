# pyright: strict
"""forge-mvc-notifications — notifications in-app opt-in (NOTIFICATIONS-OPTIN-SCAFFOLD-001).

Brique générique : créer des notifications destinées aux utilisateurs (élève
inscrit, note publiée, devoir à rendre) dans une table `notifications`, les lire,
les marquer comme lues. API explicite `notify`/`get_notifications`/`mark_read`.

Périmètre V1 : notifications in-app (lignes en base). La livraison hors
application (email, push) reste applicative, par exemple en combinant ce paquet
avec `forge-mvc-jobs` et `forge-mvc-mail`. La dépendance va de l'opt-in vers le
cœur, jamais l'inverse.
"""
from forge_mvc_notifications.errors import NotificationError
from forge_mvc_notifications.store import (
    CREATE_TABLE_SQL,
    MAX_LIMIT,
    TABLE_NAME,
    Notification,
    get_notifications,
    mark_all_read,
    mark_read,
    notify,
    unread_count,
)

__version__ = "1.0.0rc2"

__all__ = [
    "NotificationError",
    "Notification",
    "TABLE_NAME",
    "MAX_LIMIT",
    "CREATE_TABLE_SQL",
    "notify",
    "get_notifications",
    "unread_count",
    "mark_read",
    "mark_all_read",
]
