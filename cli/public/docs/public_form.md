# La commande make:public-form dans Forge

Ce document décrit la commande `forge make:public-form`.

Le fichier de code correspondant est `cli/public/public_form.py`.

## 1. À quoi sert cette commande ?

`make:public-form` génère un formulaire public d'enregistrement à partir d'une entité.
Elle déduit les champs de saisie et leur type d'`input` depuis la définition JSON validée de l'entité.

Les champs sensibles sont exclus du formulaire public.
La méthode de contrôleur générée gère l'insertion en base via du SQL visible (principe 5).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `public_form_fields(definition)` | champs de saisie publics d'une entité |
| `build_public_form_spec(definition)` | construit la spécification du formulaire |
| `build_public_form_new_method(spec)` | produit la méthode de contrôleur de soumission |
| `PublicFormSpec` / `MakePublicFormResult` | structures de spécification et de résultat |
| `main(args, *, root=None)` | point d'entrée de `forge make:public-form` |

## 3. Contextes d'utilisation

- **Saisie publique** : recueillir des données depuis un visiteur (inscription, dépôt).
- **Sécurité** : ne jamais exposer les champs sensibles dans le formulaire.

## 4. Voir aussi

- [La commande make:public-contact](public_contact.md) : formulaire de contact spécialisé.
- [La commande make:public-list](public_list.md) : liste publique.
