# L'initialisation : `forge notifications:init`

Ce document décrit la commande qui installe la table des notifications.

Le fichier de code correspondant est `forge_mvc_notifications/cli/init.py`.

## 1. À quoi sert la commande

La table `notifications` n'est pas créée automatiquement : l'écriture en base
reste explicite (principe 3, SQL visible).
`forge notifications:init` copie la migration SQL embarquée dans le dossier
`mvc/migrations/` du projet.
Aucune connexion MariaDB ni exécution SQL à cette étape.

```bash
forge notifications:init
forge migration:apply
```

`forge migration:apply` applique ensuite la migration et crée la table.

## 2. Comportement

La commande est idempotente et ne réécrit jamais en silence :

- un fichier absent est copié (`[OK]`) ;
- un fichier déjà présent et identique est laissé tel quel (`[OK]`) ;
- un fichier présent au contenu différent déclenche un `[WARN]` et n'est pas
  écrasé.

Si le dossier `mvc/` est absent, la commande s'arrête avec un message clair
(`[ERREUR]`).

## 3. Voir aussi

- [Les notifications](store.md) : créer et lire une fois la table créée.
