# Welcome Entités

Objectif : premier contact avec le **moteur d'entités**, l'opt-in `forge-mvc-entities`.

**Ce que vous allez apprendre :** une **entité** est décrite par un contrat JSON explicite, versionné avec votre code.
Ce contrat est la source unique dont Forge dérive le SQL de la table, le modèle Python et les écrans CRUD.
Rien n'est caché : vous lisez et versionnez la description, Forge se contente d'en générer les projections.

Premier palier du **niveau débutant** de la progression Entités.

!!! note "Module opt-in"
    Cette progression suppose `forge-mvc-entities` installé (palier « Installation »).
    Moteur à **SQL visible** : aucun ORM, les requêtes et le schéma restent lisibles.

## Qu'est-ce qu'une entité dans Forge

Une entité vit dans `mvc/entities/<nom>/<nom>.json`.
Le fichier déclare la forme des données ; il ne contient ni SQL, ni type de colonne, ni clé primaire.

```json
{
  "schema_version": "1.0",
  "name": "Article",
  "table": "article",
  "fields": [
    { "name": "title", "type": "string", "max_length": 255, "required": true },
    { "name": "content", "type": "text", "nullable": true }
  ]
}
```

La clé primaire `id` n'est pas déclarée : Forge l'ajoute automatiquement dans toutes les projections.
Les types sont des **types Forge** (`string`, `text`, `integer`, `foreign_key`…), pas des types SQL : c'est Forge qui les traduit pour le backend installé.

## Ce que ce palier montre

- comprendre le rôle du contrat d'entité, source unique de la couche de données ;
- situer les commandes de la progression : `make:entity`, `make:relation`, `build:model`, `make:crud`.

## Commandes Forge utilisées

| Commande | Rôle dans la progression | Référence |
|---|---|---|
| `forge make:entity` | Créer le contrat JSON d'une entité. | [make:entity](../../modules/make_entity.md) |
| `forge build:model` | Dériver le SQL et le modèle depuis le contrat. | [model](../../modules/model.md) |
| `forge make:crud` | Générer les écrans CRUD d'une entité. | [make:crud](../../modules/make_crud.md) |

## La suite

Au palier suivant, vous déclarez concrètement votre première entité avec `forge make:entity`.

[Continuer : déclarer une entité](entity-make.md)
