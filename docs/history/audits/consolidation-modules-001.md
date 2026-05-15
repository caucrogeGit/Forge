# Audit CONSOLIDATION-MODULES-001 — Cycle complet des modules Forge

**Date :** 2026-05-09
**Périmètre :** système de modules `core/modules/` + `forge_cli/modules.py`
**Ticket :** CONSOLIDATION-MODULES-001

---

## Objectif

Vérifier que le système de modules Forge est installable, lisible, sûr, non destructif et correctement borné dans ses limites avant publication de Forge 2.0.

Ce ticket n'ajoute aucune fonctionnalité module nouvelle.

---

## Synthèse

| Zone module | État | Commentaire |
|---|---|---|
| `module:list` | OK | Découverte locale, dossier absent toléré |
| `module:install` | OK | Déclaratif, double installation refusée |
| `module:files` | OK | Copie contrôlée, conflit bloque tout |
| `module:routes` | OK | Injection explicite, doublon refusé |
| Structure module | OK | Contrat JSON validé, champs obligatoires clairs |
| Runtime `modules/` | OK | Dossier optionnel, non chargé dynamiquement |
| Sécurité fichiers | OK | Symlinks, `..`, `file://`, chemin absolu tous refusés |
| Non-écrasement | OK | Atomique : un seul conflit bloque toute l'installation |
| Gestion module absent | OK | `SystemExit(1)` + message explicite |
| Gestion module invalide | OK | Signalé dans liste `invalid`, `SystemExit(1)` à l'install |
| Documentation publique | partiel | `docs/reference.md` couvre les commandes, `docs/modules.md` absent |
| Limites assumées | OK | Identifiées et explicitement hors périmètre |

---

## Méthode d'audit

- Lecture complète de `core/modules/` (6 fichiers, ~901 lignes)
- Lecture complète de `forge_cli/modules.py` (214 lignes)
- Revue des 7 fichiers de tests existants (`test_module_*.py`, ~1900 lignes)
- Exécution des tests existants (tous verts)
- Ajout de tests ciblés dans `tests/test_consolidation_modules_001.py`
- Vérification sécurité (grep `symlink`, `file://`, `..`, `copytree`, `exec`, `eval`)
- Vérification documentation (`docs/reference.md`, `docs/modules.md`)

---

## Fichiers audités

| Fichier | Lignes | Responsabilité |
|---|---|---|
| `core/modules/manifest.py` | 169 | Validation contrat module |
| `core/modules/discovery.py` | 43 | Scan dossier local |
| `core/modules/registry.py` | 157 | Registre JSON `forge_modules.json` |
| `core/modules/files.py` | 225 | Copie contrôlée + sécurité |
| `core/modules/routes.py` | 233 | Injection routes dans `module_routes.py` |
| `core/modules/__init__.py` | 74 | API publique centralisée |
| `forge_cli/modules.py` | 214 | Interface CLI (4 commandes) |
| **Total** | **1115** | |

---

## Commandes auditées

| Commande | Fonction CLI | Comportement |
|---|---|---|
| `forge module:list [--path]` | `cmd_module_list()` | Scanne `modules/` ou `--path`, liste valides/invalides, non-destructif |
| `forge module:install <nom> [--path] [--dry-run]` | `cmd_module_install()` | Valide le manifest, enregistre dans `forge_modules.json`, ne copie pas |
| `forge module:files <nom> [--dry-run]` | `cmd_module_files()` | Copie les fichiers déclarés dans `mvc/`, refuse si conflit |
| `forge module:routes <nom> [--dry-run]` | `cmd_module_routes()` | Injecte dans `mvc/module_routes.py`, refuse si doublon |

---

## Cycle module vérifié

Le cycle est **découpé en étapes explicites** et intentionnellement non automatique :

```
1. forge module:list          → découvrir les modules disponibles
2. forge module:install <nom> → enregistrer le module dans forge_modules.json
3. forge module:files <nom>   → copier les fichiers dans mvc/
4. forge module:routes <nom>  → injecter les routes dans mvc/module_routes.py
```

Ce découpage est une décision de conception deliberée : il rend chaque étape visible, réversible manuellement, et évite toute magie cachée.

---

## Structure standard d'un module

Un module valide Forge est un dossier contenant :

```
modules/
  agenda/
    module.json          # Obligatoire
    controllers/         # Si "controllers" dans provides
    views/               # Si "views" dans provides
    entities/            # Si "entities" dans provides
    routes.py            # Si "routes" dans provides
    docs/                # Si "docs" dans provides
```

**Champs obligatoires de `module.json` :**

