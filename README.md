# Forge — Framework MVC Python 1.0.0

Framework web MVC pur Python, HTTPS natif, Jinja2 intégré.
Runtime léger : trois dépendances Python explicites — MariaDB, python-dotenv et Jinja2.

> Copyright (c) 2026 Roger Cauchon — voir [LICENSE](LICENSE)

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
| `core/security/hashing.py` | PBKDF2-HMAC-SHA256 + rate limiting |
| `core/security/middleware.py` | `AuthMiddleware`, `CsrfMiddleware` |
| `core/security/decorators.py` | `@require_auth`, `@require_csrf`, `@require_role` |
| `core/forms/` | `Form`, `Field`, `cleaned_data`, erreurs affichables |
| `core/mvc/controller/base_controller.py` | `render`, `redirect`, `json`, `body`, `csrf_token`… |
| `core/mvc/model/validator.py` | Logique de validation seule (sans HTML) |
| `core/mvc/view/pagination.py` | Calcul de pagination |
| `core/forge.py` | Registre de configuration du noyau |

### Ce que `mvc/` implémente (application)

| Composant | Rôle |
|-----------|------|
| `mvc/routes.py` | Déclaration des routes de **votre** application |
| `mvc/controllers/` | Contrôleurs métier (y compris auth) |
| `mvc/models/` | Requêtes SQL de **votre** base de données |
| `mvc/forms/` | Formulaires applicatifs |
| `mvc/validators/` | Règles de validation de **vos** entités |
| `mvc/helpers/form_errors.py` | Rendu HTML des erreurs (CSS choisi par vous) |
| `mvc/helpers/flash.py` | Rendu HTML des messages flash (CSS choisi par vous) |
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

Forge vise un CRUD applicatif complet, explicite et lisible, sans ORM implicite : formulaires, validation, CSRF automatique, messages flash, redirections, erreurs de formulaire et modèles applicatifs SQL structurés.

Doctrine associée :

- Forge ne génère pas de repository magique.
- Forge ne cache pas le SQL.
- Forge fournit une structure stable pour organiser le CRUD.
- Le développeur reste propriétaire du modèle applicatif.

---

## Prérequis

| Outil | Version minimale |
|-------|-----------------|
| Python | 3.11 |
| MariaDB | 10.6 |
| OpenSSL | disponible dans le terminal |
| Node.js | 20 (optionnel — uniquement pour recompiler Tailwind CSS) |

---

## Installation manuelle

### 1. Prérequis système

Sous Linux Ubuntu / Zorin :

```bash
sudo apt update
sudo apt install git python3 python3-venv python3-pip openssl mariadb-server build-essential python3-dev libmariadb-dev pkg-config
```

### 2. Cloner le projet

```bash
git clone --branch v1.0.0 --depth=1 https://github.com/caucrogeGit/Forge.git NomDuProjet
cd NomDuProjet
```

Remplacez `NomDuProjet` par le nom de votre application.

Le clone sur un tag laisse le dépôt en *detached HEAD*. Réinitialisez-le immédiatement pour démarrer votre propre historique :

```bash
rm -rf .git
git init
git add -A
git commit -m "init: NomDuProjet — based on Forge v1.0.0"
```

> `forge new NomDuProjet` fait ces deux étapes automatiquement et est la voie recommandée.

### 3. Créer l’environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

> La commande `forge` n'est disponible qu'après installation du package en mode editable.
> Sans `pip install -e .`, la commande `forge` ne sera pas trouvée.

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

### 7. Lancer l’application

```bash
python app.py
```

Puis ouvrir dans le navigateur :

```text
https://localhost:8000
```

### 8. Bootstrap historique optionnel

Si vous utilisez encore le bootstrap historique de schéma et de sécurité, les commandes suivantes existent toujours :

```bash
python cmd/make.py schema:create
python cmd/make.py security:init --env dev
```

Elles restent techniques, internes et hors flux officiel du modèle d'entités.

> La CLI d’installation `forge-mvc` est encore en cours de stabilisation. L’installation manuelle ci-dessus reste la méthode recommandée pour créer un projet.

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
forge db:apply
forge routes:list
```

Cycle recommandé :

1. `forge doctor` pour vérifier l'environnement avant de démarrer
2. `forge make:entity Contact`
3. édition de `mvc/entities/contact/contact.json`
4. `forge sync:entity Contact`
5. `forge check:model`
6. `forge build:model`
7. `forge db:init`
8. `forge upload:init` si votre application reçoit des fichiers
9. `forge db:apply`
10. `forge routes:list` pour vérifier le routage déclaré

L'ancien outillage `cmd/make.py` existe toujours, mais reste hors flux officiel pour le modèle d'entités.

---

## Structure du projet

```
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
│       ├── hashing.py            # PBKDF2-HMAC-SHA256 + rate limiting
│       ├── middleware.py         # AuthMiddleware, CsrfMiddleware
│       └── decorators.py        # @require_auth, @require_csrf, @require_role
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
│   │   └── sql/dev/              # Requêtes SQL (ignoré par git)
│   ├── validators/
│   ├── helpers/
│   │   ├── form_errors.py        # render_errors_html (rendu HTML des erreurs)
│   │   └── flash.py              # render_flash_html (messages flash CSS)
│   └── views/
│       ├── layouts/base.html     # Gabarit commun ({% block contenu %})
│       ├── home/index.html       # Page d'accueil publique
│       ├── auth/login.html
│       ├── errors/               # 403, 404, 429, 500
│       └── partials/flash.html
│
├── tests/                        # Suite de tests (pytest)
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
├── cmd/                          # Outillage CLI historique
│   ├── make.py                   # Point d'entrée : python cmd/make.py <commande>
│   ├── mvc/                      # Générateurs MVC
│   ├── sql/                      # Générateurs SQL
│   ├── inspect/                  # Diagnostic
│   └── security/                 # Initialisation sécurité
│
├── static/
│   ├── favicon.svg
│   ├── img/                      # Logos et images (png, svg, ico…)
│   ├── tailwind.css              # CSS compilé (ignoré par git)
│   └── src/input.css             # Source Tailwind
│
└── env/                          # Variables d'environnement
    ├── example                   # Squelette (commité)
    ├── dev                       # Valeurs de développement (ignoré par git)
    └── prod                      # Valeurs de production (ignoré par git)
