# Les relations globales dans Forge

Ce document décrit la validation et la génération des relations globales.

Le fichier de code correspondant est `cli/entities/relations.py`.

## 1. À quoi sert ce module ?

Il valide les relations déclarées entre entités et en génère le SQL global.
Il résout les champs concernés, vérifie la cohérence des liens et signale les problèmes rencontrés.

Il prend en charge les relations `many_to_one` et les relations `many_to_many` canoniques (pivot enrichi).
Le SQL produit reste visible (principe 5).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `ValidatedRelation` / `ValidatedCanonicalManyToManyRelation` | relations validées |
| `ResolvedEntityField` / `ValidatedPivotField` | champs résolus et champs de pivot |
| `RelationIssue` | problème détecté sur une relation |
| `EntityRelationsError` | exception en cas de relations invalides |

## 3. Contextes d'utilisation

- **Validation** : vérifier la cohérence globale des relations du projet.
- **Génération** : produire le SQL des relations entre entités.

## 4. Voir aussi

- [L'orchestration du modèle](model.md) : `sync:relations` et build du modèle.
- [La commande make:relation](make_relation.md) : déclaration interactive d'une relation.