| Champ | Type | Contrainte |
|---|---|---|
| `name` | string | snake_case, 2-50 chars, `[a-z][a-z0-9_-]*` |
| `label` | string | Non vide |
| `version` | string | Format `MAJOR.MINOR.PATCH` |
| `description` | string | Non vide |

**Champs optionnels :**

| Champ | Valeurs autorisées |
|---|---|
| `provides` | `["controllers", "views", "entities", "routes", "docs"]` |
| `paths` | Chemins relatifs vers chaque provide |

---

## Découverte des modules

`discover_module_manifests(root_path)` :
- Scanne les **sous-dossiers directs** seulement (pas récursif)
- Ignore les dossiers sans `module.json`
- Retourne `(valid: list[ModuleManifest], invalid: list[tuple[str, str]])`
- Si `root_path` absent : retourne `([], [])` sans erreur

Comportement correct : la liste invalide est visible sans bloquer les modules valides.

---

## Installation d'un module

`install_module_manifest()` :
- Vérifie que le module n'est **pas déjà installé** → `ModuleAlreadyInstalledError`
- Refuse les URL, les `..`, les chemins absolus hors cwd
- En `dry_run=True` : simule sans écrire `forge_modules.json`
- Enregistre dans `forge_modules.json` : `name`, `label`, `version`, `description`, `source`

---

## Fichiers installés

`install_module_files()` :
- Lit le registre pour trouver `source`
- Prépare la liste `(source, target)` de tous les fichiers à copier
- **Détecte tous les conflits avant toute copie** → atomicité garantie
- Si un seul fichier cible existe : `ModuleFileConflictError`, aucune copie
- Copie avec `shutil.copy2` uniquement
- Met à jour le registre avec `files_installed`
- Destinations : `mvc/controllers/`, `mvc/views/`, `mvc/entities/`, `docs/modules/<nom>/`

Fichiers ignorés lors de la copie : `__pycache__/`, `.git/`, `.venv/`, `.env`, `.DS_Store`, `Thumbs.db`, `*.pyc`, `*.tmp`, `*.bak`.

---

## Routes de module

`inject_module_routes()` :
- Crée `mvc/module_routes.py` s'il n'existe pas (avec entête standard)
- Injecte un bloc balisé `# forge-module-routes:<nom>:start/end`
- Refuse si le marqueur existe déjà → `ModuleRoutesAlreadyInjectedError`
- Ajoute le pont dans `mvc/routes.py` si le fichier existe

La détection de doublon est basée sur le marqueur : robuste même si le fichier est modifié manuellement autour du bloc.

---

## Runtime officiel `modules/`

Le dossier `modules/` est un **dossier de stockage local**, pas un loader dynamique.

- Jamais chargé au démarrage du serveur
- Jamais scanné par `core/` au runtime
- Les routes injectées sont des **imports Python statiques** dans `module_routes.py`
- `MODULE-ROUTES-RUNTIME-AUDIT-001` a confirmé que `modules/` est le runtime officiel

Aucune exécution dynamique (`importlib`, `exec`, `eval`) n'a été détectée dans `core/modules/`.

---

## Préservation du code utilisateur

Le mécanisme est **le refus explicite** (différent du `build_model` qui distingue fichiers régénérables/manuels).

`prepare_module_file_installation()` (lignes 168-170) :
```python
conflicts = tuple(target for _, target in planned if Path(target).exists())
if conflicts:
    raise ModuleFileConflictError(conflicts)
```

Et re-vérifié lors de la copie effective (lignes 212-213) :
```python
if target_path.exists():
    raise ModuleFileConflictError((target,))
```

**Conséquence :** l'installation de fichiers de module est une **opération à sens unique** — elle n'est pas conçue pour être ré-exécutée. Si des fichiers ont été modifiés par l'utilisateur, il doit les supprimer manuellement pour réinstaller.

Cette approche est cohérente avec CONSOLIDATION-NON-OVERWRITE-001 : aucun fichier existant n'est jamais écrasé silencieusement.

---

## Sécurité des fichiers

| Menace | Protection | Localisation |
|---|---|---|
| Symlinks | Détecté et refusé | `files.py:97-106` |
| Traversée `..` | Refus dans paths | `manifest.py:106`, `registry.py:98`, `files.py:65`, `routes.py:52` |
| Chemins absolus | Refusé dans paths | `manifest.py:108-111`, `files.py:68`, `routes.py:56` |
| URL `file://` | Regex, refusé | `manifest.py:15`, `files.py:33` (inclut `file://`) |
| URL `https://`, `ftp://` | Regex, refusé | Tous les modules |
| Écrasement fichiers | Atomique, refusé | `files.py:168-170, 212-213` |
| Code dynamique | Absent | Aucun `importlib`, `exec`, `eval` dans `core/modules/` |
| Fichiers `.env` | Ignoré | `files.py:31` |

