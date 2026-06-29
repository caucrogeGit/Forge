# Bilan du niveau avancé

Vous comprenez le dialecte MariaDB et son exploitation en production.

## Ce que vous avez appris

- `INT AUTO_INCREMENT` + `PRIMARY KEY`, `ENGINE=InnoDB`, `utf8mb4`, index inline, backticks ;
- le pool de connexions thread-safe pour un serveur multi-workers ;
- provisioning unique avec `DB_ADMIN_*`, runtime avec `DB_APP_*` ;
- migrations explicites au déploiement, articulation avec `forge-mvc-deploy`.

## Points clés

- MariaDB = backend de production de référence, client-serveur ;
- deux comptes (admin / applicatif), DML strict au runtime ;
- un seul backend par projet (ADR-054).

## Fin du parcours

Vous maîtrisez le backend MariaDB de Forge.

[Aide-mémoire](../recapitulatif.md)
