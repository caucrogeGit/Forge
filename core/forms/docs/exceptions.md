# L'erreur de validation de formulaire dans Forge

Ce document décrit l'exception de validation affichable par un formulaire.

Le fichier de code correspondant est `core/forms/exceptions.py`.

## 1. À quoi sert ce module ?

Quand un champ refuse une valeur, le formulaire lève une `ValidationError` portant un message destiné à être **affiché** à l'utilisateur.

## 2. L'objet

| Élément | Rôle |
|---|---|
| `ValidationError` | erreur de validation affichable par un formulaire Forge |

## 3. Contextes d'utilisation

- **Champ** : levée pendant la conversion/validation, collectée dans `Form.errors`.

## 4. Voir aussi

- [Les formulaires](form.md) et [les champs](fields.md).
