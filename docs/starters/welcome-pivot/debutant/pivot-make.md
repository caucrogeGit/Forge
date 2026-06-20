# Générer le sous-CRUD pivot

Objectif : produire un sous-CRUD dédié au pivot enrichi avec `forge make:pivot-crud`.

**Ce que vous allez apprendre :** quand une relation porte des attributs, Forge
fournit un générateur dédié, `make:pivot-crud`, distinct de `make:crud`. Il
**affiche** le code à coller (contrôleur, templates, routes) sans réécrire vos
fichiers (charte principe 9).

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-pivot` installé. Module à **SQL visible**.

## Pourquoi une commande dédiée ?

`make:crud` gère une entité simple. Dès qu'un pivot porte au moins un champ
**requis** ou **non nullable**, `make:crud` est **bloqué** par un garde-fou : il
faut `make:pivot-crud`, qui sait gérer les attributs de la relation.

## Classes Forge utilisées

| Commande | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `forge make:pivot-crud` | Génère le sous-CRUD d'un pivot enrichi. | [Pivot avancé](../../../entities/pivot-advanced.md) |

## Générer (mode aperçu)

Commencez toujours par un **aperçu** `--dry-run` : rien n'est écrit, tout est affiché.

```bash
forge make:pivot-crud Article tags --dry-run
```

La sortie montre le contrôleur, les templates et les **routes** à câbler pour le
sous-CRUD de l'association `Article` ↔ `tags`.

## Générer (réel)

```bash
forge make:pivot-crud Article tags
```

Les **fichiers nouveaux** sont créés ; les routes à ajouter dans `mvc/routes.py`
sont **affichées** (Forge ne réécrit jamais vos routes en silence).

### Comprendre ce code

- Le générateur produit un sous-CRUD : lister les tags d'un article, en attacher,
  modifier l'attribut, détacher — exactement les opérations de pivot.
- Le code généré s'appuie sur `PivotAdvancedService`, que vous manipulerez
  directement au niveau intermédiaire.
- `--dry-run` est la bonne habitude : on lit avant d'écrire.

## À retenir

- `make:pivot-crud <Source> <relation>` génère le sous-CRUD d'un pivot enrichi.
- `make:crud` est **bloqué** pour les pivots à attributs requis/non nullables.
- `--dry-run` affiche sans rien écrire.

## Après ce starter

Le code est généré. Voyons le **stockage** : la table pivot en SQL.

[Le schéma SQL du pivot](pivot-schema.md)
