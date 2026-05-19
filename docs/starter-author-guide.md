# Créer un starter Forge

Ce guide explique comment créer un nouveau starter Forge : structure, métadonnées,
entités, relations, routes, fichiers applicatifs, tests et bonnes pratiques.

!!! info "Où vivent les starters ?"
    Les starters font partie de la distribution Forge. Créer un starter consiste
    à ajouter un répertoire dans `forge_cli/starters/data/`. C'est une
    contribution au projet Forge, pas une configuration par projet.
    Pour ajouter une brique réutilisable à un projet existant, préférez
    un [module Forge](module-author-guide.md).

---

## Objectif

Un starter est une base applicative reproductible. Il permet de générer
rapidement un squelette cohérent pour illustrer un usage de Forge.

---

## Ce qu'est un starter Forge

Un starter est un dossier dans `forge_cli/starters/data/` contenant un
`starter.json` et les fichiers qu'il va déployer dans un projet.

La commande `forge starter:build <id>` lit ce dossier, génère les entités,
injecte les routes et copie les fichiers applicatifs dans le projet courant.

---

## Différence starter / module / application

| Type | Rôle |
|---|---|
| **Starter** | Base applicative reproductible pour démarrer ou démontrer un usage |
| **Module** | Brique réutilisable installée dans un projet existant |
| **Application** | Projet final développé et maintenu par l'utilisateur |

Un **starter** initialise un projet ou en installe une couche de démonstration.
Il ne persiste pas dans le projet de façon traçable — il copie des fichiers
que l'utilisateur prend ensuite en charge.

Un **module** s'installe de façon traçable dans `forge_modules.json` et
peut être désinstallé proprement. Voir [Créer un module](module-author-guide.md).

---

## Ce qu'un starter ne doit pas être

- Une application métier complète avec des dizaines d'entités
- Un système de configuration de Forge lui-même
- Un mécanisme de téléchargement distant
- Un générateur de code arbitraire non lié au MVC Forge

Un starter doit rester lisible, reproductible et auditable.

---

## Types de starters

Forge supporte trois types de starters, définis par le champ `kind` dans `starter.json`.

| `kind` | Usage | Exemple |
|---|---|---|
| `crud` | CRUD simple pour une seule entité | starter 1 — Contacts |
| `application` | Application multi-entités avec relations | starters 2, 3, 4 |
| `skeleton` | Démonstrateur riche avec fichiers applicatifs complets | starter 5 |

### `kind=crud`

Build automatisé en 7 étapes : `make:entity` → injection JSON canonique →
`check:model` → `build:model` → `db:apply` → `make:crud` → injection routes.

Les routes sont déclarées directement dans `starter.json` sous la clé `routes`.

### `kind=application`

Build automatisé en 7 étapes avec plusieurs entités : création des entités →
injection des JSON canoniques → injection `relations.json` → `check:model` →
`build:model` → `db:apply` → copie fichiers applicatifs → injection routes.

Les routes sont lues depuis un fichier `routes.py.snippet`.

### `kind=skeleton`

Build en 2 étapes : copie des fichiers applicatifs → injection routes depuis
`routes.py.snippet`. Aucune entité gérée automatiquement.

---

## Structure d'un starter

Tous les starters résident dans `forge_cli/starters/data/` :

```text
forge_cli/starters/data/
└── <starter-id>/
    ├── starter.json           # métadonnées (obligatoire)
    ├── <entity>.json          # JSON canonique d'entité (kind=crud)
    ├── entities/              # JSON canoniques d'entités (kind=application)
    │   └── <entity>.json
    ├── relations.json         # relations globales (kind=application si pertinent)
    ├── routes.py.snippet      # bloc de routes à injecter (kind=application/skeleton)
    └── files/                 # fichiers applicatifs à copier dans le projet
        ├── mvc/controllers/
        ├── mvc/models/
        ├── mvc/forms/
        ├── mvc/views/
        └── scripts/
```

---

## Métadonnées du starter

Le fichier `starter.json` déclare toutes les métadonnées.

### Champs communs à tous les kinds

