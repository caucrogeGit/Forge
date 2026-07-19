# Vérifier votre environnement

Objectif : confirmer que PostgreSQL fonctionne de bout en bout sur votre serveur.

**Ce que vous allez apprendre :** comment vérifier la chaîne complète sur votre environnement ; la CI de Forge la valide déjà en amont contre un vrai PostgreSQL 16.

Deuxième palier du **niveau avancé**.

## Démarrer un serveur de test

Le plus simple est un conteneur Docker jetable :

```bash
docker run --rm -e POSTGRES_PASSWORD=test -p 5432:5432 postgres
```

Configurez `env/dev` pour pointer ce serveur (`DB_HOST=127.0.0.1`, `DB_PORT=5432`, etc.).

## Vérifier la chaîne

1. provisionner la base (`forge db:init --run`) ;
2. `forge db:apply` (création de tables) ;
3. une migration (`migration:make` puis `migration:apply`) ;
4. lecture/écriture via `core.database.db`.

Si ces quatre étapes passent, la chaîne est bonne sur votre serveur.

## Ce que la CI de Forge couvre déjà

- la couche BDD (insertion, lecture, `rowcount`, anti-injection, transactions, clés étrangères) ;
- le runner de migrations (application, idempotence, dry-run, refus CHANGED, rollback réel, introspection `information_schema`).

Cette vérification locale contrôle donc votre environnement (serveur, réseau, comptes), pas le backend lui-même.

!!! note "Remonter les écarts"
    Documenter un écart rencontré sur votre serveur aide à améliorer le backend.

!!! warning "Ne pas confondre dev et prod"
    Un conteneur jetable convient au test ; en production, utilisez un serveur PostgreSQL géré, sauvegardé et restreint.

## Après cette étape

[Bilan du niveau avancé](bilan.md)
