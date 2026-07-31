# Pourquoi dev-only

Objectif : comprendre pourquoi `forge-mvc-testing` ne doit jamais être une dépendance runtime.

**Ce que vous allez apprendre :** la frontière entre outillage de test et code de production.

Deuxième palier du **niveau avancé**.

## Le principe

Le code de test (fixtures, fausses requêtes, faux exécuteurs) n'a rien à faire en production : il alourdirait l'application et exposerait des mécanismes de test.

`forge-mvc-testing` est donc déclaré comme dépendance de **développement** (ADR-041), pas dans les dépendances du projet.

## En pratique

| Où | Faut-il le paquet ? |
|---|---|
| `requirements-dev` (dev, CI) | oui |
| Dépendances du projet (production) | non |
| Import dans `mvc/` (code applicatif) | non |

## Vérifier

```bash
if grep -rq "forge_mvc_testing" mvc/; then
    echo "FUITE : l'application importe le paquet de test"
    exit 1
fi
echo "OK : aucune fuite"
```

Aucun fichier de l'application ne doit importer le paquet de test.

La forme est un peu plus longue qu'un `grep` nu, et c'est délibéré.
`grep` sort en **code 1** quand il ne trouve rien, c'est-à-dire dans le cas qui nous convient : posé tel quel dans un script ou une intégration continue, il signalerait un échec au moment même où tout va bien.
Ce bloc se colle donc sans surprise dans une vérification automatisée.

!!! warning "Ne pas fuiter en production"
    Si `forge-mvc-testing` apparaît dans les dépendances runtime, retirez-le : il appartient au développement.

!!! note "Cohérence avec la charte"
    Séparer test et production suit le principe de frontières nettes : l'outil de test dépend du cœur, jamais l'inverse, et n'entre pas dans le livrable.

## Après cette étape

[Bilan du niveau avancé](bilan.md)