| Champ | Requis | Rôle |
|---|---|---|
| `id` | Oui | Identifiant unique kebab-case (ex : `mon-starter`) |
| `number` | Oui | Numéro d'affichage dans `forge starter:list` |
| `name` | Oui | Libellé humain |
| `kind` | Non | `"crud"` (défaut), `"application"`, `"skeleton"` |
| `aliases` | Non | Identifiants alternatifs pour `forge starter:build` |
| `description` | Non | Description courte affichée dans `forge starter:list` |
| `status` | Non | `"available"` pour visible, autre pour masqué |
| `requires_db` | Non | `true` si MariaDB est nécessaire à l'exécution |
| `routes_marker` | Oui | Identifiant unique des marqueurs de routes dans `mvc/routes.py` |
| `home_route` | Non | Chemin à câbler comme route `/` dans `mvc/routes.py` |
| `check_paths` | Non | Chemins vérifiés pour détecter une installation existante |
| `open_url` | Non | URL suggérée après installation |
| `test_command` | Non | Commande de test post-installation affichée à l'utilisateur |
| `doc_url` | Non | URL de la documentation du starter |

### Champs spécifiques à `kind=crud`

| Champ | Rôle |
|---|---|
| `entity` | Nom de l'entité (ex : `"Contact"`) |
| `routes` | Déclaration des routes : `prefix` + liste d'`actions` |

### Champs spécifiques à `kind=application`

| Champ | Rôle |
|---|---|
| `entities` | Liste de `{"entity": "Nom", "json": "entities/nom.json"}` |
| `relations_json` | Chemin vers `relations.json` dans le dossier du starter |
| `routes_snippet` | Fichier contenant le bloc de routes à injecter (ex : `"routes.py.snippet"`) |
| `supports_public` | `false` si `--public` n'est pas applicable |

### Exemple — `kind=crud`

```json
{
  "id": "mon-starter",
  "number": 6,
  "name": "Mon starter",
  "entity": "Produit",
  "aliases": ["6", "produit", "mon-starter"],
  "description": "Starter 6 — CRUD simple de produits",
  "status": "available",
  "requires_db": true,
  "home_route": "/produits",
  "routes_marker": "mon-starter",
  "routes": {
    "prefix": "/produits",
    "actions": [
      {"method": "GET",  "path": "",             "action": "index",   "name": "produit_index"},
      {"method": "GET",  "path": "/new",         "action": "new",     "name": "produit_new"},
      {"method": "POST", "path": "",             "action": "create",  "name": "produit_create"},
      {"method": "GET",  "path": "/{id}",        "action": "show",    "name": "produit_show"},
      {"method": "GET",  "path": "/{id}/edit",   "action": "edit",    "name": "produit_edit"},
      {"method": "POST", "path": "/{id}",        "action": "update",  "name": "produit_update"},
      {"method": "POST", "path": "/{id}/delete", "action": "destroy", "name": "produit_destroy"}
    ]
  },
  "check_paths": [
    "mvc/entities/produit",
    "mvc/controllers/produit_controller.py"
  ]
}
```

### Exemple — `kind=application`

```json
{
  "id": "mon-starter-app",
  "number": 7,
  "name": "Mon starter app",
  "kind": "application",
  "entities": [
    {"entity": "Categorie", "json": "entities/categorie.json"},
    {"entity": "Produit",   "json": "entities/produit.json"}
  ],
  "relations_json": "relations.json",
  "aliases": ["7", "mon-starter-app"],
  "description": "Starter 7 — Application produits et catégories",
  "status": "available",
  "requires_db": true,
  "supports_public": false,
  "home_route": "/produits",
  "routes_marker": "mon-starter-app",
  "routes_snippet": "routes.py.snippet",
  "open_url": "https://localhost:8000/produits",
  "check_paths": [
    "mvc/entities/categorie",
    "mvc/entities/produit",
    "mvc/entities/relations.json"
  ]
}
```

---

## Entités fournies par un starter

### `kind=crud` — entité unique

Placez le JSON canonique directement dans `forge_cli/starters/data/<id>/` :

```text
forge_cli/starters/data/mon-starter/
├── starter.json
└── Produit.json          # ou produit.json — nom libre
```

Forge injecte ce JSON dans `mvc/entities/produit/produit.json` en remplaçant
le JSON minimal généré par `make:entity --no-input`.

### `kind=application` — plusieurs entités

Placez les JSON canoniques dans `entities/` :

```text
forge_cli/starters/data/mon-starter-app/
├── starter.json
├── entities/
│   ├── categorie.json
│   └── produit.json
└── relations.json
```

Le JSON d'entité reste la source canonique. Forge génère automatiquement
`<entity>.sql` et `<entity>_base.py` à partir de ce JSON lors du build.

---

## Relations fournies par un starter

Si le starter déclare une `kind=application` avec des entités liées, fournissez
un `relations.json` au format canonique :

