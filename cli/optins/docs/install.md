# La commande opt-in:install dans Forge

Ce document décrit la commande `forge opt-in:install <name>`.

Le fichier de code correspondant est `cli/optins/install.py`.

## 1. À quoi sert cette commande ?

`opt-in:install` agit sur l'axe **présence** d'un opt-in (ADR-016).
Elle **affiche** la commande d'installation du package PyPI correspondant, sans rien exécuter.

Selon le contexte, elle propose `pip` (en venv) ou `pipx inject` (en installation pipx).
Le choix « afficher plutôt qu'exécuter » est délibéré : installer un package est un geste explicite de l'utilisateur.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `main(args=None)` | point d'entrée de la commande `forge opt-in:install` |

## 3. Contextes d'utilisation

- **Découverte** : connaître la commande exacte à lancer pour un opt-in.
- **Environnements mixtes** : adapter le conseil au mode venv ou pipx.

## 4. Voir aussi

- [La commande opt-in:remove](remove.md) : miroir, désinstallation.
- [La commande opt-in:enable](enable.md) : branchement local dans le projet.
