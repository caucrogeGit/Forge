# Cadrer par environnement

Objectif : comprendre quel environnement les fixtures visent et pourquoi la production est protégée.

**Ce que vous allez apprendre :** `fixtures:load` et `fixtures:purge` agissent sur la base de l'environnement actif, et refusent la production sans geste explicite.

## L'environnement actif

Forge choisit l'environnement avec la variable `APP_ENV` (défaut `dev`).
Les commandes de fixtures visent la base de cet environnement : en `dev`, elles chargent dans votre base de développement.

```bash
forge fixtures:load --run          # charge dans dev
APP_ENV=test forge fixtures:load --run   # charge dans test
```

Les fixtures sont ainsi **cadrées par environnement** : les mêmes fichiers peuplent la base de l'environnement que vous ciblez.

## La production est protégée

Charger ou purger des données de démonstration en production est presque toujours une erreur.
Aussi, en `APP_ENV=prod`, `--run` seul est **refusé** :

```bash
APP_ENV=prod forge fixtures:load --run
# Refus : chargement de fixtures en environnement 'prod'. Ajoutez --force pour confirmer.
```

Il faut un geste explicite supplémentaire :

```bash
APP_ENV=prod forge fixtures:load --run --force
```

Ce double garde-fou évite d'écraser une base de production par distraction.

## Bonne pratique

Gardez les fixtures pour `dev` et `test`.
En production, le référentiel permanent passe par une migration de seed, pas par des fixtures.

## Commandes utilisées

| Situation | Commande |
|---|---|
| Charger en dev | `forge fixtures:load --run` |
| Charger dans un autre environnement | `APP_ENV=test forge fixtures:load --run` |
| Forcer en production (rare) | `APP_ENV=prod forge fixtures:load --run --force` |

## La suite

Faisons le bilan du niveau intermédiaire.

[Continuer : bilan du niveau intermédiaire](bilan.md)
