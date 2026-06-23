# La commande project:audit dans Forge

Ce document décrit la commande `forge project:audit`.

Le fichier de code correspondant est `cli/project/project_audit.py`.

## 1. À quoi sert cette commande ?

`forge project:audit` produit un rapport d'audit détaillé et **non destructif** du projet.
Elle analyse la structure, la configuration, les entités, les routes, les templates, les modules et les migrations.

Elle ne modifie rien : c'est une lecture approfondie qui restitue des observations.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `AuditResult` | observation unitaire d'audit |
| `audit_project_structure`, `audit_project_config`, `audit_project_entities`, `audit_project_routes`, `audit_project_templates`, `audit_project_modules`, `audit_project_migrations` | audits unitaires par domaine |

## 3. Contextes d'utilisation

- **État des lieux** : dresser un panorama détaillé d'un projet existant.
- **Reprise de projet** : comprendre un projet hérité avant d'y toucher.

## 4. Voir aussi

- [La commande project:check](project_check.md) : contrôle strict CI-ready.
- [La commande doctor](doctor.md) : diagnostic tolérant.
