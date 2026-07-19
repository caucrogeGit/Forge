# Bilan du niveau intermédiaire

Vous savez faire évoluer le schéma SQL Server et vous connaissez le périmètre du support.

## Ce que vous avez appris

- `migration:status` / `migration:make` / `migration:apply` fonctionnent sur SQL Server ;
- ce qui est garanti (provisioning `db:init`, dialecte, paramètres natifs, `db:apply`, migrations et runtime validés en CI) ;
- ce qui reste à votre charge (pilote ODBC système, compte `DB_ADMIN_*` existant).

## Points clés

- niveau plein (ADR-084) : `db:init` provisionne, le reste suit le flux du cœur ;
- les formes gardées remplacent `IF NOT EXISTS` ;
- l'escape hatch `DB_APP_PRIVILEGES` au-delà du DML reste propre à MariaDB.

## Après ce niveau

Place au niveau avancé : dialecte et validation.

[Niveau avancé : Le dialecte SQL Server](../avance/mssql-dialect.md)
