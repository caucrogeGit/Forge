# Bilan du niveau avancé

Vous comprenez le dialecte SQL Server et savez valider l'intégration.

## Ce que vous avez appris

- `BIGINT IDENTITY(1,1)`, identifiants entre crochets, formes gardées `IF OBJECT_ID` ;
- `?` natifs (pyodbc), `lastrowid` via `SCOPE_IDENTITY()`, introspection `INFORMATION_SCHEMA` ;
- comment vérifier la chaîne complète sur un serveur de test ;
- ce qui n'est pas couvert (provisioning CLI, diff fin).

## Points clés

- statut Alpha : dialecte et runtime fonctionnels, provisioning et intégration à finaliser ;
- pilote ODBC indispensable ;
- un seul backend par projet (ADR-054).

## Fin du parcours

Vous maîtrisez l'état actuel du backend SQL Server de Forge.

[Aide-mémoire](../recapitulatif.md)
