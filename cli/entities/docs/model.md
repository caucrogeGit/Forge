# Les commandes build:model, check:model et sync:entity dans Forge

Ce document décrit l'orchestration du modèle d'entités.

Le fichier de code correspondant est `cli/entities/model.py`.

## 1. À quoi sert ce module ?

Il orchestre la génération des modèles Python et du SQL à partir des entités JSON.
Il porte plusieurs commandes : `build:model` (régénère tous les modèles), `check:model` (vérifie la cohérence), `sync:entity` et `sync:relations` (régénèrent un fichier ciblé).

La génération s'appuie sur des contrats validés au préalable.
Un mode dry-run permet de prévisualiser sans écrire.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `build_model(entities_root, *, dry_run=False)` | régénère l'ensemble des modèles |
| `check_model(...)` | vérifie la cohérence des modèles |
| `sync_entity(entities_root, entity_name)` | régénère les fichiers d'une entité |
| `sync_relations(entities_root)` | régénère `relations.sql` |
| `BuildModelResult` / `EntitySource` | résultat de build et descripteur de source |
| `ModelValidationError` | exception en cas de contrat invalide |
| `main(argv=None)` | point d'entrée dispatchant les commandes de modèle |

## 3. Contextes d'utilisation

- **Régénération** : reconstruire les modèles après modification des entités.
- **Cohérence** : vérifier que les modèles reflètent les entités (`check:model`).

## 4. Voir aussi

- [Les relations globales](relations.md) : validation et génération du SQL de relations.
- [Le normaliseur canonique](canonical_model_normalizer.md) : traduction vers la structure interne.
