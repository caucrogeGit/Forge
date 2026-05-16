# Modules Forge

Un module Forge est un dossier lisible contenant au minimum un fichier
`module.json`. Il décrit ce qu'il fournit et Forge installe ce contenu
par étapes explicites et contrôlées.

### Modules — Principe général

Un module Forge doit rester lisible, copiable, auditable et modifiable.

Règles fondamentales :

- un module est un dossier, pas une boîte noire ;
- le manifeste central est `module.json` ;
- aucun code de module n'est exécuté pendant son installation ;
- l'installation est déclarative : elle enregistre, puis copie, puis génère ;
- le développeur garde la maîtrise des fichiers copiés et du branchement des routes ;
- aucun écrasement silencieux n'est autorisé ;
- aucune marketplace ni téléchargement distant n'existe.

### Modules — Structure d'un module

Structure minimale :

```text
agenda/
  module.json
```

Structure complète possible :

```text
agenda/
  module.json
  README.md
  entities/
  controllers/
  views/
  docs/
  routes.py
```

Règles :

- `module.json` est obligatoire ;
- les autres dossiers et fichiers sont optionnels ;
- seuls les éléments déclarés dans `provides` sont pris en compte par Forge ;
- les chemins réels vers ces éléments sont définis dans `paths`.

### Modules — Format `module.json`

Exemple complet :

```json
{
  "name": "agenda",
  "label": "Agenda",
  "version": "0.1.0",
  "description": "Module générique d'agenda.",
  "provides": [
    "entities",
    "controllers",
    "views",
    "routes",
    "docs"
  ],
  "paths": {
    "entities": "entities",
    "controllers": "controllers",
    "views": "views",
    "routes": "routes.py",
    "docs": "docs"
  }
}
```

### Modules — Champs obligatoires

| Champ | Rôle |
|---|---|
| `name` | nom technique du module |
| `label` | libellé humain |
| `version` | version du module |
| `description` | description courte |

Règles de validation :

- `name` : snake_case minuscule, ne commence pas par un chiffre, sans chemin ni URL ni HTML ;
- `version` : format `MAJOR.MINOR.PATCH` (ex. `0.1.0`) ;
- `label` et `description` : sans HTML.

### Modules — Champs optionnels

| Champ | Type | Valeur par défaut |
|---|---|---|
| `provides` | liste | `[]` |
| `paths` | dictionnaire | `{}` |

### Modules — `provides`

`provides` liste les types de contenu fournis par le module.

| Valeur | Rôle |
|---|---|
| `entities` | définitions d'entités |
| `controllers` | contrôleurs |
| `views` | templates Jinja |
| `routes` | fichier de routes |
| `docs` | documentation |
| `static` | fichiers statiques (réservé) |
| `migrations` | migrations SQL (réservé) |

`forge module:files` traite `entities`, `controllers`, `views` et `docs`.
`routes` est traité séparément par `forge module:routes`.
`static` et `migrations` sont réservés pour de futurs tickets.

### Modules — `paths`

`paths` associe chaque type déclaré dans `provides` à un chemin relatif à l'intérieur du dossier du module.

```json
"paths": {
  "entities": "entities",
  "controllers": "controllers",
  "views": "views",
  "routes": "routes.py",
  "docs": "docs"
}
```

Règles de validation :

- chemins relatifs uniquement ;
- pas de `..` ;
- pas de chemin absolu (Unix ou Windows) ;
- pas d'URL.

### Modules — Registre `forge_modules.json`

`forge_modules.json` est le registre des modules installés.
Il est créé ou mis à jour par `forge module:install`.

Exemple après installation et copie des fichiers :

```json
{
  "installed": {
    "agenda": {
      "name": "agenda",
      "label": "Agenda",
      "version": "0.1.0",
      "description": "Module générique d'agenda.",
      "source": "modules/agenda",
      "provides": ["entities", "controllers", "views", "routes", "docs"],
      "files_installed": [
        "mvc/entities/event/event.json",
        "mvc/controllers/agenda_controller.py",
        "mvc/views/agenda/index.html",
        "docs/modules/agenda/agenda.md"
      ]
    }
  }
}
```

