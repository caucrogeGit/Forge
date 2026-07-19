# Bilan du niveau débutant

Vous savez démarrer une base SQL Server avec Forge.

## Ce que vous avez appris

- le cœur découvre `forge-mvc-mssql` par entry point ;
- `forge db:init` affiche le SQL de provisioning et `--run` l'exécute (compte `DB_ADMIN_*` existant) ;
- `forge db:apply` applique le schéma des entités ;
- `pyodbc` utilise les `?` nativement.

## Points clés

- SQL Server est un serveur et requiert un pilote ODBC ;
- niveau plein (ADR-084) : provisioning par `db:init`, intégration validée en CI ;
- un seul backend BDD par projet.

## Après ce niveau

Place au niveau intermédiaire : migrations et état du support.

[Niveau intermédiaire : Migrations](../intermediaire/mssql-migrate.md)
