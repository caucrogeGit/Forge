# Bilan du niveau débutant

Vous savez démarrer une base PostgreSQL avec Forge.

## Ce que vous avez appris

- le cœur découvre `forge-mvc-postgres` par entry point ;
- `forge db:init` affiche le SQL de provisioning et `--run` l'exécute ;
- `forge db:apply` applique le schéma sur la base provisionnée ;
- les paramètres `?` sont traduits en `%s` pour psycopg.

## Points clés

- PostgreSQL est un serveur : il faut une connexion ;
- niveau plein (ADR-084) : provisioning par la CLI, intégration validée en CI ;
- un seul backend BDD par projet.

## Après ce niveau

Place au niveau intermédiaire : migrations et état du support.

[Niveau intermédiaire : Migrations](../intermediaire/postgres-migrate.md)
