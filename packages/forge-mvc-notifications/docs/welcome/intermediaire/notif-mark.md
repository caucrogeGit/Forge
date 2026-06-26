# Marquer comme lu

Objectif : marquer une notification comme lue, ou tout marquer d'un coup.

**Ce que vous allez apprendre :** la fonction `mark_read` marque une notification précise comme lue.
La fonction `mark_all_read` marque toutes les notifications d'un destinataire comme lues.
Ces deux fonctions renseignent le compteur de non lues.

Premier palier du **niveau intermédiaire** de la progression Notifications.

!!! note "Module opt-in"
    Si `forge-mvc-notifications` n'est pas installé, l'import échoue.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Ce que ce starter montre

- marquer une notification précise comme lue avec `mark_read` ;
- marquer toutes les notifications d'un destinataire avec `mark_all_read`.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `mark_read(notification_id)` | Marque une notification comme lue ; renvoie `True` si elle était non lue. | Opt-ins |
| `mark_all_read(recipient)` | Marque toutes les notifications du destinataire ; renvoie le nombre marqué. | Opt-ins |

## 1. Marquer une notification, puis toutes

```python
from forge_mvc_notifications import notify, mark_read, mark_all_read

notification_id = notify("eleve.42", "Votre note est publiée")

etait_non_lue = mark_read(notification_id)
print("marquée lue :", etait_non_lue)

nombre = mark_all_read("eleve.42")
print(nombre, "notification(s) marquée(s) lue(s)")
```

### Comprendre ce code

- `mark_read(notification_id)` marque la notification ciblée comme lue.
- Elle renvoie `True` si la notification était non lue, `False` si elle l'était déjà.
- `mark_all_read("eleve.42")` marque toutes les notifications encore non lues du destinataire.
- Elle renvoie le nombre de notifications effectivement marquées.

## À retenir

- `mark_read(id)` marque une notification précise ; `True` si elle était non lue.
- `mark_all_read(destinataire)` marque tout d'un coup et renvoie le nombre marqué.
- Après ces appels, `unread_count` reflète le nouvel état.

## Après ce starter

Vous savez gérer l'état lu.
Voyons comment qualifier une notification par son `type` et lui attacher une charge `data`.

[Type et données](notif-data.md)
