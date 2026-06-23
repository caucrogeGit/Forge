# L'aide générale du CLI dans Forge

Ce document décrit le texte d'aide global affiché par `forge help` et `forge --help`.

Le fichier de code correspondant est `cli/_support/help.py`.

## 1. À quoi sert ce module ?

Ce module porte le **sommaire** de toutes les commandes Forge.
Il regroupe les commandes par thème (Projet, Entités, Base de données, Sécurité, opt-ins…).
C'est la vue d'ensemble qu'un utilisateur voit en premier.

Il ne documente pas chaque commande en détail : c'est le rôle de l'aide par commande.
Voir [L'aide par commande](help_dispatch.md) pour le détail d'une commande précise.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `build_help(version)` | construit le texte d'aide complet en y injectant le numéro de version |

Le texte est porté par un gabarit interne (`_HELP_TEMPLATE`).
La version est passée par l'appelant : ce module ne lit pas lui-même `pyproject.toml`.

## 3. Contextes d'utilisation

- **`forge help`** : affichage du sommaire complet.
- **`forge --help` / `forge -h`** sans commande : même sommaire.
- **Découverte** : un nouvel utilisateur parcourt les groupes pour repérer la commande utile.

## 4. Voir aussi

- [L'aide par commande](help_dispatch.md) : aide détaillée d'une commande donnée.
- [Le formatage de sortie CLI](output.md) : tags de statut.
