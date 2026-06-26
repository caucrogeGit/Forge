# L'initialisation : `forge audit:init`

Ce document décrit la commande qui installe la table d'audit.

Le fichier de code correspondant est `forge_mvc_audit/cli/init.py`.

## 1. À quoi sert la commande

La table `audit_log` n'est pas créée automatiquement : l'écriture en base reste
explicite (principe 3, SQL visible).
`forge audit:init` copie la migration SQL embarquée dans le dossier
`mvc/migrations/` du projet.
Aucune connexion MariaDB ni exécution SQL à cette étape : on prépare seulement le
fichier.

```bash
forge audit:init
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

## 3. La migration

La migration crée la table avec `CREATE TABLE IF NOT EXISTS`, donc sûre même si
la table existe déjà.
La même définition est exposée par la constante `CREATE_TABLE_SQL` du module.

## 4. Voir aussi

- [Le journal d'audit](store.md) : écrire et lire une fois la table créée.
