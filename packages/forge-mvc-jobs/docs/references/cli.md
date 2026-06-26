# L'initialisation : `forge jobs:init`

Ce document décrit la commande qui installe la table de file.

Le fichier de code correspondant est `forge_mvc_jobs/cli/init.py`.

## 1. À quoi sert la commande

La table `jobs` n'est pas créée automatiquement : l'écriture en base reste
explicite (principe 3, SQL visible).
`forge jobs:init` copie la migration SQL embarquée dans le dossier
`mvc/migrations/` du projet.
Aucune connexion MariaDB ni exécution SQL à cette étape.

```bash
forge jobs:init
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

## 3. Lancer le worker

`forge jobs:init` ne lance pas le worker : le worker est un process séparé que
l'application démarre elle-même, en appelant `run_worker(handlers)` depuis son
propre script (voir [La file de tâches](queue.md)).
Le worker reste donc une commande explicite, jamais déclenchée par la requête.

## 4. Voir aussi

- [La file de tâches](queue.md) : enfiler et traiter une fois la table créée.
