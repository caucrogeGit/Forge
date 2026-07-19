# Bilan du niveau avancé

Vous comprenez le dialecte SQL Server et savez vérifier votre environnement.

## Ce que vous avez appris

- `BIGINT IDENTITY(1,1)`, identifiants entre crochets, formes gardées `IF OBJECT_ID` ;
- `?` natifs (pyodbc), `lastrowid` via `SCOPE_IDENTITY()` (même lot que l'INSERT), introspection `INFORMATION_SCHEMA` ;
- comment vérifier la chaîne complète sur un serveur de test.

## Points clés

- niveau plein (ADR-084) : provisioning par `db:init`, identité fiable, intégration validée en CI ;
- pilote ODBC indispensable ;
- un seul backend par projet (ADR-054).

## Fin du parcours

Vous maîtrisez le backend SQL Server de Forge.

[Aide-mémoire](../recapitulatif.md)
