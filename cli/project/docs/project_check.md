# La commande project:check dans Forge

Ce document décrit la commande `forge project:check`.

Le fichier de code correspondant est `cli/project/project_check.py`.

## 1. À quoi sert cette commande ?

`forge project:check` effectue un contrôle **strict** des conventions d'un projet Forge.
Elle est pensée pour la CI : un manquement se traduit par un échec.

Elle couvre la structure, la configuration, les entités, les routes, les templates, les modules et les migrations.
Contrairement à [`doctor`](doctor.md) qui est tolérant, `project:check` est exigeant.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `run_project_check(root, version)` | exécute tous les contrôles et retourne la liste des résultats |
| `check_project_structure`, `check_project_config`, `check_project_entities`, `check_project_routes`, `check_project_templates`, `check_project_modules`, `check_project_migrations` | contrôles stricts unitaires |

Les résultats réutilisent le type `CheckResult` de la commande `doctor`.

## 3. Contextes d'utilisation

- **CI** : valider qu'un projet respecte les conventions avant fusion.
- **Revue** : vérifier strictement la conformité d'un projet.

## 4. Voir aussi

- [La commande doctor](doctor.md) : diagnostic tolérant.
- [La commande project:audit](project_audit.md) : rapport détaillé.
