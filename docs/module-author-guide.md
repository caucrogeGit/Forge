# Créer un module Forge

Ce guide explique comment créer un module Forge réutilisable : structure,
manifeste, installation, routes, suppression et bonnes pratiques.

---

## Objectif

Un module Forge est une brique d'extension installable dans un projet existant.
Il permet de partager des contrôleurs, des vues, des routes ou des entités
entre projets sans dupliquer le code.

---

## Ce qu'est un module Forge

Un module Forge est un dossier autonome contenant un fichier `module.json`
(le manifeste) et les fichiers qu'il apporte.

Il s'installe dans un projet Forge existant via les commandes `forge module:*`.
Forge trace les fichiers qu'il a copiés dans `forge_modules.json` et peut
les supprimer proprement.

### Différences entre module, starter et application

| Type | Rôle |
|---|---|
| **Module** | Brique réutilisable ajoutée à un projet existant |
| **Starter** | Point de départ complet pour initialiser un nouveau projet ou une démonstration |
| **Application** | Projet Forge concret utilisé en production |

Un **starter** crée un projet ou une application de démonstration.
Un **module** ajoute une fonctionnalité à un projet qui existe déjà.
Une **application** utilise Forge comme moteur — elle n'est ni un module ni un starter.

---

## Ce qu'un module ne doit pas être

- Une application métier complète déguisée en module
- Un substitut à `forge new` pour initialiser un projet
- Un système de plugins avec résolution automatique de dépendances
- Un module qui télécharge du code depuis Internet

Un module doit rester petit, ciblé et auditable.

---

## Structure minimale d'un module

Les modules sont placés dans le dossier `modules/` à la racine du projet.
Forge cherche dans ce dossier par défaut lors de `forge module:list` et
`forge module:install`.

```text
modules/
└── mon_module/
    ├── module.json                       # manifeste (obligatoire)
    ├── controllers/                      # si provides: ["controllers"]
    │   └── mon_module_controller.py
    └── routes.py                         # si provides: ["routes"]
```

Le nom du dossier doit correspondre au champ `name` dans `module.json`.

### Exemple avec vues et entités

```text
modules/
└── mon_module/
    ├── module.json
    ├── controllers/
    │   └── mon_module_controller.py
    ├── views/
    │   └── mon_module/
    │       └── list.html
    ├── entities/
    │   └── MonEntite/
    │       └── MonEntite.json
    └── routes.py
```

---

## Manifeste du module

Le manifeste est le fichier `module.json` placé à la racine du dossier du module.

```json
{
  "name": "mon_module",
  "label": "Mon module",
  "version": "0.1.0",
  "description": "Description courte du module.",
  "provides": ["controllers", "routes"],
  "paths": {
    "controllers": "controllers",
    "routes": "routes.py"
  }
}
```

### Champs du manifeste

| Champ | Requis | Rôle |
|---|---|---|
| `name` | Oui | Identifiant snake_case minuscule. Format : `^[a-z][a-z0-9_]*$` |
| `label` | Oui | Libellé lisible. Pas de HTML. |
| `version` | Oui | Version au format `MAJOR.MINOR.PATCH` |
| `description` | Oui | Description courte. Pas de HTML. |
| `provides` | Non | Liste de briques fournies (voir tableau ci-dessous) |
| `paths` | Non | Chemins des sources pour chaque brique déclarée dans `provides` |

### Valeurs autorisées pour `provides`

| Valeur | Destination dans le projet | Copie via `module:files` ? |
|---|---|---|
| `entities` | `mvc/entities/` | Oui |
| `controllers` | `mvc/controllers/` | Oui |
| `views` | `mvc/views/` | Oui |
| `docs` | `docs/modules/<name>/` | Oui |
| `routes` | généré dans `mvc/routes_<module>.py` | Via `module:routes` |
| `static` | déclaré, non copié automatiquement | Non |
| `migrations` | déclaré, non copié automatiquement | Non |