```json
{
  "$schema": "../../schemas/relations.schema.json",
  "schema_version": "1.0",
  "relations": [
    {
      "type": "many_to_one",
      "from": "Produit",
      "to": "Categorie",
      "name": "categorie",
      "foreign_key": "categorie_id",
      "nullable": true,
      "on_delete": "set_null"
    }
  ]
}
```

Lors du build, Forge copie ce fichier dans `mvc/entities/relations.json` du
projet. `relations.sql` est généré automatiquement.

---

## Fichiers applicatifs (dossier `files/`)

Pour les starters `application` et `skeleton`, les fichiers applicatifs sont
placés dans un dossier `files/` qui reflète la structure cible dans le projet.

```text
forge_cli/starters/data/mon-starter-app/
└── files/
    ├── mvc/
    │   ├── controllers/
    │   │   ├── categorie_controller.py
    │   │   └── produit_controller.py
    │   ├── models/
    │   │   ├── categorie_model.py
    │   │   └── produit_model.py
    │   ├── forms/
    │   │   └── produit_form.py
    │   └── views/
    │       ├── layouts/
    │       │   └── app.html
    │       ├── categorie/
    │       │   └── index.html
    │       └── produit/
    │           ├── index.html
    │           └── show.html
    └── scripts/
        └── seed_produits.py
```

Forge copie l'intégralité du contenu de `files/` à la racine du projet lors
du build.

!!! warning "Écrasement silencieux"
    `forge starter:build --force` supprime les fichiers existants avant la copie.
    Sans `--force`, le build est annulé si des fichiers cibles existent déjà.
    Les fichiers du dossier `files/` ne bénéficient pas de la protection SHA256
    des modules — ils sont copiés tels quels.

---

## Routes injectées

### Bloc de routes pour `kind=crud`

Les routes sont déclarées dans `starter.json` sous la clé `routes`.
Forge les génère et les injecte dans `mvc/routes.py` avec des marqueurs.

Résultat dans `mvc/routes.py` :

```python
# forge-starter:mon-starter:start
from mvc.controllers.produit_controller import ProduitController

with router.group("/produits") as g:
    g.add("GET",  "",             ProduitController.index,   name="produit_index")
    g.add("GET",  "/new",         ProduitController.new,     name="produit_new")
    g.add("POST", "",             ProduitController.create,  name="produit_create")
    g.add("GET",  "/{id}",        ProduitController.show,    name="produit_show")
    g.add("GET",  "/{id}/edit",   ProduitController.edit,    name="produit_edit")
    g.add("POST", "/{id}",        ProduitController.update,  name="produit_update")
    g.add("POST", "/{id}/delete", ProduitController.destroy, name="produit_destroy")
# forge-starter:mon-starter:end
```

### Fichier snippet pour `kind=application` et `kind=skeleton`

Créez un fichier `routes.py.snippet` contenant le bloc complet avec marqueurs :

```python
# forge-starter:mon-starter-app:start
from mvc.controllers.categorie_controller import CategorieController
from mvc.controllers.produit_controller import ProduitController

with router.group("/categories", public=True, csrf=False) as g:
    g.add("GET", "", CategorieController.index, name="categorie_index")

with router.group("/produits", public=True, csrf=False) as g:
    g.add("GET",  "",             ProduitController.index,   name="produit_index")
    g.add("GET",  "/new",         ProduitController.new,     name="produit_new")
    g.add("POST", "",             ProduitController.create,  name="produit_create")
    g.add("GET",  "/{id}",        ProduitController.show,    name="produit_show")
    g.add("GET",  "/{id}/edit",   ProduitController.edit,    name="produit_edit")
    g.add("POST", "/{id}",        ProduitController.update,  name="produit_update")
    g.add("POST", "/{id}/delete", ProduitController.destroy, name="produit_destroy")
# forge-starter:mon-starter-app:end
```

Le `routes_marker` dans `starter.json` doit correspondre exactement au
marqueur utilisé dans le snippet. C'est ce marqueur qui permet de détecter
si le starter est déjà installé et de prévenir les doublons.

### Route d'accueil

Si `home_route` est défini dans `starter.json`, Forge remplace la route `/`
dans `mvc/routes.py` par une redirection vers ce chemin.

---

## Templates et layouts

Les templates sont placés dans `files/mvc/views/`. Suivez la structure
conventionnelle de Forge :

```text
files/mvc/views/
├── layouts/
│   └── app.html           # layout principal (optionnel — écrase le layout existant)
└── <entite>/
    ├── index.html          # liste
    ├── show.html           # fiche
    └── form.html           # création / modification
```

