# La commande make:public-contact dans Forge

Ce document décrit la commande `forge make:public-contact`.

Le fichier de code correspondant est `cli/public/public_contact.py`.

## 1. À quoi sert cette commande ?

`make:public-contact` génère une page de contact publique : gabarit de vue et méthode de contrôleur.
Elle réutilise les blocs et helpers de [`make:public-page`](public_page.md) (mise en page, titre, scripts).

C'est une variante spécialisée de la page publique, dédiée au formulaire de contact.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `build_contact_template()` | produit le gabarit de la page de contact |
| `make_public_contact(*, root=None)` | génère la page de contact |
| `print_result(result)` | affiche le résultat de la génération |
| `main(args=None, *, root=None)` | point d'entrée de `forge make:public-contact` |

## 3. Contextes d'utilisation

- **Contact** : offrir une page de contact publique prête à l'emploi.
- **Cohérence** : hériter de la mise en page commune des pages publiques.

## 4. Voir aussi

- [La commande make:public-page](public_page.md) : page statique de base réutilisée.
- [La commande make:public-form](public_form.md) : formulaire public générique.
