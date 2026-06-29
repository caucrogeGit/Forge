# Bilan du niveau débutant

Vous savez démarrer une base SQL Server avec Forge (en mode Alpha).

## Ce que vous avez appris

- le cœur découvre `forge-mvc-mssql` par entry point ;
- en Alpha, base et login se créent à la main (provisioning CLI non câblé) ;
- `forge db:apply` applique le schéma sur la base existante ;
- `pyodbc` utilise les `?` nativement.

## Points clés

- SQL Server est un serveur et requiert un pilote ODBC ;
- statut Alpha : provisioning manuel, intégration à valider ;
- un seul backend BDD par projet.

## Après ce niveau

Place au niveau intermédiaire : migrations et état du support.

[Niveau intermédiaire : Migrations](../intermediaire/mssql-migrate.md)