```

---

## Flux d'une requête

```
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

## Application (core/application.py)

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
par défaut, y compris sur les routes publiques comme `/login`. Les API et webhooks
doivent demander l'exemption explicitement avec `csrf=False`.

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

Le contrôleur orchestre. Le formulaire valide. Le modèle applicatif SQL appelle
des requêtes visibles dans `*_queries.py`. Aucun repository généré, aucun SQL caché.

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

Le formulaire ne persiste rien. Le modèle applicatif SQL reste responsable de la table pivot.

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

## Réponses JSON (BaseController)

```python
# Retourner du JSON depuis un contrôleur
return BaseController.json({"id": 1, "nom": "Dupont"})
return BaseController.json({"erreur": "non trouvé"}, status=404)

# Lire un body JSON (POST/PUT/PATCH/DELETE application/json)
data = BaseController.json_body(request)  # → dict
```

`Request.json_body` est peuplé automatiquement si le `Content-Type` de la
requête est `application/json`. `Request.body` reste le dict formulaire habituel
pour `POST`, `PUT`, `PATCH` et `DELETE`.

---

## Moteur de templates (Jinja2)

Forge utilise Jinja2 avec autoescape HTML activé sur tous les fichiers `.html`.

```python
# Initialisation au démarrage (app.py)
from integrations.jinja2.renderer import Jinja2Renderer
from core.templating.manager import template_manager

template_manager.register(Jinja2Renderer(forge.get("views_dir")))
```

```python
# Dans un contrôleur
return BaseController.render("contacts/index.html", context={"contacts": contacts}, request=request)
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
Utilisez `{{ variable | safe }}` uniquement pour du HTML pré-rendu (flash, erreurs).

---

## Ce que Forge n'est pas

Forge est un framework intentionnellement minimal. Ces limites sont des choix,
non des dettes techniques.

| Forge ne fournit pas | Alternative si besoin |
|----------------------|-----------------------|
| ORM ou query builder | Requêtes SQL paramétrées directes (cf. `sql_loader.py`) |
| Ancien outillage CLI | `cmd/make.py` existe encore, mais reste hors flux officiel pour les entités |
| Backend de session persistant | Sessions en mémoire — remplacez `_sessions` dans `session.py` |
| Routing avancé (regex, contraintes) | Le routeur actuel couvre 95 % des besoins CRUD |
| Gestion des rôles intégrée | `@require_role` + table `utilisateur_role` (starter app) |
| Support multi-base | Un connecteur MariaDB — ajoutez le vôtre si besoin |
| Rechargement automatique | Lancez avec `watchdog` ou un process manager |
| Système de plugins | Architecture directe — étendez sans couche d'abstraction |

---

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

Les tests ne nécessitent **pas** MariaDB installé : l'import du driver est
paresseux (`core/database/connection.py`) et tous les modèles DB sont mockés
dans les tests applicatifs.

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

| Mesure | Détail |
|--------|--------|
| HTTPS | `ssl.SSLContext` sur `ThreadingHTTPServer` |
| Authentification | Cookie `HttpOnly; Secure; SameSite=Strict` + vérification en base |
| CSRF | Token par session, vérifié sur `POST`, `PUT`, `PATCH`, `DELETE` sauf `csrf=False` explicite |
| XSS | Autoescape Jinja2 sur tous les templates `.html` |
| Mots de passe | PBKDF2-HMAC-SHA256, 260 000 itérations, sel aléatoire |
| Timing attacks | `hmac.compare_digest()` |
| Session fixation | Nouveau `session_id` après chaque connexion |
| Rate limiting | 5 tentatives / 60 s par IP sur `/login` |
| Headers HTTP | CSP, HSTS, X-Frame-Options, X-Content-Type-Options |
| Path traversal | `os.path.realpath()` sur les fichiers statiques |
| Injection SQL | Requêtes paramétrées exclusivement |

---

## Dépendances

**Runtime** (`requirements.txt`)

| Package | Rôle |
|---------|------|
| `mariadb` | Connecteur MariaDB natif |
| `python-dotenv` | Chargement des fichiers `env/*` |
| `jinja2` | Moteur de templates avec autoescape HTML |

**Développement** (`requirements-dev.txt`)

| Package | Rôle |
|---------|------|
| `pytest` | Suite de tests |

---

## Feuille de route

### Landing page

La landing page actuelle est une solution transitoire.
Elle fonctionne et remplit son rôle comme page d'accueil publique par défaut de Forge.

Elle est servie comme template Jinja2 et repose sur les assets locaux du projet.
Elle n'utilise plus React UMD, Babel standalone ni dépendance CDN pour son rendu.

La source canonique de la landing est `mvc/views/landing/index.html`.
La page d'accueil MkDocs `docs/index.html` est générée depuis cette source :

```bash
forge sync:landing
forge sync:landing --check
```

Ne modifiez pas `docs/index.html` à la main.

---

## Licence

Copyright (c) 2026 Roger Cauchon — Tous droits réservés.  
Voir [LICENSE](LICENSE) pour les conditions d'utilisation.
