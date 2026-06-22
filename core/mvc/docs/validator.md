# Le validateur de modèle dans Forge

Ce document décrit la classe de base de validation de formulaires côté modèle.

Le fichier de code correspondant est `core/mvc/model/validator.py`.

## 1. À quoi sert ce module ?

`Validator` est une classe de base pour valider des données de formulaire au niveau modèle.

## 2. L'objet

| Élément | Rôle |
|---|---|
| `Validator` | classe de base pour la validation de formulaires |

## 3. Contextes d'utilisation

- **Modèle** : dériver `Validator` pour des règles de validation propres à une entité.

## 4. Voir aussi

- [L'erreur de doublon](exceptions.md) : `DoublonError`.
- [Les formulaires (core/forms)](../core-forms/form.md).
