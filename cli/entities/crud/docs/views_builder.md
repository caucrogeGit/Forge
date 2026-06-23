# Les builders de vues CRUD dans Forge

Ce document décrit les *builders* de vues du générateur CRUD.

Le fichier de code correspondant est `cli/entities/crud/views_builder.py`.

## 1. À quoi sert ce module ?

Il génère les vues et fragments du CRUD : mise en page, liste, fiche, formulaire, pagination, partiels d'erreurs et de résultats.
Il regroupe toutes les fonctions `build_*_view` et `build_*_partial`.

C'est la brique d'affichage appelée par `make:crud`.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `build_layout()` | mise en page de l'application |
| `build_index_view(...)` | vue liste |
| `build_show_view(...)` | vue fiche |
| `build_form_view(...)` | vue formulaire |
| `build_table_partial(...)` / `build_results_partial(...)` / `build_pagination_partial(...)` | fragments de liste |
| `build_form_errors_partial()` | fragment d'erreurs de formulaire |

## 3. Contextes d'utilisation

- **Génération CRUD** : produire l'ensemble des gabarits d'une entité.
- **Fragments htmx** : générer les partiels rechargés sans page complète.

## 4. Voir aussi

- [Le builder de contrôleur](controller_builder.md) : génération du contrôleur.
- [Le builder de formulaire](form_builder.md) : génération du formulaire.
