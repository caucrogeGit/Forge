# La pagination dans Forge

Ce document décrit l'objet de pagination des vues liste.

Le fichier de code correspondant est `core/mvc/view/pagination.py`.

## 1. À quoi sert ce module ?

Afficher une liste par pages demande de calculer la page courante, le nombre de pages, les bornes.
`Pagination` encapsule cette logique pour les vues liste.

## 2. L'objet

| Élément | Rôle |
|---|---|
| `Pagination` | encapsule la logique de pagination (page courante, total, bornes, navigation) |

## 3. Contextes d'utilisation

- **Vue liste** : paginer un jeu de résultats et fournir les liens page précédente/suivante au gabarit.

## 4. Voir aussi

- [Le contrôleur de base](base_controller.md) : passe la pagination au contexte de rendu.