!!! warning "Règle `routes`"
    Si `provides` contient `"routes"`, alors `paths.routes` est obligatoire.
    Si `provides` contient `"controllers"`, `"views"` ou `"entities"`,
    le chemin correspondant dans `paths` est obligatoire.

---

## Fichiers installables

Lors de `forge module:files`, Forge copie les fichiers des briques `entities`,
`controllers`, `views` et `docs` vers leur destination dans le projet.

Les fichiers `static` et `migrations` sont déclarables dans le manifeste
mais ne sont pas copiés automatiquement par Forge — leur gestion reste manuelle.

**Fichiers ignorés lors de la copie** : `__pycache__/`, `.git/`, `.venv/`,
fichiers `.env`, `.DS_Store`, `*.pyc`, `*.tmp`, `*.bak`, liens symboliques.

Forge refuse l'installation si un fichier cible existe déjà. C'est une
protection contre l'écrasement silencieux.

---

## Routes de module

Si votre module expose des routes, déclarez un fichier `routes.py` contenant
une fonction `register_routes(router)`.

```python
# modules/mon_module/routes.py

def register_routes(router):
    from mvc.controllers.mon_module_controller import MonModuleController
    router.get("/mon-module/", MonModuleController, "index")
```

### Génération du fichier de routes dédié

`forge module:routes mon_module` génère un fichier `mvc/routes_mon_module.py`
**sans modifier** `mvc/routes.py` :

```python
# mvc/routes_mon_module.py (généré par Forge — régénérable)
"""Routes du module Forge "mon_module".

Fichier genere par `forge module:routes mon_module`. Regenerable.
Pour activer ces routes, ajoutez dans mvc/routes.py :

    from mvc.routes_mon_module import register_mon_module_routes
    register_mon_module_routes(router)
"""
from modules.mon_module.routes import register_routes as register_mon_module_routes

__all__ = ["register_mon_module_routes"]
```

### Branchement explicite dans mvc/routes.py

La commande affiche les deux lignes à ajouter manuellement dans `mvc/routes.py` :

```python
# À ajouter manuellement dans mvc/routes.py
from mvc.routes_mon_module import register_mon_module_routes
register_mon_module_routes(router)
```

**Forge ne modifie jamais `mvc/routes.py` automatiquement.**
Le branchement est visible, lisible, modifiable et réversible.

### Comportement de module:install

`forge module:install` enregistre le module dans `forge_modules.json`.
Il **ne génère pas** de fichier de routes et **n'écrit pas** dans `mvc/routes.py`.

### Comportement de module:routes

`forge module:routes` génère `mvc/routes_<module>.py` et affiche les lignes
à copier dans `mvc/routes.py`. Il **ne modifie pas** `mvc/routes.py`.

### Comportement de module:remove

`forge module:remove` supprime les fichiers copiés par `module:files` et
nettoie le registre.

Pour les routes, **Forge ne supprime pas `mvc/routes_<module>.py`** ni
les lignes que vous avez ajoutées dans `mvc/routes.py`. Ces fichiers restent
sur le disque après la suppression — à retirer manuellement.

!!! note "Compatibilité arrière"
    Si un projet existant contient d'anciens blocs à marqueurs
    (`# forge-module-routes:<nom>:start/end`) dans `mvc/module_routes.py`,
    `forge module:remove` peut les nettoyer. Ce mécanisme est conservé pour
    compat arrière uniquement — les nouveaux projets utilisent le fichier dédié.

### Migration depuis l'ancien mécanisme injecté

Si un ancien projet contient un bloc à marqueurs dans `mvc/module_routes.py`,
Forge ne le maintient plus automatiquement. Migration recommandée :

1. Générer `mvc/routes_<module>.py` avec `forge module:routes <nom>`.
2. Vérifier le contenu du fichier généré.
3. Ajouter manuellement les deux lignes dans `mvc/routes.py`.
4. Supprimer manuellement l'ancien bloc dans `mvc/module_routes.py` si nécessaire.
5. Relancer les tests.

---

## Templates de module

