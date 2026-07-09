# Relier deux entités avec `make:relation`

Objectif : ajouter une relation `many_to_one` d'`Article` vers une entité `Auteur`.

**Ce que vous allez apprendre :** `forge make:relation` déclare une relation entre entités, et pour un `many_to_one` il **injecte la clé étrangère comme champ** de l'entité source.
La clé étrangère devient un champ d'entité de première classe (type `foreign_key`), visible dans le contrat.

!!! note "La clé étrangère est un champ"
    Depuis l'ADR-069, une relation `many_to_one` ajoute un champ `foreign_key` dans le contrat de l'entité source.
    L'écriture est chirurgicale et annoncée (`[MODIFIE]`), les autres champs sont préservés.

## Déclarer l'entité cible

D'abord, une entité `Auteur` à relier.

```bash
forge make:entity Auteur
```

Complétez son contrat, par exemple avec un champ `name`.

## Créer la relation

```bash
forge make:relation
```

L'assistant interactif demande le type (`many_to_one`), l'entité source (`Article`), l'entité cible (`Auteur`) et l'action `ON DELETE`.

Forge écrit alors deux choses :

- la relation dans `mvc/entities/relations.json` (contrainte, `on_delete`, cardinalité) ;
- un champ `foreign_key` dans le contrat d'`Article`, par exemple `auteur_id`.

```json
{ "name": "auteur_id", "type": "foreign_key", "references": "Auteur", "required": true }
```

Le champ adopte le type de la clé primaire visée (`BIGINT UNSIGNED` sur MariaDB, backend-agnostique), avec une colonne snake_case fidèle au dictionnaire.

## Vérifier

```bash
forge entity:validate
```

La clé étrangère est désormais un champ comme les autres : le contrat d'`Article` la montre, et tout l'outillage la gère uniformément.

## Commandes Forge utilisées

| Commande | Rôle dans ce palier | Référence |
|---|---|---|
| `forge make:relation` | Déclarer la relation et injecter la clé étrangère. | [make:relation](../../modules/make_relation.md) |
| `forge entity:validate` | Vérifier la cohérence des relations déclarées. | [entity:validate](../../modules/entity_validate.md) |

## La suite

Vos entités sont déclarées et reliées.
Au palier suivant, vous générez leur SQL et leur modèle Python avec `forge build:model`.

[Continuer : générer le SQL et le modèle](build-model.md)
