# Forge — Framework MVC Python 1.0.0-beta.1

[![PyPI version](https://img.shields.io/pypi/v/forge-mvc.svg)](https://pypi.org/project/forge-mvc/)
[![Python](https://img.shields.io/pypi/pyversions/forge-mvc.svg)](https://pypi.org/project/forge-mvc/)
[![License](https://img.shields.io/badge/license-Forge%20Proprietary-blue.svg)](https://github.com/caucrogeGit/Forge/blob/main/LICENSE)

> **Forge 1.0.0-beta.1 — bêta publique.** Disponible sur [PyPI](https://pypi.org/project/forge-mvc/1.0.0b1/) sous `forge-mvc==1.0.0b1`.
> L'option `--pre` est nécessaire car `1.0.0b1` est une préversion bêta PEP 440.

*Une forge pour les créer toutes. Framework web applicatif.*

Framework web MVC pur Python, HTTPS natif, Jinja2 intégré.  
Forge conserve un runtime Python volontairement limité, avec des dépendances explicites et justifiées : MariaDB, python-dotenv, Jinja2, Pillow, et Argon2.

> Copyright (c) 2026 Roger Cauchon — voir [LICENSE](LICENSE)

---

## Charte et décisions architecturales

Forge suit une [charte philosophique](CHARTE_DOC.md) qui définit ses
principes : explicite, pédagogique, testable, durable. Le noyau reste
minimal, l'écosystème grandit par modules.

Les choix structurants de Forge sont documentés dans [`docs/adr/`](docs/adr/) :

- [ADR-001](docs/adr/001-auth-strategy.md) — stratégie d'authentification Forge 2.x
- [ADR-002](docs/adr/002-session-strategy.md) — stratégie de sessions
- [ADR-003](docs/adr/003-language-convention.md) — API publique en anglais
- [ADR-004](docs/adr/004-core-perimeter.md) — périmètre du `core/` minimal strict
- [ADR-005](docs/adr/005-packaging.md) — packaging hybride monorepo / multi-distributions PyPI
- [ADR-006](docs/adr/006-python-version.md) — Python 3.12+ minimum
- [ADR-007](docs/adr/007-charter-v2-adoption.md) — adoption formelle de la charte v2
- [ADR-008](docs/adr/008-auth-audit-architecture.md) — architecture de l'audit auth

---

## Philosophie : périmètre du framework vs périmètre de l'application

Forge suit une règle stricte de séparation entre ce que le **framework fournit**
et ce que **l'application implémente**.

### Ce que `core/` fournit (framework)

| Outil | Rôle |
|-------|------|
| `core/http/request.py` | Encapsulation de la requête HTTP |
| `core/http/response.py` | Réponse HTTP |
| `core/http/helpers.py` | Helper `html()` — rendu Jinja2 → Response |
| `core/http/router.py` | Routage statique/dynamique, groupes, noms |
| `core/application.py` | Pipeline middlewares + dispatch + CSRF auto + 500 auto |
| `core/templating/` | Contrat `Renderer` + singleton `template_manager` |
| `core/security/session.py` | Sessions, CSRF, expiration |
| `core/security/hashing.py` | Hachage Argon2id ; vérification legacy PBKDF2 conservée pour compatibilité — création PBKDF2 supprimée |
| `core/security/middleware.py` | `AuthMiddleware`, `CsrfMiddleware` |
| `core/security/decorators.py` | `@require_auth`, `@require_csrf`, `@require_role` |
| `core/forms/` | `Form`, `Field`, `cleaned_data`, erreurs affichables |
| `core/mvc/controller/base_controller.py` | `render`, `redirect`, `json`, `body`, `csrf_token`… |
| `core/mvc/model/validator.py` | Logique de validation seule (sans HTML) |
| `core/mvc/view/pagination.py` | Calcul de pagination |
| `core/forge.py` | Registre de configuration du noyau |

### Modules officiels disponibles

Forge sépare le noyau minimal des fonctionnalités spécialisées.
Les modules suivants sont distribués en **mode source-only** via GitHub
(publication PyPI des opt-in prévue dans une version ultérieure) :

| Module | Rôle | Statut |
|--------|------|--------|
| `forge-mvc-mfa` | Authentification multi-facteurs (TOTP, codes de récupération) | Pre-Alpha |
| `forge-mvc-rbac` | RBAC fin (rôles, permissions, décorateurs) | Beta |
| `forge-mvc-workflow` | Cycles de vie applicatifs (statuts, transitions) | Beta |
| `forge-mvc-stats` | Tracking d'événements génériques | Beta |

Installation depuis le monorepo (voir [installation-github.md](docs/installation-github.md)) :

```bash
python -m pip install -e .                   # core
python -m pip install -r requirements-dev.txt  # opt-in + outils dev
```

Voir [ADR-004](docs/adr/004-core-perimeter.md) pour la justification de cette séparation.

### Ce que `mvc/` implémente (application)

| Composant | Rôle |
|-----------|------|
| `mvc/routes.py` | Déclaration des routes de **votre** application |
| `mvc/controllers/` | Contrôleurs métier |
| `mvc/models/` | Requêtes SQL de **votre** base de données |
| `mvc/forms/` | Formulaires applicatifs |
| `mvc/validators/` | Règles de validation de **vos** entités |
| `mvc/helpers/form_errors.py` | Rendu HTML des erreurs |
| `mvc/helpers/flash.py` | Rendu HTML des messages flash |
| `mvc/views/` | Tous les templates Jinja2, y compris login et layout |

### Architecture des entités

Le modèle d'entités officiel repose sur `mvc/entities/`.

```text
mvc/
└── entities/
    ├── relations.json
    ├── relations.sql
    └── contact/
        ├── __init__.py
        ├── contact.json
        ├── contact.sql
        ├── contact_base.py
        └── contact.py
```

Rôle des fichiers :

- `contact.json` : source canonique locale de l'entité
- `contact.sql` : projection SQL locale régénérable
- `contact_base.py` : base Python générée régénérable
- `contact.py` : classe métier manuelle finale
- `relations.json` : source canonique globale des relations
- `relations.sql` : projection SQL globale des relations

### Règle d'or

> Le framework ne connaît pas votre schéma de base, ne sait pas qui s'appelle
> `login` ou `password`, et n'impose aucune route par défaut.
> `AuthController`, les vues de connexion et les routes `/login`/`/logout` sont
> du code **applicatif** fourni à titre d'exemple dans `mvc/` — vous pouvez les
> modifier ou les supprimer librement.

### Cap CRUD explicite

Forge vise un CRUD applicatif complet, explicite et lisible, sans ORM implicite :
formulaires, validation, CSRF automatique, messages flash, redirections,
erreurs de formulaire et modèles applicatifs SQL structurés.

Doctrine associée :

- Forge ne génère pas de repository magique.
- Forge ne cache pas le SQL.
- Forge fournit une structure stable pour organiser le CRUD.
- Le développeur reste propriétaire du modèle applicatif.

---

## Prérequis

| Outil | Version minimale |
|-------|-----------------|
| Python | 3.12 ou supérieur ; 3.12.x recommandé pour développer Forge |
| MariaDB | 10.6 |
| OpenSSL | disponible dans le terminal |
| Node.js | 20, optionnel — uniquement pour recompiler Tailwind CSS |

## CSS officiel

Tailwind est le framework CSS officiel de Forge pour les templates générés.
Forge ne maintient pas plusieurs variantes Bootstrap, Bulma, Foundation ou
autres frameworks CSS.

Le workflow front standard est :

```bash
npm install
npm run build:css
```

Le fichier source est `static/src/input.css`. Le fichier compilé servi par
l'application est `static/tailwind.css`.

Node.js/npm est utile pour recompiler le CSS, mais il n'est pas nécessaire pour
exécuter le serveur Python Forge quand `static/tailwind.css` existe déjà.

Un développeur peut remplacer Tailwind manuellement dans son application, hors
chemin standard généré par Forge. Voir `docs/front.md`.

---

## Installation depuis GitHub

Le core `forge-mvc` est disponible sur [PyPI](https://pypi.org/project/forge-mvc/) — voir [Installation avec pipx](docs/installation-pipx.md).
L'installation depuis GitHub est recommandée pour contribuer ou travailler directement sur les sources.

### 1. Installer les prérequis système

Sous Linux Ubuntu / Zorin :

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip openssl mariadb-server build-essential python3-dev libmariadb-dev pkg-config
```

### 2. Cloner Forge

```bash
git clone --branch v1.0.0-beta.1 --depth=1 https://github.com/caucrogeGit/Forge.git NomDuProjet
cd NomDuProjet
```

Remplacez `NomDuProjet` par le nom de votre application. Un profil peut être précisé avec `--profile` (`minimal`, `standard`, `dynamic`, `multilingual`) — `standard` est le profil par défaut. Voir [docs/profiles.md](docs/profiles.md).

### 3. Réinitialiser l'historique Git pour votre application

```bash
rm -rf .git
git init
git add -A
git commit -m "init: NomDuProjet — based on Forge 1.0.0-beta.1"
```

### 4. Créer l’environnement virtuel du projet

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Préparer l’environnement

```bash
cp env/example env/dev
```

Puis éditez `env/dev` avec vos paramètres MariaDB.

### 6. Générer les certificats HTTPS locaux

```bash
openssl req -x509 -newkey rsa:2048 \
  -keyout key.pem \
  -out cert.pem \
  -days 365 \
  -nodes \
  -subj "/CN=localhost"
```

### 7. Initialiser la base et lancer l’application

```bash
forge db:init
python app.py
```

Puis ouvrir dans le navigateur :

```text
https://localhost:8000
```

---

## Installation pour contribuer au framework

Pour contribuer au développement de Forge ou tester une branche précise :

### 1. Prérequis système

Sous Linux Ubuntu / Zorin :

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip openssl mariadb-server build-essential python3-dev libmariadb-dev pkg-config
```

### 2. Cloner le dépôt Forge

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge
```

### 3. Créer l’environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
pip install -r requirements.txt
```

> La commande `forge` locale n'est disponible qu'après installation du package en mode editable.
> Sans `pip install -e .`, la commande `forge` du projet ne sera pas trouvée.

### 4. Générer les certificats HTTPS locaux

```bash
openssl req -x509 -newkey rsa:2048 \
  -keyout key.pem \
  -out cert.pem \
  -days 365 \
  -nodes \
  -subj "/CN=localhost"
```

### 5. Préparer l’environnement

```bash
cp env/example env/dev
```

Puis éditez `env/dev` avec vos paramètres MariaDB.

Exemple :

```env
APP_NAME=Forge
APP_ROUTES_MODULE=mvc.routes

# Administration MariaDB globale
DB_ADMIN_HOST=localhost
DB_ADMIN_PORT=3306
DB_ADMIN_LOGIN=root
DB_ADMIN_PWD=

# Base projet
DB_NAME=contacts
DB_CHARSET=utf8mb4
DB_COLLATION=utf8mb4_unicode_ci

# Utilisateur applicatif du projet
DB_APP_HOST=localhost
DB_APP_PORT=3306
DB_APP_LOGIN=forge
DB_APP_PWD=motdepassefort
DB_POOL_SIZE=5

APP_HOST=127.0.0.1
APP_PORT=8000
APP_SSL_ENABLED=true
# Dev : HTTPS local. Prod derrière Nginx : APP_SSL_ENABLED=false.

SSL_CERTFILE=cert.pem
SSL_KEYFILE=key.pem
```

### 6. Préparer l'environnement MariaDB du projet

Le flux recommandé est désormais :

```bash
forge db:init
```

Cette commande utilise `DB_ADMIN_*` pour préparer `DB_NAME`, créer `DB_APP_LOGIN` si nécessaire et attribuer les droits sur la base du projet.
Elle prépare aussi la table technique `forge_migrations`, utilisée par les
migrations SQL versionnées.

Contrat de la commande :

- si la base existe déjà, `forge db:init` ne tombe pas en erreur et signale simplement qu’elle est déjà présente
- si l’utilisateur applicatif existe déjà, `forge db:init` ne le recrée pas et ne modifie pas silencieusement son mot de passe
- les privilèges sur la base projet sont appliqués ou réappliqués à chaque exécution
- si la situation de l’utilisateur existant est ambiguë ou non vérifiable, `forge db:init` demande une vérification manuelle au lieu de “réparer” silencieusement

Politique de privilèges par défaut sur `DB_NAME.*` :

- `SELECT`
- `INSERT`
- `UPDATE`
- `DELETE`
- `CREATE`
- `ALTER`
- `DROP`
- `INDEX`
- `REFERENCES`

Forge n’accorde pas de privilèges globaux serveur à l’utilisateur applicatif et n’utilise pas `ALL PRIVILEGES` par défaut si cette liste explicite suffit.

> **Développement vs production**
>
> En développement, `forge db:init` conserve un flux pédagogique simple : le compte `DB_APP_LOGIN` reçoit aussi les droits nécessaires à `forge db:apply` (`CREATE`, `ALTER`, `DROP`, `INDEX`, `REFERENCES`). C'est pratique en développement et pour les starters.
>
> En production, privilégiez une séparation stricte : un compte d'administration ou de migration pour `forge db:init` / `forge db:apply`, et un compte applicatif runtime limité à `SELECT`, `INSERT`, `UPDATE`, `DELETE`.
>
> Cette séparation sera formalisée dans une évolution ultérieure sans changer la doctrine JSON/SQL actuelle.

Les migrations SQL versionnées vivent dans `mvc/migrations/`. Le flux complet
est documenté dans `docs/migrations.md` :

```bash
forge migration:make initial_schema --from-entities
forge migration:status
forge migration:apply
```

### 7. Lancer l’application

```bash
python app.py
```

Puis ouvrir dans le navigateur :

```text
https://localhost:8000
```

### 8. Fin de l’outillage historique

> **`cmd/` n'est plus disponible.** Utiliser exclusivement la CLI officielle `forge`.

La méthode recommandée pour créer un projet depuis les sources est décrite dans [Installation depuis GitHub](#installation-depuis-github).
L’installation pour contribuer au framework est décrite dans [Installation pour contribuer](#installation-pour-contribuer-au-framework).

Les commandes historiques de génération de schéma et d’initialisation de sécurité
sont désormais remplacées par `forge db:init`.

---

## Modèle d'entités — CLI officielle

```bash
forge doctor
forge make:entity Contact
forge sync:entity Contact
forge sync:relations
forge build:model
forge check:model
forge db:init
forge upload:init
forge media:init
forge mail:init
forge db:apply
forge routes:list
```

Cycle recommandé :

1. `forge doctor` pour vérifier l’environnement avant de démarrer
2. `forge make:entity Contact`
3. édition de `mvc/entities/contact/contact.json`
4. `forge sync:entity Contact`
5. `forge check:model`
6. `forge build:model`
7. `forge db:init`
8. `forge upload:init` si votre application reçoit des fichiers
9. `forge media:init` si votre application utilise le socle média et les variantes d’images
10. `forge mail:init` si votre application envoie des mails
11. `forge db:apply`
12. `forge routes:list` pour vérifier le routage déclaré

L'outillage historique a été supprimé. La CLI officielle est `forge`.

---

## Structure du projet

```text
.
├── app.py                        # Point d'entrée — serveur HTTPS, routeur
├── forge.py                      # Point d’entrée CLI officiel
├── config.py                     # Chargement des variables d'environnement
│
├── core/                         # Framework — ne pas modifier
│   ├── application.py            # Dispatcher : middlewares + routage + 500 automatique
│   ├── forge.py                  # Registre de configuration du noyau
│   ├── http/
│   │   ├── request.py            # Requête HTTP (form, JSON, params, ip)
│   │   ├── response.py           # Réponse HTTP
│   │   └── helpers.py            # html() — rendu Jinja2 → Response
│   ├── templating/
│   │   ├── contracts.py          # Protocole Renderer (swappable)
│   │   └── manager.py            # Singleton template_manager
│   ├── database/
│   │   ├── connection.py         # Pool de connexions MariaDB thread-safe
│   │   └── sql_loader.py         # Chargement des requêtes selon APP_ENV
│   ├── forms/                    # Form, Field, cleaned_data, erreurs
│   ├── mvc/
│   │   ├── controller/
│   │   │   └── base_controller.py  # render, redirect, json, body, flash, CSRF…
│   │   ├── model/
│   │   │   ├── validator.py      # Validation de formulaires (logique seule)
│   │   │   └── exceptions.py
│   │   └── view/
│   │       └── pagination.py
│   └── security/
│       ├── session.py            # Sessions, CSRF, expiration
│       ├── hashing.py            # PBKDF2-HMAC-SHA256 + rate limiting (legacy)
│       ├── middleware.py         # AuthMiddleware, CsrfMiddleware
│       └── decorators.py         # @require_auth, @require_csrf, @require_role
│
├── integrations/
│   └── jinja2/
│       └── renderer.py           # Jinja2Renderer (autoescape HTML)
│
├── mvc/                          # Application — périmètre utilisateur
│   ├── routes.py                 # Table de routage URL → contrôleur
│   ├── controllers/
│   ├── entities/                 # Modèle canonique des entités
│   ├── forms/
│   ├── models/
│   │   └── sql/dev/              # Requêtes SQL ignorées par git
│   ├── validators/
│   ├── helpers/
│   │   ├── form_errors.py        # render_errors_html
│   │   └── flash.py              # render_flash_html
│   └── views/
│       ├── layouts/base.html     # Gabarit commun ({% block contenu %})
│       ├── home/index.html       # Page d'accueil publique
│       ├── auth/login.html
│       ├── errors/               # 403, 404, 429, 500
│       └── partials/flash.html
│
├── tests/                        # Suite de tests pytest
│   ├── conftest.py               # Fixtures : configure_forge_kernel, fake_request…
│   ├── fake_request.py           # FakeRequest — requête simulée pour tests contrôleurs
│   ├── test_application.py       # dispatch(), exceptions, pipeline middleware
│   ├── test_hashing.py
│   ├── test_json.py              # BaseController.json(), json_body, FakeRequest
│   ├── test_middleware.py
│   ├── test_response.py
│   ├── test_router.py
│   ├── test_session.py
│   ├── test_templating.py        # TemplateManager, Jinja2Renderer, html(), vues réelles
│   └── test_validator.py
│
├── static/
│   ├── favicon.svg
│   ├── img/                      # Logos et images
│   ├── tailwind.css              # CSS compilé ignoré par git
│   └── src/input.css             # Source Tailwind
│
└── env/                          # Variables d'environnement
    ├── example                   # Squelette commité
    ├── dev                       # Valeurs de développement ignorées par git
    └── prod                      # Valeurs de production ignorées par git
```

---

## Flux d'une requête

```text
Navigateur
    ↓  HTTPS
ThreadingHTTPServer + ssl.SSLContext
    ↓
RequestHandler (GET / POST / PUT / PATCH / DELETE)
    ↓  encapsulation
Request (method, path, headers, params, body, json_body, ip)
    ↓
Application.dispatch()
    ├─ route absente → 404
    ├─ route protégée → pipeline middlewares
    ├─ méthode unsafe → CSRF automatique sauf csrf=False
    └─ handler
       ↓  exception non gérée → 500 automatique
Contrôleur → Modèle → MariaDB
    ↓
html(template, context) ou BaseController.json(data) → Response
    ↓
Navigateur
```

---

## Application (`core/application.py`)

`Application` orchestre le routage et les middlewares.

```python
# Usage minimal — AuthMiddleware par défaut
app = Application(router)

# Middlewares personnalisés
app = Application(router, middlewares=[AuthMiddleware("/login"), MonMiddleware()])

# Login URL personnalisée
app = Application(router, login_url="/connexion")
```

Un middleware est un objet exposant `check(request) → Response | None`.  
Le premier middleware qui retourne une `Response` court-circuite la chaîne.

Les middlewares ne s'appliquent qu'aux routes protégées (`public=False`).

La protection CSRF s'applique aux méthodes unsafe (`POST`, `PUT`, `PATCH`, `DELETE`)
par défaut, y compris sur les routes publiques comme `/login`.

Les API et webhooks doivent demander l'exemption explicitement avec `csrf=False`.

Toute exception non gérée dans un contrôleur est interceptée par `dispatch()`
et produit automatiquement une réponse `errors/500.html`.

---

## CRUD explicite

Organisation recommandée :

```text
mvc/
├── forms/
│   └── contact_form.py
├── models/
│   ├── contact_model.py
│   └── sql/dev/contact_queries.py
└── views/contacts/
    ├── index.html
    ├── create.html
    ├── edit.html
    └── show.html
```

Le contrôleur orchestre.  
Le formulaire valide.  
Le modèle applicatif SQL appelle des requêtes visibles dans `*_queries.py`.

Aucun repository généré, aucun SQL caché.

```python
form = ContactForm.from_request(request)
if not form.is_valid():
    return BaseController.validation_error(
        "contacts/create.html",
        context={"form": form, **form.context},
        request=request,
    )

contact_id = ContactModel.create(form.cleaned_data)

return BaseController.redirect_to_route(
    "contacts_show",
    id=contact_id,
    request=request,
    flash="Contact créé.",
)
```

Pour un pivot explicite simple, `RelatedIdsField` prépare seulement la sélection :

```python
class ContactForm(Form):
    nom = StringField(required=True)
    groupe_ids = RelatedIdsField(required=False, allowed_ids_key="allowed_group_ids")


form = ContactForm.from_request(
    request,
    allowed_group_ids=GroupeModel.allowed_ids(),
)
```

Le formulaire ne persiste rien.  
Le modèle applicatif SQL reste responsable de la table pivot.

Pour une écriture multiple :

```python
from core.database.transaction import transaction

with transaction() as tx:
    contact_id = ContactModel.create(form.cleaned_data, tx=tx)
    ContactGroupeModel.replace_for_contact(
        contact_id,
        form.cleaned_data["groupe_ids"],
        tx=tx,
    )
```

Dans un template :

```html
<a href="{{ url_for('contacts_show', id=contact.Id) }}">Voir</a>
<input name="nom" value="{{ form.value('nom') }}">
```

---

## Réponses JSON (`BaseController`)

```python
# Retourner du JSON depuis un contrôleur
return BaseController.json({"id": 1, "nom": "Dupont"})
return BaseController.json({"erreur": "non trouvé"}, status=404)

# Lire un body JSON (POST/PUT/PATCH/DELETE application/json)
data = BaseController.json_body(request)  # → dict
```

`Request.json_body` est peuplé automatiquement si le `Content-Type` de la
requête est `application/json`.

`Request.body` reste le dictionnaire formulaire habituel pour `POST`, `PUT`,
`PATCH` et `DELETE`.

---

## Moteur de templates Jinja2

Forge utilise Jinja2 avec autoescape HTML activé sur tous les fichiers `.html`.

```python
# Initialisation au démarrage dans app.py
from integrations.jinja2.renderer import Jinja2Renderer
from core.templating.manager import template_manager

template_manager.register(Jinja2Renderer(forge.get("views_dir")))
```

```python
# Dans un contrôleur
return BaseController.render(
    "contacts/index.html",
    context={"contacts": contacts},
    request=request,
)
```

```html
<!-- Template Jinja2 -->
{% extends "layouts/base.html" %}

{% block contenu %}
{% for contact in contacts %}
  <p>{{ contact.nom }}</p>
{% endfor %}
{% endblock %}
```

Les variables sont échappées automatiquement contre le XSS.

Utilisez `{{ variable | safe }}` uniquement pour du HTML pré-rendu contrôlé
comme les messages flash ou les erreurs de formulaire.

---

## Ce que Forge n'est pas

Forge est un framework intentionnellement minimal. Ces limites sont des choix,
non des dettes techniques.

| Forge ne fournit pas | Alternative si besoin |
|----------------------|-----------------------|
| ORM ou query builder | Requêtes SQL paramétrées directes |
| Ancien outillage CLI | supprimé — utiliser `forge` exclusivement |
| Backend de session persistant | Sessions en mémoire — remplacez `_sessions` dans `session.py` |
| Routing avancé | Le routeur actuel couvre les besoins CRUD courants |
| Gestion des rôles intégrée | `@require_role` + table `utilisateur_role` dans les applications ou starters |
| Support multi-base | Un connecteur MariaDB — ajoutez le vôtre si besoin |
| Rechargement automatique | Lancez avec `watchdog` ou un process manager |
| Système de plugins | Architecture directe — étendez sans couche d'abstraction inutile |

---

## Tests

```bash
pip install -e .
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

Les tests ne nécessitent **pas** MariaDB installé : l'import du driver est
paresseux (`core/database/connection.py`) et les modèles DB sont mockés dans les
tests applicatifs.

### Validation complète (avant commit)

```bash
python -m compileall -q .
mkdocs build --strict
git diff --check
python -m pytest -x -q
```

### FakeRequest

Pour tester un contrôleur sans démarrer le serveur :

```python
from tests.fake_request import FakeRequest

req = FakeRequest("GET", "/clients")
req = FakeRequest("POST", "/clients", body={"Nom": "Dupont"})
req = FakeRequest("POST", "/api/sync", json_body={"ids": [1, 2]})
req = FakeRequest("GET", "/tableau-de-bord", session_id="abc123")
```

---

## Sécurité

### Sessions mémoire

Forge stocke les sessions en mémoire dans le processus Python.

Ce choix est adapté au développement, à la pédagogie et aux petites applications mono-processus. **En production, Forge doit tourner en mono-processus derrière Nginx** tant qu'aucun backend de session partagé n'est configuré.

Limites connues :

- les sessions sont perdues au redémarrage ;
- elles ne sont pas partagées entre plusieurs workers ou plusieurs machines ;
- ce stockage n'est pas adapté au scaling horizontal ;
- Gunicorn/uWSGI multi-worker n'est pas supporté sans backend partagé.

Forge fournit `FileSessionStore` et `MariaDbSessionStore` pour les déploiements
multi-processus — voir `core/sessions/` et [ADR-002 — Stratégie de session](docs/adr/002-session-strategy.md).

| Mesure | Détail |
|--------|--------|
| HTTPS dev | `ssl.SSLContext` — TLS 1.2 minimum imposé explicitement. En production, TLS est terminé par Nginx. |
| Authentification | Cookie `HttpOnly; Secure; SameSite=Strict` + vérification en base |
| CSRF | Token par session, vérifié sur `POST`, `PUT`, `PATCH`, `DELETE` sauf `csrf=False` explicite |
| XSS | Autoescape Jinja2 sur tous les templates `.html` |
| Mots de passe | Argon2id (`core.auth`) pour les nouveaux projets ; PBKDF2-HMAC-SHA256 600 000 itérations en legacy |
| Timing attacks | `hmac.compare_digest()` |
| Session fixation | Nouveau `session_id` après chaque connexion |
| Rate limiting | 5 tentatives / 60 s par IP sur `/login` |
| Headers HTTP | CSP, HSTS, X-Frame-Options, X-Content-Type-Options |
| Path traversal | `os.path.realpath()` sur les fichiers statiques |
| Injection SQL | Requêtes paramétrées exclusivement |

Versions supportées et procédure de signalement : [SECURITY.md](SECURITY.md)

---

## Dépendances

**Runtime** (`requirements.txt`)

| Package | Rôle |
|---------|------|
| `mariadb` | Connecteur MariaDB natif |
| `python-dotenv` | Chargement des fichiers `env/*` |
| `jinja2` | Moteur de templates avec autoescape HTML |
| `Pillow` | Traitement image et génération des variantes médias |
| `argon2-cffi` | Hachage sécurisé des mots de passe (Argon2id) |

Les modules opt-in (`forge-mvc-mfa`, `-rbac`, `-workflow`, `-stats`) nécessitent des dépendances
supplémentaires non installées avec `forge-mvc`. `forge-mvc-mfa` (Pre-Alpha) n'est pas publié sur
PyPI en `1.0` — ses dépendances (dont `pyotp`) ne font pas partie du runtime core.

**Développement** (`requirements-dev.txt`)

| Package | Rôle |
|---------|------|
| `pytest` | Suite de tests |
| `build` | Packaging wheel |
| `twine` | Publication PyPI |
| `mkdocs` | Génération de la documentation |
| `mkdocs-material` | Thème Material pour MkDocs |
| `pymdown-extensions` | Extensions Markdown pour MkDocs |

---

## Feuille de route

### Landing page

La landing page actuelle est une solution transitoire.

Elle fonctionne et remplit son rôle comme page d'accueil publique par défaut de Forge.

Elle est servie comme template Jinja2 et repose sur les assets locaux du projet.

Elle n'utilise plus React UMD, Babel standalone ni dépendance CDN pour son rendu.

La source canonique de la landing est :

```text
mvc/views/landing/index.html
```

La page d'accueil MkDocs `docs/index.html` est générée depuis cette source :

```bash
forge sync:landing
forge sync:landing --check
```

Ne modifiez pas `docs/index.html` à la main.

---

## Licence

Forge est distribué sous licence propriétaire / source disponible.

L'usage professionnel, commercial ou institutionnel n'est pas autorisé sans
accord écrit préalable de Roger Cauchon.

Les usages autorisés sans accord écrit sont limités à la lecture, l'étude,
l'évaluation personnelle et l'usage éducatif non commercial.

Voir [LICENSE](LICENSE) pour les conditions complètes.