`MODULE-FILES-SECURITY-001` avait déjà validé cette surface. L'audit CONSOLIDATION confirme que la protection est toujours en place.

---

## Limites actuelles

Les limites suivantes sont **assumées et documentées** — elles ne sont pas des défauts :

| Limite | Justification |
|---|---|
| Pas de `module:remove` | Hors périmètre Forge 2.0, suppression manuelle simple |
| Pas de `module:update` | Hors périmètre, réinstallation manuelle |
| Pas de rollback | Hors périmètre, opération à sens unique documentée |
| Pas de dépendances entre modules | Hors périmètre |
| Pas de registre distant | Hors périmètre |
| Pas de marketplace | Hors périmètre |
| Pas de signature cryptographique | Hors périmètre Forge 2.0 |
| Installation partielle possible | Si `module:files` réussit mais `module:routes` échoue, état intermédiaire |
| Pas de résolution de conflit avancée | L'utilisateur résout manuellement |

---

## Points cohérents

1. **Séparation des responsabilités** : `manifest.py`, `discovery.py`, `registry.py`, `files.py`, `routes.py` sont indépendants et testables unitairement.
2. **Cycle explicite** : 4 étapes séparées, aucune magie cachée.
3. **Sécurité en profondeur** : les validations sont répétées dans chaque module (`manifest`, `registry`, `files`, `routes`).
4. **Dry-run disponible** sur toutes les commandes qui modifient des fichiers.
5. **Atomicité** : la détection de conflits est faite avant toute copie.
6. **API publique propre** : `core/modules/__init__.py` expose exactement ce qui est nécessaire.
7. **Tests existants solides** : 7 fichiers, ~1900 lignes couvrant tous les sous-composants.

---

## Incohérences détectées

### 1. `docs/modules.md` absent — **mineure**

`CONSOLIDATION-DOC-001` l'avait déjà identifiée. La documentation des modules est dans `docs/reference.md` (section commandes + section guide d'installation), mais il n'existe pas de page dédiée `docs/modules.md` pour les développeurs de modules.

**Impact :** documentation publiable mais lacunaire pour les auteurs de modules.
**Action recommandée :** ticket `CONSOLIDATION-DOC-MODULES-001`.

### 2. État intermédiaire possible — **acceptable**

Si `module:files` réussit mais `module:routes` échoue (fichier de routes manquant, conflit de marqueur), le module est dans un état partiellement installé : fichiers copiés, routes non injectées. Le registre reflète `files_installed` mais pas les routes.

**Impact :** l'utilisateur doit relancer `module:routes` manuellement.
**Action recommandée :** documenter cette situation dans `CONSOLIDATION-DOC-MODULES-001`.

---

## Risques restants

| Risque | Niveau | Commentaire |
|---|---|---|
| État intermédiaire non documenté | Faible | Récupérable manuellement |
| `docs/modules.md` absent | Faible | Ne bloque pas Forge 2.0 |
| Aucun `module:remove` | Acceptable | Suppression manuelle simple |
| Modules tiers non vérifiés | Hors périmètre | Utilisateur responsable du contenu |

---

## Recommandations

1. **Créer `docs/modules.md`** avec : structure standard, cycle d'installation, limites — dans `CONSOLIDATION-DOC-MODULES-001`.
2. **Documenter l'état intermédiaire** dans la doc et/ou dans le message CLI de `module:routes`.
3. **Aucune modification fonctionnelle** requise avant Forge 2.0.

---

## Tickets futurs proposés

| Ticket | Sujet |
|---|---|
| `CONSOLIDATION-DOC-MODULES-001` | Créer `docs/modules.md` et documenter les limites |
| `MODULE-REMOVE-001` | Ajouter `module:remove` (post-Forge 2.0) |
| `MODULE-UPDATE-001` | Ajouter `module:update` (post-Forge 2.0) |

---

## Verdict final

**Le système de modules Forge est suffisamment fiable pour Forge 2.0.**

Le cycle `module:list` → `module:install` → `module:files` → `module:routes` est **complet, explicite, sécurisé et non destructif**. Les 4 commandes fonctionnent correctement, les refus sont explicites, les limites sont assumées.

La seule lacune notable est l'absence de `docs/modules.md`, qui n'est pas bloquante pour la publication mais devrait être adressée avant ou pendant Forge 2.0.

**Résultat :** CONSOLIDATION-MODULES-001 — **VALIDÉ**
