# Les commandes upload:init et media:init dans Forge

Ce document décrit les commandes `forge upload:init` et `forge media:init`.

Le fichier de code correspondant est `cli/assets/uploads.py`.

## 1. À quoi servent ces commandes ?

Elles préparent l'arborescence de stockage des fichiers téléversés.
La racine est `storage/uploads/`, avec les catégories `images`, `documents` et `tmp`.
Les variantes d'image (`images/thumbnail`, `images/medium`) sont également créées.

La création des dossiers est déléguée à l'opt-in `forge-mvc-files` (`ensure_upload_dirs`, ADR-019).
Un fichier `.gitkeep` est posé dans chaque dossier pour le versionner vide.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `init_upload_storage(root=UPLOAD_ROOT)` | crée l'arborescence d'upload et les `.gitkeep` |
| `init_media_storage(root=UPLOAD_ROOT)` | variante orientée médias |
| `main(args)` | point d'entrée dispatchant `upload:init` / `media:init` |

## 3. Contextes d'utilisation

- **Préparation** : initialiser le stockage avant le premier téléversement.
- **Idempotence** : relancer la commande ne détruit aucun fichier existant.

## 4. Voir aussi

- [La commande js:init](front.md) : bibliothèques front.
