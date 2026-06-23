# La commande make:public-show dans Forge

Ce document décrit la commande `forge make:public-show`.

Le fichier de code correspondant est `cli/public/public_show.py`.

## 1. À quoi sert cette commande ?

`make:public-show` génère une fiche publique détaillée pour une entité.
C'est le pendant « détail » de [`make:public-list`](public_list.md).

Ce fichier est une façade mince : il délègue à `show_main` du module `public_list`.
La logique de génération vit donc à côté de celle de la liste, pour rester cohérente.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `main(args, *, root=None)` | point d'entrée de `forge make:public-show` (délègue à `public_list.show_main`) |

## 3. Contextes d'utilisation

- **Détail public** : exposer une fiche entité accessible depuis une liste publique.

## 4. Voir aussi

- [La commande make:public-list](public_list.md) : liste paginée et logique partagée.
- [La commande make:public-page](public_page.md) : page statique de base.
