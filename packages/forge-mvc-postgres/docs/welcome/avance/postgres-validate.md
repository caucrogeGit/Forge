# Valider l'intégration

Objectif : confirmer que PostgreSQL fonctionne de bout en bout sur votre serveur.

**Ce que vous allez apprendre :** comment vérifier la chaîne complète, puisque l'intégration est à valider (Alpha).

Deuxième palier du **niveau avancé**.

## Démarrer un serveur de test

Le plus simple est un conteneur Docker jetable :

```bash
docker run --rm -e POSTGRES_PASSWORD=test -p 5432:5432 postgres
```

Configurez `env/dev` pour pointer ce serveur (`DB_HOST=127.0.0.1`, `DB_PORT=5432`, etc.).

## Vérifier la chaîne

1. créer base et rôle (palier débutant) ;
2. `forge db:apply` (création de tables) ;
3. une migration (`migration:make` puis `migration:apply`) ;
4. lecture/écriture via `core.database.db`.

Si ces quatre étapes passent, l'intégration runtime est bonne sur votre serveur.

## Ce qui n'est pas couvert

- le provisioning par `db:init` (création automatique base + rôle) ;
- le diff incrémental fin (noms de types PostgreSQL).

!!! note "Remonter les écarts"
    Documenter ce qui marche ou casse sur un vrai serveur aide à faire passer le backend de Alpha à bêta.

!!! warning "Ne pas confondre dev et prod"
    Un conteneur jetable convient au test ; en production, utilisez un serveur PostgreSQL géré, sauvegardé et restreint.

## Après cette étape

[Bilan du niveau avancé](bilan.md)
