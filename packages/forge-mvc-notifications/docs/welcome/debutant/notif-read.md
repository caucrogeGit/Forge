# Lire les notifications

Objectif : relire les notifications d'un destinataire et compter les non lues.

**Ce que vous allez apprendre :** la fonction `get_notifications` renvoie les notifications d'un destinataire, les plus récentes d'abord.
La fonction `unread_count` donne le nombre de notifications non lues.
Chaque notification est un objet `Notification` immuable.

Deuxième palier du **niveau débutant** de la progression Notifications.

## Ce que ce starter montre

- lister les notifications d'un destinataire avec `get_notifications` ;
- compter les non lues avec `unread_count`.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `get_notifications(recipient)` | Renvoie la liste des notifications, plus récentes d'abord. | Opt-ins |
| `unread_count(recipient)` | Renvoie le nombre de notifications non lues. | Opt-ins |

## 1. Lister et compter

```python
from forge_mvc_notifications import get_notifications, unread_count

notifications = get_notifications("eleve.42")
for notification in notifications:
    print(notification.created_at, notification.message)

print(unread_count("eleve.42"), "non lue(s)")
```

### Comprendre ce code

- `get_notifications("eleve.42")` renvoie une `list[Notification]`, triée de la plus récente à la plus ancienne.
- Chaque `Notification` expose `id`, `recipient`, `type`, `message`, `data`, `read` et `created_at`.
- `unread_count("eleve.42")` compte uniquement les notifications dont `read` vaut `False`.
- La liste est bornée par défaut à 50 entrées ; le paramètre `limit` ajuste cette borne.

## À retenir

- `get_notifications(destinataire)` renvoie les notifications, plus récentes d'abord.
- `unread_count(destinataire)` compte les non lues.
- Une `Notification` est un objet immuable avec `id`, `message`, `read` et `created_at`.

## Après ce starter

Vous savez créer et lire des notifications.
Place au bilan du niveau débutant.

[Bilan débutant](bilan.md)
