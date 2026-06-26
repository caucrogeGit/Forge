# Les commandes module:* dans Forge

Ce document décrit la famille de commandes `forge module:*` (gestion des modules Forge locaux).

Le fichier de code correspondant est `cli/deploy/modules.py`.

## 1. À quoi servent ces commandes ?

Ces commandes gèrent le cycle de vie des modules Forge installés dans un projet.
Un module regroupe des fichiers et des routes décrits par un manifeste.

Le dossier de modules par défaut est `modules/` ; l'option `--path` permet d'en viser un autre.
La logique métier est portée par le cœur (`core.modules`) : ce fichier n'est que la couche CLI.

## 2. L'API

| Commande | Fonction | Rôle |
|---|---|---|
| `module:list` | `cmd_module_list(args)` | liste les modules disponibles |
| `module:install` | `cmd_module_install(args)` | installe un module (enregistre son manifeste) |
| `module:files` | `cmd_module_files(args)` | copie les fichiers d'un module |
| `module:routes` | `cmd_module_routes(args)` | génère les routes d'un module |
| `module:remove` | `cmd_module_remove(args)` | retire un module installé |
| | `main(args)` | point d'entrée dispatchant les sous-commandes `module:*` |

Chaque sous-commande gère son propre `--help`.

## 3. Contextes d'utilisation

- **Découverte** : `module:list` recense les modules présents dans `modules/`.
- **Branchement** : `module:install` puis `module:files` et `module:routes` intègrent un module au projet.
- **Retrait** : `module:remove` désinstalle proprement un module.

## 4. Voir aussi

- Le déploiement (`deploy:init` / `deploy:check`) est désormais fourni par l'opt-in `forge-mvc-deploy` (ADR-053).
