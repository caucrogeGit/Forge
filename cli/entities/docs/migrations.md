# Les commandes migration:* dans Forge

Ce document décrit la famille de commandes `forge migration:*`.

Le fichier de code correspondant est `cli/entities/migrations.py`.

## 1. À quoi servent ces commandes ?

Ces commandes gèrent les migrations SQL du projet : statut, application, création et diff.
Une migration est un fichier SQL versionné, identifié par un *checksum* pour détecter toute altération.

Les opérations base de données utilisent les identifiants d'administration (`DB_ADMIN_*`).
Le SQL des migrations reste visible et écrit à la main ou généré explicitement (principes 3 et 5).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `build_migration_status(...)` | construit le rapport de statut des migrations |
| `build_schema_diff_report(...)` | génère un diff SQL entre entité et base |
| `migration_checksum(path)` | calcule le *checksum* d'un fichier de migration |
| `MigrationStatusReport` / `MigrationFile` / `AppliedMigration` | structures du suivi de migrations |
| `MigrationError` / `MigrationNoChange` | exceptions du domaine migrations |
| `main(argv=None)` | point d'entrée dispatchant `migration:status` / `migration:apply` / `migration:make` / `migration:diff` |

## 3. Contextes d'utilisation

- **Suivi** : connaître les migrations appliquées et en attente.
- **Évolution** : créer puis appliquer une migration SQL.
- **Comparaison** : produire un diff entre le modèle et l'état de la base.

## 4. Voir aussi

- [La commande db:apply](db_apply.md) : application du schéma SQL.
- [L'orchestration du modèle](model.md) : génération des modèles et du SQL.
