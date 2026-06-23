# La commande db:apply dans Forge

Ce document décrit la commande `forge db:apply`.

Le fichier de code correspondant est `cli/entities/db_apply.py`.

## 1. À quoi sert cette commande ?

`db:apply` applique le schéma SQL du modèle d'entités à la base.
Elle collecte les fichiers SQL générés à partir des entités, puis les applique avec les identifiants d'administration (`DB_ADMIN_*`).

Elle vérifie les fichiers SQL avant application.
Le SQL reste visible et inspectable (principe 5).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `apply_model_sql(entities_root)` | applique le SQL du modèle d'entités |
| `collect_sql_files(entities_root)` | rassemble les fichiers SQL à appliquer |
| `verify_sql_files(files)` | contrôle les fichiers SQL avant application |
| `DbApplyConfig` / `SqlFileToApply` | configuration et descripteur de fichier SQL |
| `DbApplyError` | exception en cas d'erreur d'application |
| `main(argv=None)` | point d'entrée de la commande `forge db:apply` |

## 3. Contextes d'utilisation

- **Création du schéma** : matérialiser les entités en tables.
- **Mise à jour structurelle** : appliquer le SQL généré après évolution du modèle.

## 4. Voir aussi

- [La commande db:init](db_init.md) : provisioning de la base et du compte.
- [Le statut des migrations](migrations.md) : suivi des migrations.
