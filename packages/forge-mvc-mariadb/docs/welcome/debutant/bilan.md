# Bilan du niveau débutant

Vous savez provisionner et alimenter une base MariaDB avec Forge.

## Ce que vous avez appris

- le cœur découvre `forge-mvc-mariadb` par entry point ;
- `forge db:init` crée la base et le compte applicatif via `DB_ADMIN_*` ;
- `forge db:apply` applique le schéma d'une entité (DDL, compte admin) ;
- le code utilise `core.database.db`, jamais le pilote `mariadb` directement.

## Points clés

- MariaDB est un serveur : il faut une connexion et un compte admin ;
- deux comptes : `DB_ADMIN_*` (structure) et `DB_APP_*` (runtime) ;
- un seul backend BDD par projet.

## Après ce niveau

Place au niveau intermédiaire : migrations et comptes.

[Niveau intermédiaire : Migrations](../intermediaire/mariadb-migrate.md)