Règles du registre :

- la source est stockée comme chemin relatif au projet ;
- `files_installed` est ajouté après `forge module:files` ;
- ne contient pas le contenu des fichiers ;
- ne doit pas contenir de chemin absolu ;
- ne doit pas devenir une base de données.

### Modules — Lister les modules

```bash
forge module:list
forge module:list --path modules
```

`forge module:list` scanne un dossier et liste les modules détectés par la
présence d'un fichier `module.json` valide dans chaque sous-dossier direct.
Le dossier par défaut est `modules/`.

Exemple de sortie :

```
Modules Forge disponibles :

  - agenda 0.1.0 — Agenda
  - patrimoine 0.1.0 — Patrimoine

Modules invalides :

  - broken — label: champ obligatoire manquant
```

Si le dossier n'existe pas :

```
Aucun dossier de modules trouvé : modules
```

Règles :

- lit uniquement les fichiers `module.json` ;
- n'installe rien, ne copie aucun fichier, n'injecte aucune route ;
- signale les modules invalides sans bloquer l'affichage des valides ;
- ne crée pas le dossier `modules/` s'il est absent.

### Modules — Installer déclarativement un module

```bash
forge module:install agenda
forge module:install agenda --path modules
forge module:install agenda --dry-run
```

`forge module:install` valide le module et l'inscrit dans `forge_modules.json`.

```text
module:install = validation + registre
```

Règles :

- valide le `module.json` avant toute écriture ;
- refuse l'installation d'un module déjà présent dans le registre ;
- écrit uniquement dans `forge_modules.json` ;
- ne copie aucun fichier dans `mvc/` ;
- n'injecte aucune route ;
- n'exécute aucun code du module ;
- `--dry-run` simule sans écrire.

### Modules — Installer les fichiers d'un module

```bash
forge module:files agenda --dry-run
forge module:files agenda
```

`forge module:files` copie les fichiers déclarés d'un module déjà enregistré
avec `forge module:install`.

```text
module:files = copie contrôlée, sans écrasement
```

Mappage des dossiers :

| Module | Projet cible |
|---|---|
| `entities/` | `mvc/entities/` |
| `controllers/` | `mvc/controllers/` |
| `views/` | `mvc/views/` |
| `docs/` | `docs/modules/<nom_module>/` |

Règles :

- copie uniquement les fichiers déclarés dans `provides` et `paths` ;
- crée les dossiers cibles si nécessaire ;
- refuse d'écraser un fichier existant ;
- `--dry-run` affiche les copies prévues sans écrire ;
- ignore les caches, fichiers temporaires et dossiers cachés ;
- ne modifie pas `mvc/routes.py` ;
- ne lance aucun SQL ;
- n'exécute aucun code du module.

Après une installation réelle, Forge trace les fichiers copiés dans
`forge_modules.json` avec la clé `files_installed`.

### Modules — Activer les routes d'un module

```bash
forge module:routes agenda --dry-run
forge module:routes agenda
```

`forge module:routes` génère un fichier de routes dédié pour un module déjà
enregistré dans `forge_modules.json`.

```text
module:routes = génération d'un fichier dédié + affichage des lignes à copier
```

Prérequis : le module doit déclarer `"routes"` dans `provides` et un chemin
valide dans `paths.routes`.

