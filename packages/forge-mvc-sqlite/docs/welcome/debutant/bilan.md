# Bilan du niveau débutant

Vous savez maintenant démarrer une base SQLite avec Forge.

## Ce que vous avez appris

- le cœur découvre `forge-mvc-sqlite` par entry point, sans configuration ;
- `forge db:init` crée le fichier de base (sans serveur) ;
- `forge db:apply` applique le schéma d'une entité ;
- le code utilise `core.database.db`, jamais `sqlite3` directement.

## Points clés

- une base SQLite = un fichier (`DB_NAME`) ;
- aucun serveur, aucun compte : `requires_provisioning=False` ;
- un seul backend BDD par projet.

## Après ce niveau

Place au niveau intermédiaire : faire évoluer le schéma par migrations.

[Niveau intermédiaire : Migrations](../intermediaire/sqlite-migrate.md)
