# La commande make:public-list dans Forge

Ce document décrit la commande `forge make:public-list`.

Le fichier de code correspondant est `cli/public/public_list.py`.

## 1. À quoi sert cette commande ?

`make:public-list` génère une liste publique paginée à partir d'une entité.
Elle s'appuie sur la définition JSON de l'entité (validée) pour choisir les champs affichés.

Les champs sensibles sont exclus de l'affichage public.
Les entrées média (couverture, galerie) sont prises en charge quand l'entité en déclare.

Ce module porte aussi la logique de `make:public-show` (fiche détaillée publique).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `public_list_fields(definition)` | champs publics affichables d'une entité |
| `public_media_entries(definition)` | entrées média publiques d'une entité |
| `PublicListSpec` / `MakePublicListResult` / `MakePublicShowResult` | structures de spécification et de résultat |
| `main(args, *, root=None)` | point d'entrée de `forge make:public-list` |
| `show_main(args, *, root=None)` | point d'entrée de `forge make:public-show` |

## 3. Contextes d'utilisation

- **Vitrine** : exposer publiquement une collection d'entités en lecture.
- **Pagination** : produire une liste navigable sans code manuel.

## 4. Voir aussi

- [La commande make:public-show](public_show.md) : fiche détaillée.
- [La commande make:public-page](public_page.md) : page statique de base.