Si votre module fournit des templates, déclarez `"views"` dans `provides`
et indiquez le chemin source dans `paths.views`.

```json
{
  "provides": ["views"],
  "paths": {
    "views": "views"
  }
}
```

Forge copiera le contenu du dossier `views/` du module vers `mvc/views/`.

Exemple de structure recommandée pour éviter les conflits :

```text
modules/mon_module/
└── views/
    └── mon_module/       # sous-dossier avec le nom du module
        ├── list.html
        └── show.html
```

---

## Fichiers statiques

Les fichiers statiques ne sont pas copiés automatiquement par `forge module:files`.
Déclarez `"static"` dans `provides` pour signaler l'intention, mais copiez
les fichiers manuellement dans `static/` de votre projet.

---

## Installation du module

Le cycle complet d'installation se fait en trois étapes :

```bash
# 1. Vérifier que le module est détectable
forge module:list

# 2. Enregistrer le module dans forge_modules.json
forge module:install mon_module

# 3. Copier les fichiers du module dans le projet
forge module:files mon_module

# 4. Générer le fichier de routes (uniquement si le module fournit des routes)
#    Puis ajouter manuellement les lignes affichées dans mvc/routes.py
forge module:routes mon_module
```

### Ce que chaque commande fait

| Commande | Action |
|---|---|
| `forge module:list` | Scanne `modules/` et affiche les modules valides et invalides |
| `forge module:install <nom>` | Enregistre le module dans `forge_modules.json` |
| `forge module:files <nom>` | Copie les fichiers dans le projet, trace les chemins dans `forge_modules.json` |
| `forge module:routes <nom>` | Génère `mvc/routes_<nom>.py` et affiche les lignes à ajouter dans `mvc/routes.py` |
| `forge module:remove <nom>` | Supprime les fichiers non modifiés, nettoie le registre (`mvc/routes_<nom>.py` à retirer manuellement) |

Toutes ces commandes acceptent `--dry-run` pour simuler l'opération sans rien écrire.

### Dossier de modules alternatif

Par défaut, Forge cherche dans `modules/`. Pour utiliser un autre dossier :

```bash
forge module:list --path /chemin/vers/mes_modules
forge module:install mon_module --path /chemin/vers/mes_modules
```

---

## Réinstallation et double installation

Forge refuse d'installer un module déjà présent dans `forge_modules.json` :

```text
Module déjà installé : mon_module
```

Pour réinstaller, supprimez d'abord le module avec `forge module:remove`.

Forge refuse aussi d'écraser un fichier existant lors de `forge module:files`.
Si un fichier cible existe déjà, l'installation est annulée sans aucune modification.

---

## Suppression du module

```bash
forge module:remove mon_module
```

La suppression suit cette règle :

> Forge ne supprime que ce qu'il peut prouver avoir installé sans modification.

Concrètement :

| Situation | Action |
|---|---|
| Fichier identique à la source du module | Supprimé |
| Fichier modifié par l'utilisateur | Conservé (non supprimé) |
| Source du module introuvable | Fichier conservé, raison signalée |
| Fichier déjà absent | Ignoré |

Le registre `forge_modules.json` est nettoyé.
Les fichiers copiés par `module:files` sont supprimés s'ils n'ont pas été modifiés.
`mvc/routes_<module>.py` et les lignes ajoutées dans `mvc/routes.py` restent
sur le disque — à retirer manuellement si souhaité.

---

## Préservation des fichiers modifiés

Si vous modifiez un fichier installé par Forge (par exemple un contrôleur),
`forge module:remove` le conservera au lieu de le supprimer.

Forge calcule un hash SHA256 du fichier installé et le compare au fichier
source original. Si les deux diffèrent, le fichier est conservé et signalé :

```text
Fichiers conservés (non supprimés) :
  - mvc/controllers/mon_module_controller.py (modifié manuellement, conservé)
```

Cette règle est testée par le test E2E `TestModuleRemovePreservesModified`.
Elle garantit que vos modifications ne peuvent pas être perdues lors d'une
désinstallation.

---

