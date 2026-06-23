# La commande doctor dans Forge

Ce document décrit la commande `forge doctor`.

Le fichier de code correspondant est `cli/project/doctor.py`.

## 1. À quoi sert cette commande ?

`forge doctor` réalise un diagnostic large et tolérant du projet, en lecture seule.
Elle vérifie l'environnement Python, la configuration, la structure MVC, les entités, le TLS de développement, la présence de Node, et d'autres points.

Elle est volontairement tolérante : elle informe et oriente, sans bloquer.
Pour un contrôle strict orienté CI, voir [`project:check`](project_check.md).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `CheckResult` | résultat unitaire d'un contrôle (statut, libellé, détail) |
| `load_project_config(root)` | charge la configuration du projet |
| `check_python()`, `check_env(root)`, `check_mvc_structure(root)`, `check_model_entities(root)`, `check_ssl(root, config)`, `check_node()` | contrôles unitaires de diagnostic |

## 3. Contextes d'utilisation

- **Premier réflexe** : diagnostiquer un projet qui ne démarre pas.
- **Tour d'horizon** : vérifier l'environnement avant de travailler.

## 4. Voir aussi

- [La commande project:check](project_check.md) : contrôle strict CI-ready.
- [La commande project:audit](project_audit.md) : rapport d'audit détaillé.
