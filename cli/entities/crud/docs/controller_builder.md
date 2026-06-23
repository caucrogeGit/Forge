# Le builder de contrôleur CRUD dans Forge

Ce document décrit le *builder* de contrôleur du générateur CRUD.

Le fichier de code correspondant est `cli/entities/crud/controller_builder.py`.

## 1. À quoi sert ce module ?

Il génère le code du contrôleur CRUD d'une entité.
Il prend en compte les relations et, le cas échéant, les téléversements de médias.

C'est l'une des briques appelées par `make:crud` pour produire le scaffolding.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `build_controller(...)` | produit le code du contrôleur CRUD |

## 3. Contextes d'utilisation

- **Génération CRUD** : produire le contrôleur d'une entité.
- **Relations** : intégrer les liens `many_to_one` et `many_to_many` au contrôleur.

## 4. Voir aussi

- [Le builder de modèle](model_builder.md) : génération du modèle.
- [Le builder de formulaire](form_builder.md) : génération du formulaire.