**Forge ne modifie jamais `mvc/routes.py`** (principe 9 de la charte v2 : pas
d'écriture invisible dans le code utilisateur).

La commande :

1. Crée `mvc/routes_<nom>.py` (fichier dédié par module, write-if-new) ;
2. Affiche sur stdout les lignes à ajouter dans `mvc/routes.py`.

```python
# Contenu généré dans mvc/routes_agenda.py :
from modules.agenda.routes import register_routes as register_agenda_routes

__all__ = ["register_agenda_routes"]
```

Pour activer les routes, ajoutez dans `mvc/routes.py` :

```python
from mvc.routes_agenda import register_agenda_routes
register_agenda_routes(router)
```

Règles :

- le module doit être installé avant génération ;
- `--dry-run` affiche ce qui serait créé sans modifier de fichier ;
- si `mvc/routes_<nom>.py` existe déjà, la commande refuse et affiche un message ;
  supprimez le fichier manuellement pour le régénérer ;
- aucun chemin absolu, `..` ou URL n'est accepté pour `paths.routes` ;
- Forge n'importe pas dynamiquement `routes.py` du module pendant la génération ;
- ne copie aucun fichier d'entité, vue, contrôleur ou doc.

### Modules — Dépendance runtime des routes

Les routes de modules référencent le dossier source du module (`modules/<nom>/`).

```python
# Dans mvc/routes_agenda.py, après génération :
from modules.agenda.routes import register_routes as register_agenda_routes
```

Conséquences pratiques :

- un module qui expose des routes doit rester présent dans `modules/<nom>/` tant que ses routes sont utilisées par l'application ;
- supprimer `modules/<nom>/` après `forge module:routes` provoque une erreur d'import au démarrage de l'application ;
- `forge module:files` copie les entités, contrôleurs et vues dans `mvc/`, mais pas les routes — c'est délibéré.

Raisons de ce choix :

- les fichiers de routes sont du code Python importé, pas des ressources statiques copiables sans précaution ;
- le dossier `modules/` est déjà une source contrôlée du projet — ce n'est pas un dépôt externe ;
- évite de dupliquer du code Python entre `modules/` et `mvc/`, ce qui rendrait les mises à jour de module risquées.

### Modules — Cycle recommandé

```bash
forge module:list
forge module:install agenda --dry-run
forge module:install agenda
forge module:files agenda --dry-run
forge module:files agenda
forge module:routes agenda --dry-run
forge module:routes agenda
```

Schéma du cycle :

```text
module.json
→ forge module:list
→ forge module:install
→ forge_modules.json
→ forge module:files
→ fichiers copiés dans mvc/ et docs/modules/
→ forge module:routes
→ mvc/routes_<nom>.py généré (fichier dédié par module)
→ lignes à copier dans mvc/routes.py affichées
```

Chaque étape est indépendante et explicite. Aucune étape n'en déclenche
automatiquement une autre.

### Modules — Désinstaller un module

```bash
forge module:remove agenda --dry-run
forge module:remove agenda
```

`forge module:remove` désinstalle un module installé par Forge lorsque les fichiers
et routes sont encore traçables.

```text
module:remove = retrait des fichiers inchangés + retrait des routes marquées + mise à jour du registre
```

**Règle centrale** : Forge ne supprime que ce qu'il peut prouver avoir installé sans modification.

Comportement par fichier tracé dans `forge_modules.json` :

| Situation | Action |
|---|---|
| Fichier identique à la source | Supprimé |
| Fichier modifié manuellement | Conservé — signalé |
| Source introuvable | Conservé — signalé |
| Fichier absent (déjà supprimé) | Ignoré |

Comportement sur les routes :

| Situation | Action |
|---|---|
| `mvc/routes_<nom>.py` existe | **Conservé** — à retirer manuellement |
| Marqueurs `forge-module-routes:<nom>:start/end` présents (anciens projets) | Bloc retiré de `mvc/module_routes.py` (compat arrière) |
| Marqueurs absents | Nettoyage manuel requis — signalé |
| Fichier `mvc/module_routes.py` absent | Ignoré |

> **Contrat explicite :** `forge module:remove` ne supprime pas `mvc/routes_<nom>.py`
> ni les lignes que vous avez ajoutées dans `mvc/routes.py`.
> Ces éléments restent sur le disque — à retirer manuellement si souhaité.

Règles :

- `--dry-run` affiche les suppressions prévues sans rien écrire ;
- les dossiers parents ne sont jamais supprimés ;
- les fichiers non tracés dans `forge_modules.json` ne sont jamais touchés ;
- le module est retiré du registre même si des fichiers ont été conservés ;
- pas de suppression forcée ;
- pas de fusion intelligente avec fichiers modifiés.

Limites :

- pas de rollback complet ;
- pas de suppression des fichiers modifiés ;
- pas de suppression des fichiers dont la source est absente.

### Modules — API Python (`core.modules`)

```python
from core.modules import (
    # Manifeste
    ModuleManifest,
    ModuleManifestError,
    ALLOWED_PROVIDES,
    validate_module_name,
    validate_module_version,
    validate_module_manifest,
    load_module_manifest,
    # Découverte
    discover_module_manifests,
    list_module_manifests,
    # Registre
    MODULE_REGISTRY_FILE,
    ModuleRegistryError,
    ModuleAlreadyInstalledError,
    ModuleInstallResult,
    load_installed_modules_registry,
    save_installed_modules_registry,
    is_module_installed,
    prepare_module_installation,
    install_module_manifest,
    # Routes
    ModuleRouteInjectionError,
    ModuleRoutesAlreadyGeneratedError,
    ModuleRouteGenerationResult,
    generate_module_routes,
    # Fichiers
    INSTALLABLE_PROVIDES,
    ModuleFileInstallError,
    ModuleFileConflictError,
    ModuleFileInstallResult,
    prepare_module_file_installation,
    install_module_files,
)
```

### Modules — Sécurité de copie des fichiers

`forge module:files` copie uniquement les fichiers déclarés dans les répertoires autorisés. Les garanties suivantes s'appliquent :

- seuls les types `entities`, `controllers`, `views` et `docs` sont copiables par `module:files` — `routes`, `static`, `migrations` sont exclus ;
- les chemins absolus sont refusés (`/etc/...`, `C:\...`) ;
- les chemins contenant `..` sont refusés ;
- les URL sont refusées (`https://`, `ftp://`, `file://`) ;
- les **liens symboliques sont refusés** — un symlink dans un module entraîne un arrêt immédiat de l'installation, même s'il pointe vers un fichier interne au module ;
- les fichiers cachés sensibles sont ignorés : `.env`, `.DS_Store`, `Thumbs.db` ;
- les caches et fichiers de build sont ignorés : `__pycache__/`, `*.pyc`, `.git/`, `.venv/` ;
- les fichiers temporaires sont ignorés : `*.tmp`, `*.bak` ;
- aucun fichier existant n'est écrasé ;
- aucun code module n'est exécuté pendant la copie ;
- `--dry-run` permet de contrôler les copies prévues sans écriture.

Les routes restent traitées exclusivement par `forge module:routes`.

Cibles autorisées :

| Provide | Cible |
|---|---|
| `entities` | `mvc/entities/` |
| `controllers` | `mvc/controllers/` |
| `views` | `mvc/views/` |
| `docs` | `docs/modules/<nom_module>/` |

Si un symlink est détecté, l'installation est refusée entièrement — aucun fichier n'est copié et un message d'erreur explicite est affiché.

### Modules — Sécurité et limites actuelles

Limites fonctionnelles :

- pas de `forge module:update` ;
- pas de fusion automatique de fichiers ;
- pas d'option `--force` pour écraser des fichiers existants ;
- `forge module:files` ne gère pas encore `static` et `migrations` ;
- pas de gestion de dépendances entre modules ;
- pas de marketplace ni de téléchargement de modules ;
- pas de module officiel livré par Forge.

Sécurité :

- aucun code de module n'est exécuté pendant l'installation ;
- les chemins absolus, `..` et URL sont refusés à chaque étape ;
- les fichiers caches et temporaires sont ignorés lors de la copie ;
- les routes de modules restent à clarifier côté dépendance runtime dans `MODULE-ROUTES-RUNTIME-AUDIT-001` ;
- la sécurité de la copie des fichiers de modules sera auditée dans `MODULE-FILES-SECURITY-001`.

### Modules — Cycle de vie

#### Ce qui est supporté

| Étape | Commande | Ce que Forge fait |
|---|---|---|
| Découverte | `forge module:list` | Scanne un dossier, liste les modules valides et invalides |
| Enregistrement | `forge module:install` | Valide le manifeste, inscrit le module dans `forge_modules.json` |
| Copie des fichiers | `forge module:files` | Copie les fichiers déclarés dans `mvc/` et `docs/modules/` |
| Génération des routes | `forge module:routes` | Génère `mvc/routes_<nom>.py` et affiche les lignes à ajouter dans `mvc/routes.py` |
| Désinstallation contrôlée | `forge module:remove` | Supprime les fichiers inchangés, retire les routes marquées, met à jour le registre |

Chaque étape est indépendante, explicite, et dotée d'un mode `--dry-run`. Aucune étape n'en déclenche automatiquement une autre.

Garanties lors de l'installation :

- aucun fichier existant n'est écrasé — les conflits sont signalés et stoppent l'opération ;
- aucun code du module n'est exécuté pendant l'installation ;
- les chemins absolus, `..` et URL sont refusés à toutes les étapes ;
- les fichiers copiés sont tracés dans `forge_modules.json` avec la clé `files_installed` ;
- `forge module:routes` génère `mvc/routes_<nom>.py` et affiche les lignes à ajouter dans `mvc/routes.py` — il ne modifie jamais `mvc/routes.py`.

#### Ce qui n'est pas encore supporté

Forge ne fournit pas encore les opérations suivantes :

| Opération | Statut | Ticket prévu |
|---|---|---|
| `forge module:remove` — désinstallation contrôlée | **Disponible** (voir section dédiée) | `MODULE-REMOVE-001` ✅ |
| `forge module:update` — mise à jour contrôlée | Non disponible | `MODULE-UPDATE-001` |
| Rollback automatique complet | Non disponible | — |
| Fusion intelligente avec fichiers modifiés | Non disponible | — |
| Registre distant de modules | Non disponible | — |
| Gestion de dépendances entre modules | Non disponible | — |
| Marketplace de modules | Non disponible | — |
| Copie de `static` et `migrations` par `module:files` | Non disponible | — |

#### Risques connus

**La suppression contrôlée ne couvre que les fichiers traçables.**
`forge module:remove` supprime uniquement les fichiers dont le contenu est identique à la source. Les fichiers modifiés sont conservés et signalés. Si la source est absente, les fichiers sont conservés. Après `forge module:routes`, retirer le dossier source `modules/<nom>/` sans supprimer `mvc/routes_<nom>.py` et les lignes correspondantes dans `mvc/routes.py` provoque une erreur d'import au démarrage.

**Pas de rollback sur fichiers partiellement copiés.**
Si une copie de fichiers échoue en cours d'opération, les fichiers déjà copiés ne sont pas annulés. Le registre `forge_modules.json` peut indiquer une installation partielle.

**Modifications manuelles empêchent la suppression automatique future.**
Si les fichiers copiés par `forge module:files` sont modifiés après l'installation, une éventuelle commande `forge module:remove` ne pourra pas les supprimer en toute sécurité sans risquer de perdre du code utilisateur.

**Régénération refusée — suppression manuelle requise.**
`forge module:routes` refuse de régénérer `mvc/routes_<nom>.py` si le fichier existe déjà. Supprimez-le manuellement pour le régénérer.

#### Bonnes pratiques

- Toujours tester avec `--dry-run` avant une installation réelle.
- Versionner `forge_modules.json` pour garder la traçabilité des modules installés.
- Ne pas modifier les fichiers copiés par `forge module:files` si vous souhaitez garder la possibilité de supprimer ou mettre à jour le module proprement.
- Conserver le dossier `modules/<nom>/` tant que ses routes sont actives dans l'application.
- Ajouter manuellement les lignes affichées par `forge module:routes` dans `mvc/routes.py` après génération.

#### Tickets futurs

- **`MODULE-UPDATE-001`** — ajouter une mise à jour contrôlée : comparaison des fichiers, signalement des conflits, mise à jour sélective.

---

## Référence croisée — Modules Forge

### Principe général

La Phase 7 regroupe trois briques orthogonales livrées après Forge 1.5.0 :

- **Workflow** — modélisation déclarative des statuts et transitions métier d'une entité ;
- **Statistiques** — collecte légère d'événements et calcul d'indicateurs agrégés ;
- **Modules** — système d'empaquetage et d'installation de briques Forge réutilisables.

Ces trois briques partagent les mêmes principes : pas d'ORM, pas de runtime caché, déclaration explicite, zéro dépendance nouvelle.

### Workflow — Socle livré

Le workflow Forge permet de gérer les transitions d'état d'une entité sans imposer de machine à états globale.

Briques livrées :

- déclaration des statuts et transitions dans `workflow.json` (par entité) ;
- validation des transitions autorisées ;
- helpers Jinja `workflow_status_label()`, `workflow_allowed_transitions()` ;
- intégration CRUD : boutons de transition dans les vues `show` et `list` ;
- pas de callbacks automatiques — les hooks sont à écrire dans le contrôleur.

La documentation complète est dans la section [Workflow](workflow.md) de cette référence.

### Statistiques — Socle livré

Le module statistiques fournit une collecte d'événements bruts et des agrégats calculés à la demande, sans base de données dédiée ni service externe.

Briques livrées :

- `StatsEvent` — enregistrement d'un événement horodaté dans `stats_events` ;
- `stats_count()`, `stats_sum()`, `stats_average()` — agrégats sur la table des événements ;
- `stats_by_day()`, `stats_by_month()` — agrégats temporels ;
- helpers Jinja pour afficher les indicateurs dans les templates ;
- pas de dashboard généré automatiquement — les vues sont à créer dans le contrôleur.

La documentation complète est dans la section [Statistiques](stats.md) de cette référence.

### Modules — Socle livré

Le système de modules permet d'empaqueter des entités, contrôleurs, vues et docs sous forme de dossier autonome et de les installer dans un projet Forge.

Briques livrées :

| Ticket | Commande / brique |
|---|---|
| `MODULE-SYSTEM-001` | Format `module.json`, structure standard d'un module |
| `MODULE-SYSTEM-002` | `forge module:list` — découverte locale |
| `MODULE-SYSTEM-003` | `forge module:install` — installation déclarative dans `forge_modules.json` |
| `MODULE-SYSTEM-004` | `forge module:routes` — génération de `mvc/routes_<nom>.py` et affichage des lignes à ajouter |
| `MODULE-SYSTEM-005` | `forge module:files` — copie des fichiers dans `mvc/entities`, `mvc/controllers`, `mvc/views`, `docs/modules/` |

Le cycle recommandé est décrit dans la section [Modules Forge — Cycle recommandé](#modules-cycle-recommande) de cette référence.

### Cycle d'utilisation recommandé

Usage typique combinant les trois briques :

1. Déclarer les statuts d'une entité dans `workflow.json` et câbler les transitions dans le contrôleur CRUD.
2. Enregistrer un événement statistique à chaque transition (`StatsEvent.record(...)`).
3. Empaqueter l'entité, son contrôleur et ses vues dans un module (`module.json`) pour les réutiliser dans un autre projet.
4. Installer le module dans le projet cible avec `forge module:install`, `forge module:files`, `forge module:routes`.

Les trois briques sont indépendantes : Workflow ne dépend pas des Statistiques, les Modules ne dépendent pas du Workflow.

### Limites actuelles

Workflow :

- pas de callbacks automatiques sur les transitions ;
- pas de journalisation native des changements d'état ;
- pas de transitions parallèles ni de fork/join.

Statistiques :

- pas d'agrégation en temps réel ;
- pas d'export CSV ni d'API JSON dédié ;
- les événements sont stockés dans la base applicative, sans partitionnement.

Modules :

- pas de `forge module:update` ni de `forge module:uninstall` ;
- pas de gestion de dépendances entre modules ;
- pas de marketplace ni de téléchargement distant ;
- les audits de durcissement (`MODULE-ROUTES-RUNTIME-AUDIT-001`, `MODULE-FILES-SECURITY-001`) sont prévus avant les starters.

---

