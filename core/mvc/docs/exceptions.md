# L'erreur de doublon dans Forge

Ce document décrit l'exception levée sur violation d'unicité côté modèle.

Le fichier de code correspondant est `core/mvc/model/exceptions.py`.

## 1. À quoi sert ce module ?

Quand une contrainte d'unicité est violée (insérer un enregistrement déjà existant), le modèle lève une erreur identifiable.

## 2. L'objet

| Élément | Rôle |
|---|---|
| `DoublonError` | levée par un modèle quand une contrainte d'unicité est violée |

## 3. Contextes d'utilisation

- **Insertion / mise à jour** : attraper `DoublonError` pour afficher un message d'unicité.

## 4. Voir aussi

- [Le validateur de modèle](validator.md).
