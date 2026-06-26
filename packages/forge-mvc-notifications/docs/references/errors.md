# Les erreurs

Ce document décrit l'erreur levée par `forge_mvc_notifications`.

Le fichier de code correspondant est `forge_mvc_notifications/errors.py`.

## 1. `NotificationError`

```python
class NotificationError(ValueError):
    ...
```

`NotificationError` signale une entrée invalide pour une notification.
Elle hérite de `ValueError`.

## 2. Quand est-elle levée ?

| Cause | Origine |
|---|---|
| Destinataire vide | `notify` |
| Message vide | `notify` |
| Données non sérialisables en JSON | `notify` |
| `limit` inférieur à 1 | `get_notifications` |

## 3. Rattraper l'erreur

```python
from forge_mvc_notifications import notify, NotificationError

try:
    notify(destinataire, message)
except NotificationError as exc:
    print(f"Notification refusée : {exc}")
```

## 4. Voir aussi

- [Les notifications](store.md) : `notify`, `get_notifications`.
