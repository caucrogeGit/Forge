# Le builder de formulaire CRUD dans Forge

Ce document décrit le *builder* de formulaire du générateur CRUD.

Le fichier de code correspondant est `cli/entities/crud/form_builder.py`.

## 1. À quoi sert ce module ?

Il génère le code du formulaire CRUD d'une entité.
Il choisit la classe de champ et les contraintes selon le type de chaque champ de l'entité.

Il prend en charge les relations `many_to_one` (sélecteurs).
C'est une brique appelée par `make:crud`.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `build_form(...)` | produit le code du formulaire CRUD |

## 3. Contextes d'utilisation

- **Génération CRUD** : produire le formulaire d'une entité.
- **Saisie reliée** : générer les sélecteurs des relations `many_to_one`.

## 4. Voir aussi

- [Le builder de contrôleur](controller_builder.md) : génération du contrôleur.
- [Les helpers de champs](utils.md) : helpers de typage des champs.
