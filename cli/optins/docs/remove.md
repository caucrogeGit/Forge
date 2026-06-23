# La commande opt-in:remove dans Forge

Ce document décrit la commande `forge opt-in:remove <name>`.

Le fichier de code correspondant est `cli/optins/remove.py`.

## 1. À quoi sert cette commande ?

`opt-in:remove` est le miroir d'`opt-in:install` sur l'axe **présence** (ADR-016).
Elle **affiche** la commande de désinstallation du package, sans rien exécuter.

Pour débrancher un opt-in du projet sans désinstaller le package, voir [`opt-in:disable`](disable.md).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `main(args=None)` | point d'entrée de la commande `forge opt-in:remove` |

## 3. Contextes d'utilisation

- **Nettoyage** : connaître la commande exacte pour retirer le package d'un opt-in.
- **Distinction présence / activation** : désinstaller diffère de débrancher.

## 4. Voir aussi

- [La commande opt-in:install](install.md) : miroir, installation.
- [La commande opt-in:disable](disable.md) : débranchement local sans désinstallation.
