# Générer le sous-CRUD pivot

Objectif : produire un sous-CRUD dédié au pivot enrichi avec `forge make:pivot-crud`.

**Ce que vous allez apprendre :** quand une relation porte des attributs, Forge fournit un générateur dédié, `make:pivot-crud`, distinct de `make:crud`.
Il **affiche** le code à coller (contrôleur, templates, routes) sans réécrire vos fichiers (charte principe 9).

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-entities` installé.
    Module à **SQL visible**.

## Pourquoi une commande dédiée ?

`make:crud` gère une entité simple.
Dès qu'un pivot porte au moins un champ **requis** ou **non nullable**, `make:crud` est **bloqué** par un garde-fou : il faut `make:pivot-crud`, qui sait gérer les attributs de la relation.

## Classes Forge utilisées

| Commande | Rôle dans ce starter | Référence |
|----------|----------------------|-----------|
| `forge make:pivot-crud` | Génère le sous-CRUD d'un pivot enrichi. | [Pivot avancé](../../reference.md) |

!!! note "Prérequis : la relation doit exister"

    Cette page part d'une association `Article` ↔ `tags` **déjà déclarée**, avec au moins un attribut requis sur le pivot.
    Les paliers précédents la construisent en dialogue, avec vos propres noms ; pour rejouer celle-ci telle quelle :

    `Article` vient des paliers précédents ; `Tag` et la relation restent à déclarer.
    L'**attribut** du pivot se donne à la déclaration, et c'est lui qui distingue `make:pivot-crud` de `make:crud`.

    ```bash
    forge make:entity Tag --no-input
    forge make:relation --type many_to_many --from Article --to Tag --name tags \
      --pivot-field "position:integer" \
      --pivot-field "epingle:integer"
    forge build:model
    forge db:apply     # crée la table pivot en base
    ```

    Les paliers suivants lisent **ces deux attributs**, `position` et `epingle`.
    N'en déclarer qu'un fait répondre 500 à la page de liste, la requête portant alors sur une colonne absente.

    L'option `--pivot-field` est répétable et suit la grammaire de `make:entity --field`, soit `nom:type[:attributs]`.
    Le dialogue de `forge make:relation` pose la même question, un attribut par ligne, vide pour terminer.

    Sans relation déclarée, la commande répond « Entité source inconnue ».
    Sans attribut sur le pivot, elle répond « pivot.fields[] est absent ou vide » et renvoie vers `make:crud`.

## Générer (mode aperçu)

Commencez toujours par un **aperçu** `--dry-run` : rien n'est écrit, tout est affiché.

```bash
forge make:pivot-crud Article tags --dry-run
```

La sortie montre le contrôleur, les templates et les **routes** à câbler pour le sous-CRUD de l'association `Article` ↔ `tags`.

## Générer (réel)

```bash
forge make:pivot-crud Article tags
```

Les **fichiers nouveaux** sont créés, dont un fichier de routes dédié sous `mvc/routes/` (ADR-068) ; le branchement à ajouter dans `mvc/routes/__init__.py` est **affiché** (Forge ne réécrit jamais vos routes en silence).

### Comprendre ce code

- Le générateur produit un sous-CRUD : lister les tags d'un article, en attacher, modifier l'attribut, détacher : exactement les opérations de pivot.
- Le code généré s'appuie sur `PivotAdvancedService`, que vous manipulerez directement quelques paliers plus loin.
- `--dry-run` est la bonne habitude : on lit avant d'écrire.

## À retenir

- `make:pivot-crud <Source> <relation>` génère le sous-CRUD d'un pivot enrichi.
- `make:crud` est **bloqué** pour les pivots à attributs requis/non nullables.
- `--dry-run` affiche sans rien écrire.

## Après ce starter

Le code est généré.
Voyons le **stockage** : la table pivot en SQL.

[Le schéma SQL du pivot](pivot-schema.md)
