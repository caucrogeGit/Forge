# La commande make:crud dans Forge

Ce document décrit la commande `forge make:crud`.

Le fichier de code correspondant est `cli/entities/make_crud.py`.

## 1. À quoi sert cette commande ?

`make:crud` génère un CRUD complet à partir d'une entité JSON : contrôleur, modèle, formulaire, vues (liste, fiche, formulaires) et mise en page.
Elle produit du SQL visible et du code lisible, sans magie cachée (principes 3 et 5).

Toutes les écritures suivent le mode write-if-new : un fichier existant n'est jamais écrasé (principe 9).
Le mode dry-run permet de prévisualiser les fichiers qui seraient créés.

La logique de construction est déléguée aux *builders* du sous-paquet `cli/entities/crud/`.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `make_crud(...)` | génère l'ensemble des fichiers CRUD d'une entité |
| `cmd_make_crud_main(args)` | point d'entrée de la commande `forge make:crud` |
| `MakeCrudResult` | résultat de génération (fichiers créés, préservés) |

## 3. Contextes d'utilisation

- **Mise en place rapide** : obtenir un CRUD fonctionnel pour une entité.
- **Prévisualisation** : voir les fichiers prévus avant écriture (dry-run).

## 4. Voir aussi

- [La commande make:entity](make_entity.md) : création de l'entité source.
- [La commande make:relation](make_relation.md) : déclaration de relations.
