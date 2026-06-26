# L'initialisation : `forge settings:init`

Ce document décrit la commande qui installe la table des paramètres.

Le fichier de code correspondant est `forge_mvc_settings/cli/init.py`.

## 1. À quoi sert la commande

La table `app_settings` n'est pas créée automatiquement : c'est une écriture en
base, donc elle reste explicite et visible (principe 3, SQL visible).
`forge settings:init` copie la migration SQL embarquée dans le paquet vers le
dossier `mvc/migrations/` du projet.
Aucune connexion MariaDB, aucune exécution SQL à cette étape : on prépare
seulement le fichier.

```bash
forge settings:init
forge migration:apply
```

`forge migration:apply` applique ensuite la migration et crée la table.

## 2. Comportement

La commande est idempotente et ne réécrit jamais en silence :

- un fichier absent est copié (`[OK]`) ;
- un fichier déjà présent et identique est laissé tel quel (`[OK]`) ;
- un fichier présent mais au contenu différent déclenche un `[WARN]` et n'est
  pas écrasé.

Si le dossier `mvc/` est absent, la commande s'arrête avec un message clair
(`[ERREUR]`) : elle doit être lancée à la racine d'un projet Forge.

## 3. La migration

La migration crée la table avec `CREATE TABLE IF NOT EXISTS`, ce qui la rend
sûre même si la table existe déjà.
La même définition est exposée par la constante `CREATE_TABLE_SQL` du module,
pour inspection ou usage programmatique.

## 4. Voir aussi

- [Les paramètres](store.md) : lire et écrire une fois la table créée.
