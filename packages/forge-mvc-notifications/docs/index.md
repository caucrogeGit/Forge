# Forge Notifications

`forge-mvc-notifications` est l'opt-in de notifications in-app de Forge.

Il crée des notifications destinées aux utilisateurs (élève inscrit, note
publiée, devoir à rendre) dans une table `notifications`, permet de les lire et
de les marquer comme lues.

## Périmètre in-app

Le périmètre V1 est l'in-app : des lignes en base, affichées dans l'interface.
La livraison hors application (email, push) reste applicative, par exemple en
combinant ce paquet avec `forge-mvc-jobs` (tâche de fond) et `forge-mvc-mail`
(envoi).
Le cœur de Forge ignore tout des notifications ; la dépendance va de l'opt-in
vers le cœur, jamais l'inverse.

## Mise en route

```bash
pip install --pre forge-mvc-notifications
forge notifications:init   # copie la migration dans mvc/migrations/
forge migration:apply      # crée la table notifications
```

## Premier usage

```python
from forge_mvc_notifications import notify, get_notifications, unread_count, mark_read

notify("eleve.42", "Votre note est publiée")
print(unread_count("eleve.42"))
for n in get_notifications("eleve.42", unread_only=True):
    print(n.message)
mark_read(1)
```

## Pour aller plus loin

- [Les notifications](references/store.md) : `notify`, `get_notifications`, `mark_read`.
- [L'initialisation](references/cli.md) : `forge notifications:init`.
- [Les erreurs](references/errors.md) : `NotificationError`.