## Vérifier le projet après installation

Après chaque installation ou suppression de module :

```bash
forge project:check
```

Vérifie la cohérence structurelle : entités, routes, templates, modules.

```bash
forge project:audit
```

Produit un rapport détaillé sur la qualité et les éventuels problèmes.
Un projet avec un module correctement installé doit passer sans `fail`.

---

## Tester un module

Un module bien construit est testable de façon isolée.

Structure de test recommandée :

```text
tests/
└── test_mon_module.py
```

Exemple de test minimal :

```python
from pathlib import Path
from core.modules import load_module_manifest

def test_manifeste_valide():
    manifest = load_module_manifest("modules/mon_module/module.json")
    assert manifest.name == "mon_module"
    assert manifest.version

def test_fichiers_sources_existent():
    assert Path("modules/mon_module/routes.py").exists()
    assert Path("modules/mon_module/controllers/mon_module_controller.py").exists()
```

Pour tester le cycle complet (install → files → routes → remove) dans un
projet isolé, consultez `tests/test_e2e_module.py` comme exemple de test E2E
avec `tmp_path` et `monkeypatch.chdir`.

---

## Bonnes pratiques

- **Petit et ciblé** — un module ajoute une brique, pas une application entière.
- **Noms explicites** — `mon_module` (snake_case, sans ambiguïté sur la fonction).
- **Routes préfixées** — utilisez un préfixe URL pour éviter les conflits avec d'autres routes (`/mon-module/`).
- **Fichiers tracés** — tout ce que Forge installe est tracé dans `forge_modules.json`.
- **Pas d'écrasement silencieux** — Forge refuse si un fichier cible existe déjà.
- **Documentation minimale** — décrivez la fonction du module et ses routes dans `description`.
- **Tests** — testez au minimum le manifeste et les fichiers sources.
- **Versionnez le module** — incrémentez `version` à chaque modification significative.

---

## Limites actuelles

| Limite | État |
|---|---|
| Pas de marketplace ni de téléchargement distant | Les modules sont locaux uniquement |
| Pas de résolution automatique de dépendances | Aucun mécanisme `requires` dans le manifeste |
| `static` et `migrations` non copiés automatiquement | Gestion manuelle requise |
| Pas de mise à jour automatique | Supprimez et réinstallez pour mettre à jour |
| Pas d'interface Forge Design pour les modules | Forge Design est un projet séparé |
| Pas de résolution de conflits complexe | Forge refuse et laisse le choix à l'utilisateur |
| Pas de migration DB avancée intégrée | Gérez vos scripts SQL manuellement |

---

## Exemple minimal complet

### 1. Créer la structure

```text
modules/
└── mon_module/
    ├── module.json
    ├── controllers/
    │   └── mon_module_controller.py
    └── routes.py
```

### 2. Écrire le manifeste

```json
{
  "name": "mon_module",
  "label": "Mon module",
  "version": "0.1.0",
  "description": "Module d'exemple Forge.",
  "provides": ["controllers", "routes"],
  "paths": {
    "controllers": "controllers",
    "routes": "routes.py"
  }
}
```

### 3. Écrire le contrôleur

```python
# modules/mon_module/controllers/mon_module_controller.py

class MonModuleController:
    def index(self, request):
        return {"items": []}
```

### 4. Écrire les routes

```python
# modules/mon_module/routes.py

def register_routes(router):
    from mvc.controllers.mon_module_controller import MonModuleController
    router.get("/mon-module/", MonModuleController, "index")
```

### 5. Installer le module

```bash
forge module:list
forge module:install mon_module
forge module:files mon_module
forge module:routes mon_module
forge project:check
forge project:audit
```

---

## Voir aussi

- [API et CLI](reference.md) — liste complète des commandes `forge module:*`
- [Application complète](app-complete-tutorial.md) — exemple avec plusieurs entités
- [Contrat de stabilité](stability-contract.md) — garanties sur les fichiers préservés
- [Vue d'ensemble des starters](starters/index.md) — différence module / starter