!!! warning "Layout partagé"
    Si votre starter fournit un `mvc/views/layouts/app.html`, il écrase le
    layout existant du projet. Documentez ce comportement dans la description
    du starter.

---

## Build et validation

### Commandes disponibles

```bash
# Lister les starters disponibles
forge starter:list

# Simuler le build (aucun fichier écrit)
forge starter:build <id|n|alias> --dry-run

# Build complet (MariaDB requis si requires_db=true)
forge starter:build <id|n|alias>

# Build avec initialisation MariaDB
forge starter:build <id|n|alias> --init-db

# Build en écrasant les fichiers existants
forge starter:build <id|n|alias> --force
```

### Vérifier après le build

```bash
forge project:check    # cohérence structurelle
forge project:audit    # rapport qualité
pytest                 # suite de tests Forge
python -m compileall -q .
```

Un starter correctement installé doit passer `forge project:check` et
`forge project:audit` sans `fail`.

---

## Tester un starter

Les tests E2E des starters sont dans `tests/test_e2e_starter.py`. Chaque
starter ajouté à Forge doit être testé dans ce fichier ou dans un fichier
de test dédié.

Stratégie de test recommandée :

1. Créer un projet temporaire minimal (sans MariaDB réelle).
2. Mocker `apply_model_sql` pour ne pas nécessiter de base.
3. Builder le starter avec `build(meta, init_db=False)`.
4. Vérifier les fichiers créés via `check_paths`.
5. Appeler `run_project_check` et `run_project_audit`.

```python
from pathlib import Path
import pytest
from unittest.mock import patch
from forge_cli.starters.registry import resolve
from forge_cli.starters.builder import build
from forge_cli.project_check import run_project_check
from forge_cli.project_audit import run_project_audit

def test_mon_starter(tmp_path, monkeypatch):
    # Projet minimal
    (tmp_path / "config.py").write_text("APP_NAME='Test'\n")
    (tmp_path / "mvc" / "routes.py").write_text(
        "from core.http.router import Router\nrouter = Router()\n"
    )
    # ... autres fichiers requis ...
    monkeypatch.chdir(tmp_path)

    meta = resolve("mon-starter")
    with patch("forge_cli.entities.db_apply.apply_model_sql", return_value=[]):
        build(meta, init_db=False)

    assert (tmp_path / "mvc/controllers/produit_controller.py").exists()
    assert (tmp_path / "mvc/views/produit/index.html").exists()

    result_check = run_project_check(tmp_path)
    assert result_check.ok

    result_audit = run_project_audit(tmp_path)
    assert not any(r.level == "fail" for r in result_audit)
```

Les tests E2E de starters n'utilisent pas de MariaDB réelle. `apply_model_sql`
est toujours moquée.

---

## Bonnes pratiques

- **Petit et explicite** — un starter illustre un usage, pas toute la richesse de Forge.
- **Lisible** — le code des contrôleurs et vues doit être compréhensible, pas optimal.
- **Routes préfixées** — utilisez un préfixe URL cohérent avec l'identifiant du starter.
- **Marqueurs uniques** — `routes_marker` doit être unique entre tous les starters.
- **`check_paths` complet** — listez suffisamment de chemins pour détecter une installation existante.
- **`--dry-run` fonctionnel** — vérifiez que le dry-run affiche le bon résumé.
- **Documentez les scripts** — si le starter inclut des scripts (`seed_*.py`), mentionnez-les dans `test_command`.
- **Testez avec `project:check`** — un starter installé doit passer sans `fail`.
- **Pas de logique métier profonde** — le starter montre comment Forge fonctionne, pas comment résoudre un problème métier précis.

---

## Conventions de langage des starters

*Ticket de référence : STARTER-CONVENTIONS-DOC-001. Appliqué dans les starters officiels par STARTER-LANG-NORMALIZE-001.*

### Principe

Un starter Forge peut être francophone côté domaine : noms de tables, colonnes,
labels d'interface, textes utilisateur. C'est le choix du domaine métier, pas
une contrainte du framework.

En revanche, le code Python exposé dans les contrôleurs, modèles et fonctions
d'un starter doit utiliser des noms clairs, stables et cohérents — en anglais,
conformément à l'[ADR-003](adr/003-language-convention.md).

La règle ne concerne pas les noms SQL. Elle concerne les fonctions Python,
les noms de paramètres et les clés de dictionnaire exposées au reste du code.

### SQL et schéma

