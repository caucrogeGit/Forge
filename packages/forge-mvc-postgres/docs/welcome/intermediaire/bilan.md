# Bilan du niveau intermédiaire

Vous savez faire évoluer le schéma PostgreSQL et vous connaissez le niveau de support.

## Ce que vous avez appris

- `migration:status` / `migration:make` / `migration:apply` fonctionnent sur PostgreSQL ;
- ce qui est garanti au niveau plein (provisioning, identité d'insertion, couche BDD, migrations, runtime) ;
- les limites restantes (`DB_APP_PRIVILEGES` refusé au-delà du DML, diff incrémental imparfait).

## Points clés

- niveau plein (ADR-084) : `db:init` provisionne la base, le reste suit le flux du cœur ;
- les commandes `migration:*` sont identiques aux autres backends ;
- l'intégration est validée en CI contre un vrai PostgreSQL 16.

## Après ce niveau

Place au niveau avancé : dialecte et vérification.

[Niveau avancé : Le dialecte PostgreSQL](../avance/postgres-dialect.md)
