# Le normaliseur canonique du modèle dans Forge

Ce document décrit le normaliseur du format canonique vers la structure interne de `build:model`.

Le fichier de code correspondant est `cli/entities/canonical_model_normalizer.py`.

## 1. À quoi sert ce module ?

Il traduit une entité au format canonique (`schema_version: "1.0"`) en un dict compatible avec les générateurs internes.
C'est une couche de **transition** interne, pas un format public.

La structure produite alimente la validation et les générateurs de SQL et de modèles.
Elle suit le format interne attendu, sans exposer ce format aux utilisateurs.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `normalize_canonical_entity_for_model_build(entity)` | traduit une entité canonique vers la structure interne |
| `CanonicalNormalizationError` | exception en cas d'entité canonique invalide |

## 3. Contextes d'utilisation

- **Build du modèle** : préparer une entité canonique pour les générateurs internes.
- **Transition** : faire le pont entre le format public et la structure interne.

## 4. Voir aussi

- [L'orchestration du modèle](model.md) : consommateur de ce normaliseur.
- [La validation canonique](validation.md) : validation du format canonique.