- Les colonnes SQL d'un starter peuvent avoir des noms français ou métier
  (`UtilisateurId`, `Login`, `PasswordHash`, `Actif`).
- Ne pas renommer ces colonnes sans migration SQL explicite — le schéma
  appartient au domaine applicatif, pas au framework.
- Les requêtes SQL et les chaînes d'interpolation peuvent contenir ces noms
  directement.

```sql
-- Autorisé dans un starter
SELECT UtilisateurId, Login, PasswordHash, Actif
FROM utilisateur
WHERE Login = ?
```

### Code Python

- Les fonctions Python recommandées dans un starter doivent avoir des noms
  en anglais : `get_user_by_login`, `get_user_by_id`, `build_auth_user`.
- Les variables intermédiaires locales peuvent rester françaises si elles sont
  des alias courts d'un résultat SQL (`utilisateur = fetch_one(...)`).
- Les clés de dictionnaire exposées au template ou à d'autres fonctions doivent
  être normalisées : `{"id": ..., "login": ..., "prenom": ...}`.

```python
# Correct : noms de fonctions anglais, clés normalisées
def get_user_by_id(user_id: int) -> dict | None:
    row = fetch_one(GET_UTILISATEUR_PAR_ID, (user_id,))
    if not row:
        return None
    return {
        "id": row["UtilisateurId"],
        "login": row["Login"],
        "prenom": row.get("Prenom") or "",
    }
```

### Labels et interface utilisateur

Les textes visibles par l'utilisateur final peuvent rester entièrement en
français, sans restriction :

- Labels de formulaire : "Identifiant", "Mot de passe", "Connexion"
- Titres de page : "Tableau de bord", "Bienvenue"
- Messages d'erreur : "Identifiant ou mot de passe incorrect."

Ce qui pose problème n'est pas le français dans l'UI, mais l'exposition de
noms SQL métier dans les API Python.

### Pont SQL → Python

Le passage du résultat SQL brut vers un objet Python propre doit être
**explicite** et **localisé dans le modèle** (`mvc/models/auth_model.py`).

La fonction `build_auth_user()` est le pont recommandé pour les starters auth.
Elle traduit un dict SQL en `AuthUser` via `normalize_auth_user()` :

```python
from core.auth import AuthUser, normalize_auth_user

def build_auth_user(utilisateur: dict) -> AuthUser:
    """Convertit un dict DB en AuthUser pour core.auth.login_user."""
    email = utilisateur.get("Email") or utilisateur.get("Login") or ""
    return normalize_auth_user({
        "id": utilisateur["UtilisateurId"],
        "email": email,
        "password_hash": utilisateur["PasswordHash"],
        "is_active": bool(utilisateur.get("Actif", True)),
    })
```

Le code réel peut utiliser directement `normalize_auth_user()` si une fonction
dédiée n'est pas justifiée — l'important est que le mapping soit isolé hors du
contrôleur.

### AuthUser et user_loader

`AuthUser` est la forme Python propre attendue par l'auth canonique de Forge :

- `login_user(request, auth_user)` attend un `AuthUser`.
- `current_user(request, user_loader)` appelle un `user_loader(user_id)` pour
  recharger l'utilisateur depuis la base.
- `get_authenticated_user_id(request)` retourne l'identifiant stocké en session.

Le contrôleur ne doit pas construire un `AuthUser` directement depuis les clés
SQL. Cette construction appartient au modèle :

```python
# Dans le contrôleur — correct
auth_user = build_auth_user(utilisateur)
login_user(request, auth_user)

# Dans le contrôleur — à éviter
auth_user = AuthUser(
    id=utilisateur["UtilisateurId"],   # clé SQL dans le contrôleur
    email=utilisateur["Login"],
    password_hash=utilisateur["PasswordHash"],
    is_active=True,
)
```

### Exemples corrects

```python
# auth_model.py — pont SQL → AuthUser dans le modèle
def build_auth_user(row: dict) -> AuthUser:
    return normalize_auth_user({
        "id": row["UtilisateurId"],
        "email": row.get("Email") or row.get("Login") or "",
        "password_hash": row["PasswordHash"],
        "is_active": bool(row.get("Actif", True)),
    })

# auth_controller.py — contrôleur propre
utilisateur = get_user_by_login(login)
if utilisateur and _check_password(password, utilisateur["PasswordHash"]):
    auth_user = build_auth_user(utilisateur)
    login_user(request, auth_user)

# suivi_controller.py — lecture de l'utilisateur courant
user_id = get_authenticated_user_id(request)
utilisateur = get_user_by_id(user_id) if user_id else None
```

