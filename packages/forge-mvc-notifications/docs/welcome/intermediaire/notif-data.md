# Type et données

Objectif : qualifier une notification par son `type` et lui attacher une charge `data`.

**Ce que vous allez apprendre :** le paramètre `type` qualifie une notification (par exemple "info" ou "alerte").
Le paramètre `data` attache un dictionnaire, sérialisé en JSON.
Le filtre `unread_only=True` ne renvoie que les notifications non lues.

Deuxième palier du **niveau intermédiaire** de la progression Notifications.

## Ce que ce starter montre

- qualifier une notification avec `type` ;
- attacher une charge `data` sérialisée en JSON ;
- ne lire que les non lues avec `unread_only=True`.

## Fonctions Forge utilisées

| Fonction | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `notify(recipient, message, type=..., data=...)` | Crée une notification qualifiée et enrichie. | Opt-ins |
| `get_notifications(recipient, unread_only=True)` | Renvoie uniquement les notifications non lues. | Opt-ins |

## 1. Qualifier, enrichir, puis filtrer

```python
from forge_mvc_notifications import notify, get_notifications

notify(
    "eleve.42",
    "Devoir à rendre demain",
    type="alerte",
    data={"devoir_id": 7, "echeance": "2026-06-27"},
)

non_lues = get_notifications("eleve.42", unread_only=True)
for notification in non_lues:
    print(notification.type, notification.data["devoir_id"])
```

### Comprendre ce code

- `type="alerte"` qualifie la notification ; libre à l'application de définir ses propres types.
- `data={...}` attache un dictionnaire, sérialisé en JSON au stockage et relu en dict.
- Une valeur `data` non sérialisable en JSON lève une `NotificationError`.
- `unread_only=True` restreint `get_notifications` aux seules notifications non lues.

## À retenir

- `type` qualifie la notification ; c'est une chaîne libre côté application.
- `data` accepte un dict sérialisable en JSON, relu tel quel dans `notification.data`.
- `get_notifications(..., unread_only=True)` filtre sur les non lues.

## Après ce starter

Vous maîtrisez la qualification et l'enrichissement.
Place au bilan du niveau intermédiaire.

[Bilan intermédiaire](bilan.md)
