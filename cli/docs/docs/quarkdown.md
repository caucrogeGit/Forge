# La commande docs:pdf dans Forge

Ce document décrit la commande `forge docs:pdf`.

Le fichier de code correspondant est `cli/docs/quarkdown.py`.

## 1. À quoi sert cette commande ?

`forge docs:pdf` génère un PDF de la documentation à partir d'une source Quarkdown.
La source est `docs/quarkdown/forge-documentation.qd` ; la cible est `build/docs/forge-documentation.pdf`.

Quarkdown est une dépendance externe **optionnelle**.
Le module ne l'importe jamais : il appelle le binaire via `subprocess` s'il est présent sur le `PATH`.
Si le binaire est absent, la commande affiche un message d'installation et s'arrête proprement.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `build_pdf()` | génère le PDF si Quarkdown est disponible, sinon explique comment l'installer |

## 3. Contextes d'utilisation

- **Livrable** : produire une version PDF imprimable de la documentation.
- **Poste sans Quarkdown** : la commande reste tolérante et guide vers l'installation.

## 4. Voir aussi

- Le site documentaire complet est construit par `mkdocs build`.
