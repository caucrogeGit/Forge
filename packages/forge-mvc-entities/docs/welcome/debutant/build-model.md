# Générer le SQL et le modèle avec `build:model`

Objectif : dériver, depuis les contrats, le SQL des tables et le modèle Python.

**Ce que vous allez apprendre :** `forge build:model` (alias `sync:entity`) lit les contrats et écrit les projections dérivées : le `.sql` de chaque entité et son modèle d'accès aux données.
Le contrat reste la source ; les projections sont régénérables.

!!! note "Projections dérivées"
    Le SQL et le modèle sont **dérivés** du contrat : on ne les édite pas à la main.
    Pour changer une colonne, on change le contrat, puis on régénère.

## Générer

```bash
forge build:model
```

Forge produit, pour chaque entité, le fichier SQL de création de table (dans `mvc/models/sql/`) et le modèle Python associé.

La clé étrangère `auteur_id` déclarée au palier précédent apparaît naturellement comme une colonne `BIGINT UNSIGNED` ; la contrainte de clé étrangère vient de `relations.json`.

## Observer le SQL généré

Ouvrez le `.sql` généré pour `Article` : les colonnes reflètent exactement le contrat, la clé primaire `id` est ajoutée, les types Forge sont traduits pour le backend installé.

Le SQL est **visible et lisible** : c'est un artefact que vous pouvez relire, versionner et auditer.

## Contrôler la cohérence

```bash
forge check:model
```

`check:model` refuse de laisser diverger un modèle généré d'un contrat modifié : il signale ce qu'il faut régénérer.

## Commandes Forge utilisées

| Commande | Rôle dans ce palier | Référence |
|---|---|---|
| `forge build:model` | Dériver le SQL et le modèle depuis les contrats. | [model](../../modules/model.md) |
| `forge check:model` | Détecter une divergence contrat / modèle généré. | [model](../../modules/model.md) |

## La suite

Le schéma et le modèle sont générés.
Au palier suivant, vous générez l'interface d'administration complète avec `forge make:crud`.

[Continuer : générer le CRUD](crud-make.md)
