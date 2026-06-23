# La validation canonique des entités dans Forge

Ce document décrit la validation canonique des fichiers JSON d'entité.

Le fichier de code correspondant est `cli/entities/validation.py`.

## 1. À quoi sert ce module ?

Il valide la structure et les valeurs d'une définition d'entité au format canonique.
Il contrôle par exemple la casse des noms (PascalCase pour l'entité, `snake_case` pour les champs) et la cohérence des types.

C'est une brique de validation réutilisée par les commandes de génération et de modèle.
Il propose des suggestions (via `difflib`) en cas de valeur proche d'une valeur attendue.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `EntityDefinitionIssue` | problème unitaire détecté dans une définition |
| `EntityDefinitionError` | exception agrégeant les problèmes de validation |

Le module expose la validation d'une définition d'entité et les structures d'erreur associées.

## 3. Contextes d'utilisation

- **Génération** : valider une entité avant de produire modèles et SQL.
- **Diagnostic** : signaler précisément un champ ou un nom invalide.

## 4. Voir aussi

- [La commande entity:validate](entity_validate.md) : validation complète des entités.
- [Le normaliseur canonique](canonical_model_normalizer.md) : traduction vers la structure interne.
