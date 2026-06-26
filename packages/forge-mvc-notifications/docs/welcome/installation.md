# Installation de forge-mvc-notifications

Objectif : installer l'opt-in Notifications et préparer la table en base.

Le parcours qui suit montre, en trois niveaux, comment créer une notification in-app, la lire, la marquer comme lue, puis comprendre le périmètre du paquet et son indépendance vis-à-vis du cœur.

## Installer le paquet

```bash
pip install --pre forge-mvc-notifications
```

En développement, depuis le dépôt, l'installation éditable convient aussi :

```bash
pip install -e packages/forge-mvc-notifications
```

Le paquet dépend du cœur `forge-mvc`.
La dépendance va de l'opt-in vers le cœur, jamais l'inverse.

## Créer la table

Les notifications sont stockées dans une table `notifications`.
Le paquet fournit une commande qui prépare la migration, puis vous l'appliquez :

```bash
forge notifications:init
forge migration:apply
```

`notifications:init` écrit la migration de création de la table.
`migration:apply` l'exécute sur la base configurée.

## Vérifier l'installation

```python
from forge_mvc_notifications import notify, unread_count

notify("eleve.42", "Bienvenue sur la plateforme")
print(unread_count("eleve.42"), "notification(s) non lue(s)")
```

Si ce script affiche un compteur non nul, l'opt-in fonctionne et la table est en place.

## Après cette étape

Place au niveau débutant : créer votre première notification.

[Niveau débutant : Première notification](debutant/notif-welcome.md)
