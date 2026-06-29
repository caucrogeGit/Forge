# Bilan du niveau avancé

Vous comprenez le dialecte SQLite et savez quand l'utiliser.

## Ce que vous avez appris

- la clé primaire `INTEGER PRIMARY KEY AUTOINCREMENT` et les `CREATE INDEX` séparés ;
- les affinités de types de SQLite ;
- les contextes où SQLite est idéal, et quand préférer un serveur ;
- changer de backend ne change pas le code applicatif (ADR-054).

## Points clés

- SQLite = développement, tests, onboarding, petites applications ;
- serveur (MariaDB/PostgreSQL) = production multi-utilisateurs / multi-process ;
- un seul backend par projet, SQL natif assumé.

## Fin du parcours

Vous maîtrisez le backend SQLite de Forge.

[Aide-mémoire](../recapitulatif.md)
