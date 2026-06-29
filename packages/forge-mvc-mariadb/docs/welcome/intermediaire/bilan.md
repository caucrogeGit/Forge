# Bilan du niveau intermédiaire

Vous savez faire évoluer le schéma MariaDB et vous comprenez les deux comptes.

## Ce que vous avez appris

- `migration:status` / `migration:make` / `migration:apply` / `migration:diff` ;
- la table `forge_migrations` trace les migrations ;
- `DB_ADMIN_*` (structure) et `DB_APP_*` (runtime, DML) sont séparés (ADR-033).

## Points clés

- les commandes `migration:*` sont celles du cœur, identiques quel que soit le backend ;
- la DDL passe par le compte admin, le runtime par le compte applicatif ;
- le compte runtime limité au DML est une sécurité par défaut.

## Après ce niveau

Place au niveau avancé : dialecte et production.

[Niveau avancé : Le dialecte MariaDB](../avance/mariadb-dialect.md)