### Exemples à éviter

```python
# À éviter : exposition de noms SQL dans la signature d'une fonction publique
def connecter_utilisateur(UtilisateurId, MotDePasse):
    ...

# À éviter : construction AuthUser inline dans le contrôleur
auth_user = AuthUser(
    id=utilisateur["UtilisateurId"],
    email=utilisateur["Login"],
    ...
)

# À éviter : API dépréciée du core
from core.security.session import get_user, authenticate_session
utilisateur = get_user(request)           # déprécié
nouveau_id = authenticate_session(sid, u) # déprécié
```

### Ce que le core ne doit jamais absorber

Le core Forge est générique. Il ne connaît pas les noms de colonnes applicatifs
(`UtilisateurId`, `Login`, `MotDePasse`). Ces noms appartiennent au domaine du
starter ou de l'application.

Le pont doit vivre dans le starter ou dans une fonction de compatibilité
explicitement isolée dans le modèle — jamais dans `core/auth/`, `core/security/`
ou tout autre fichier du core.

Si un starter a besoin d'un mapping spécifique, il l'écrit dans son propre
`mvc/models/auth_model.py`. Le core ne s'adapte pas au schéma du starter.

---

## Limites actuelles

| Limite | État |
|---|---|
| Starters embarqués dans Forge uniquement | Pas de marketplace ni de chargement externe |
| Pas de mise à jour automatique | Supprimez et rebuilder pour mettre à jour |
| `--force` écrase sans protection SHA256 | Contrairement aux modules, pas de vérification de modification |
| Pas de MariaDB réelle dans les tests E2E | `apply_model_sql` est moquée |
| Pas de Forge Design pour les starters | Forge Design est un projet séparé |
| Pas de suppression (`starter:remove`) | Un starter installé ne se désinstalle pas automatiquement |

---

## Exemple minimal complet

### 1. Créer la structure

```text
forge_cli/starters/data/
└── mon-starter/
    ├── starter.json
    └── produit.json
```

### 2. Écrire `starter.json`

```json
{
  "id": "mon-starter",
  "number": 6,
  "name": "Mon starter",
  "entity": "Produit",
  "aliases": ["6", "produit", "mon-starter"],
  "description": "Starter 6 — CRUD simple de produits",
  "status": "available",
  "requires_db": true,
  "home_route": "/produits",
  "routes_marker": "mon-starter",
  "routes": {
    "prefix": "/produits",
    "actions": [
      {"method": "GET",  "path": "",             "action": "index",   "name": "produit_index"},
      {"method": "GET",  "path": "/new",         "action": "new",     "name": "produit_new"},
      {"method": "POST", "path": "",             "action": "create",  "name": "produit_create"},
      {"method": "GET",  "path": "/{id}",        "action": "show",    "name": "produit_show"},
      {"method": "GET",  "path": "/{id}/edit",   "action": "edit",    "name": "produit_edit"},
      {"method": "POST", "path": "/{id}",        "action": "update",  "name": "produit_update"},
      {"method": "POST", "path": "/{id}/delete", "action": "destroy", "name": "produit_destroy"}
    ]
  },
  "check_paths": [
    "mvc/entities/produit",
    "mvc/controllers/produit_controller.py"
  ]
}
```

### 3. Écrire `produit.json`

```json
{
  "entity": "Produit",
  "table": "produits",
  "primary_key": "id",
  "fields": [
    {"name": "id",          "type": "INT",         "nullable": false, "auto_increment": true},
    {"name": "nom",         "type": "VARCHAR(100)", "nullable": false},
    {"name": "description", "type": "TEXT",         "nullable": true},
    {"name": "prix",        "type": "DECIMAL(10,2)","nullable": true}
  ],
  "constraints": []
}
```

### 4. Vérifier le starter

```bash
forge starter:list
forge starter:build mon-starter --dry-run
```

### 5. Tester dans un projet réel

```bash
forge new test_produits
cd test_produits
source .venv/bin/activate
forge starter:build mon-starter
forge project:check
forge project:audit
```

---

## Voir aussi

- [API et CLI](reference.md) — liste complète des commandes `forge starter:*`
- [Créer un module](module-author-guide.md) — brique réutilisable installable dans un projet existant
- [Vue d'ensemble des starters](starters/index.md) — starters officiels Forge
- [Application complète](app-complete-tutorial.md) — exemple de build manuel
- [Relations entre entités](relations.md) — format `relations.json`
