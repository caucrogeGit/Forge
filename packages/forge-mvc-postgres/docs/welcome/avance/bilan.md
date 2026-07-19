# Bilan du niveau avancé

Vous comprenez le dialecte PostgreSQL et savez vérifier la chaîne sur votre environnement.

## Ce que vous avez appris

- `BIGSERIAL`, `CREATE INDEX` séparés, guillemets doubles, `information_schema` ;
- la traduction des paramètres `?` vers `%s` et `lastrowid` via `lastval()` sous garde savepoint ;
- comment vérifier la chaîne complète sur un serveur de test ;
- ce que la CI de Forge couvre déjà (couche BDD et runner de migrations contre PostgreSQL 16).

## Points clés

- niveau plein (ADR-084) : provisioning par `db:init`, intégration validée en CI ;
- le SQL reste celui de Forge, adapté au format psycopg ;
- un seul backend par projet (ADR-054).

## Fin du parcours

Vous maîtrisez l'état actuel du backend PostgreSQL de Forge.

[Aide-mémoire](../recapitulatif.md)
