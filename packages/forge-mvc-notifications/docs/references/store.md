# Les notifications

Ce document décrit la création, la lecture et le marquage des notifications.

Le fichier de code correspondant est `forge_mvc_notifications/store.py`.

## 1. Le modèle

Une notification est une ligne de la table `notifications` : un destinataire (`recipient`), un type (`type`), un message (`message`), des données libres (`data`), une date de lecture (`read_at`, `NULL` si non lue) et une date de création (`created_at`).
Le périmètre V1 est l'in-app : des lignes en base, affichées dans l'interface.

## 2. Créer (`notify`)

```python
def notify(recipient, message, *, type="info", data=None, db=None) -> int
```

`notify` crée une notification et renvoie son identifiant.
`recipient` et `message` sont obligatoires.
Lève `NotificationError` si l'un est vide ou si `data` n'est pas sérialisable en JSON.

```python
from forge_mvc_notifications import notify

notify("eleve.42", "Votre note est publiée", type="info", data={"cours": "maths"})
```

## 3. Lire (`get_notifications`, `unread_count`)

```python
def get_notifications(recipient, *, unread_only=False, limit=50, db=None) -> list[Notification]
def unread_count(recipient, *, db=None) -> int
```

`get_notifications` renvoie les notifications de `recipient`, les plus récentes d'abord ; `unread_only=True` ne renvoie que les non lues.
`limit` est borné à `MAX_LIMIT` (1000).

```python
from forge_mvc_notifications import get_notifications, unread_count

print(unread_count("eleve.42"))
for n in get_notifications("eleve.42", unread_only=True):
    print(n.message, n.created_at)
```

## 4. Marquer lu (`mark_read`, `mark_all_read`)

```python
def mark_read(notification_id, *, db=None) -> bool
def mark_all_read(recipient, *, db=None) -> int
```

`mark_read` renvoie `True` si la notification était non lue.
`mark_all_read` renvoie le nombre de notifications marquées.

## 5. L'objet (`Notification`)

```python
@dataclass(frozen=True)
class Notification:
    id: int
    recipient: str
    type: str
    message: str
    data: dict
    read: bool
    created_at: str
```

## 6. Le paramètre `db`

Les fonctions acceptent un `db` injectable (par défaut `core.database.db`), ce qui rend le store vérifiable sans base réelle en test.

## 7. Voir aussi

- [L'initialisation](cli.md) : créer la table via `forge notifications:init`.
- [Les erreurs](errors.md) : `NotificationError`.
