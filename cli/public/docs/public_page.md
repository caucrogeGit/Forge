# La commande make:public-page dans Forge

Ce document décrit la commande `forge make:public-page`.

Le fichier de code correspondant est `cli/public/public_page.py`.

## 1. À quoi sert cette commande ?

`make:public-page` génère une page statique publique : un gabarit de vue et la méthode de contrôleur associée.
C'est la brique de base des pages publiques : les autres commandes `make:public-*` réutilisent ses gabarits et ses helpers.

Forge n'écrase jamais un fichier utilisateur : la génération ajoute proprement une méthode au contrôleur sans détruire l'existant (principe 9).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `build_public_page_spec(name)` | construit la spécification d'une page à partir d'un nom |
| `build_public_template(spec)` | produit le gabarit de vue |
| `build_controller(spec)` / `build_controller_method(spec)` | produit le contrôleur ou la méthode |
| `PublicPageSpec` / `MakePublicPageResult` | structures de spécification et de résultat |
| `main(args, *, root=None)` | point d'entrée de la commande `forge make:public-page` |

## 3. Contextes d'utilisation

- **Page institutionnelle** : créer une page publique simple (mentions, à propos…).
- **Socle commun** : fournir les gabarits réutilisés par les autres pages publiques.

## 4. Voir aussi

- [La commande make:public-list](public_list.md) : liste publique paginée.
- [La commande make:public-contact](public_contact.md) : page de contact.
