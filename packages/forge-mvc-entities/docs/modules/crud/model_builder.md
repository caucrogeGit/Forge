# Le builder de modèle CRUD dans Forge

Ce document décrit le *builder* de modèle du générateur CRUD.

Le fichier de code correspondant est `cli/entities/crud/model_builder.py`.

## 1. À quoi sert ce module ?

Il génère le code du modèle CRUD d'une entité.
Il produit les accès aux données avec du SQL visible (principe 5), en tenant compte des relations.

C'est une brique appelée par `make:crud`.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `build_model(...)` | produit le code du modèle CRUD |

## 3. Contextes d'utilisation

- **Génération CRUD** : produire le modèle d'une entité.
- **Relations** : intégrer les jointures et sélections liées.

## 4. Voir aussi

- [Le builder de contrôleur](controller_builder.md) : génération du contrôleur.
- [Le chargeur de relations](relations_loader.md) : construction des relations CRUD.
