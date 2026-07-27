# forge-mvc-notifications

Notifications in-app opt-in pour Forge : créer des notifications destinées aux
utilisateurs (élève inscrit, note publiée, devoir à rendre) dans une table
`notifications`, les lire, les marquer comme lues.

Périmètre V1 : notifications in-app (des lignes en base, affichées dans l'IHM).
La livraison hors application (email, push) reste à la charge de l'application,
par exemple en combinant ce paquet avec `forge-mvc-jobs` et `forge-mvc-mail`.

## Installation

```bash
pip install --pre forge-mvc-notifications
```

En développement : `pip install -e ./packages/forge-mvc-notifications`.

## Mise en place de la table

```bash
forge notifications:init   # copie la migration dans mvc/migrations/
forge migration:apply      # crée la table notifications
```

## Utilisation

```python
from forge_mvc_notifications import notify, get_notifications, unread_count, mark_read

notify("eleve.42", "Votre note est publiée", type="info", data={"cours": "maths"})

print(unread_count("eleve.42"))            # 1
for n in get_notifications("eleve.42", unread_only=True):
    print(n.message, n.created_at)
mark_read(1)
```

L'API expose `notify`, `get_notifications`, `unread_count`, `mark_read`,
`mark_all_read`, plus `Notification`, `NotificationError`, `TABLE_NAME`,
`MAX_LIMIT`.

## Périmètre

- Stockage in-app uniquement (lignes en base).
- Hors périmètre : livraison email/push (à combiner avec `forge-mvc-jobs` +
  `forge-mvc-mail`), préférences de notification, temps réel.

Documentation complète : <https://forgemvc.com/docs/forge/>.
