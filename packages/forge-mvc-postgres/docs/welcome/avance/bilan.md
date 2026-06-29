# Bilan du niveau avancé

Vous comprenez le dialecte PostgreSQL et savez valider l'intégration.

## Ce que vous avez appris

- `BIGSERIAL`, `CREATE INDEX` séparés, guillemets doubles, `information_schema` ;
- la traduction des paramètres `?` vers `%s` et `lastrowid` via `lastval()` ;
- comment vérifier la chaîne complète sur un serveur de test ;
- ce qui n'est pas couvert (provisioning CLI, diff fin).

## Points clés

- statut Alpha : dialecte et runtime fonctionnels, provisioning et intégration à finaliser ;
- le SQL reste celui de Forge, adapté au format psycopg ;
- un seul backend par projet (ADR-054).

## Fin du parcours

Vous maîtrisez l'état actuel du backend PostgreSQL de Forge.

[Aide-mémoire](../recapitulatif.md)
