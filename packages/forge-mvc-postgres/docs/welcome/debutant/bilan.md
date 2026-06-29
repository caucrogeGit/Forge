# Bilan du niveau débutant

Vous savez démarrer une base PostgreSQL avec Forge (en mode Alpha).

## Ce que vous avez appris

- le cœur découvre `forge-mvc-postgres` par entry point ;
- en Alpha, base et rôle se créent à la main (provisioning CLI non câblé) ;
- `forge db:apply` applique le schéma sur la base existante ;
- les paramètres `?` sont traduits en `%s` pour psycopg.

## Points clés

- PostgreSQL est un serveur : il faut une connexion ;
- statut Alpha : provisioning manuel, intégration à valider ;
- un seul backend BDD par projet.

## Après ce niveau

Place au niveau intermédiaire : migrations et état du support.

[Niveau intermédiaire : Migrations](../intermediaire/postgres-migrate.md)
