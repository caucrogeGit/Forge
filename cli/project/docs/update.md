# La commande update dans Forge

Ce document décrit la commande `forge update`.

Le fichier de code correspondant est `cli/project/update.py`.

## 1. À quoi sert cette commande ?

`forge update` aide à mettre à jour Forge dans l'environnement Python courant (`.venv` ou pipx).
Elle vise l'utilisateur qui a créé un projet avec une ancienne version et veut passer à la dernière.

Elle détecte le mode d'installation (venv ou pipx) et adapte la commande.
Elle propose plusieurs modes, dont un mode vérification et un dry-run, avant toute mise à jour effective.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `main(args)` | point d'entrée de la commande `forge update` |

La commande gère son propre `--help` et restitue un code de retour selon le mode.

## 3. Contextes d'utilisation

- **Maintenance** : passer un projet existant à la dernière version de Forge.
- **Vérification** : savoir si une version plus récente est disponible.

## 4. Voir aussi

- [La commande doctor](doctor.md) : diagnostic après mise à jour.
