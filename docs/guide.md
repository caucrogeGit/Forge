# Forge — Guide de démarrage

## Sommaire

1. [Introduction](#introduction)
2. [Prérequis et installation](#prerequis-installation)
3. [Structure du projet](#structure-projet)
4. [Configuration](#configuration)
5. [Cycle de vie d'une requête](#cycle-vie-requete)
6. [Routeur](#routeur)
7. [Contrôleurs](#controleurs)
8. [Templates Jinja2](#templates-jinja2)
9. [Modèles et base de données](#modeles-base-donnees)
10. [Validation](#validation)
11. [Sécurité](#securite)
12. [Tests](#tests)
13. [Architecture des entités](#architecture-des-entites)
14. [CLI officielle du modèle](#cli-officielle-du-modele)
15. [CLI historique — cmd/make.py](#cli-cmd-make)
16. [CLI — forge](#cli-forge)
17. [Upload minimal](#upload-minimal)
18. [Cycle CRUD complet — forge make:crud](#cycle-crud-complet-forge-makecrud)

---

<a id="introduction"></a>
## 1. Introduction

**Forge** est un framework web MVC en Python, avec HTTPS natif, SQL explicite, moteur de templates **Jinja2** et couche de sécurité intégrée.

### Philosophie

Forge suit deux règles fondamentales :

**Règle 1 — Ce que le framework fournit (`core/`)**

| Module | Rôle |
|--------|------|
| `core/http/` | Requête, réponse, routeur, helper `html()` |
| `core/application.py` | Pipeline middlewares + dispatch |
| `core/security/` | Sessions, CSRF, hashing, middleware, décorateurs |
| `core/forms/` | Form, Field, cleaned_data, erreurs affichables |
| `core/mvc/` | BaseController, Validator historique, Pagination |
| `core/templating/` | Contrat Renderer + singleton `template_manager` |
| `core/database/` | Pool MariaDB, chargeur SQL |
| `core/uploads/` | Upload local minimal : validation, stockage, suppression |
| `core/forge.py` | Registre de configuration |

**Règle 2 — Ce que l'application implémente (`mvc/`)**

| Composant | Rôle |
|-----------|------|
| `mvc/routes.py` | Déclaration des routes |
| `mvc/controllers/` | Logique métier |
| `mvc/models/` | Requêtes SQL |
| `mvc/forms/` | Formulaires applicatifs |
| `mvc/validators/` | Règles de validation réutilisables |
| `mvc/views/` | Templates HTML / Jinja2 |
| `mvc/helpers/` | Helpers de rendu HTML |

> Le framework ne connaît pas votre schéma de base et ne fournit pas d'ORM.

### Limites assumées

| Forge ne fournit pas | Alternative |
|----------------------|-------------|
| ORM / query builder | SQL paramétré direct + `sql_loader.py` |
| Migrations auto complètes | `cmd/make.py migration` + scripts SQL versionnés |
| Session persistante | Mémoire par défaut — remplaçable dans `session.py` |
| Front build intégré au noyau | Chaîne Node séparée via `package.json` |

---

<a id="prerequis-installation"></a>
## 2. Prérequis et installation

### Prérequis

| Outil | Version minimale | Obligatoire |
|-------|------------------|-------------|
| Python | 3.11 | Oui |
| Git | récent | Oui |
| OpenSSL | disponible dans le terminal | Oui |
| MariaDB | 10.6 | Oui pour utiliser la base de données |
| Node.js | 20 | Optionnel — uniquement si vous recompiliez Tailwind |

### Installation manuelle

#### 1. Installer les prérequis système

```bash
sudo apt update
sudo apt install git python3 python3-venv python3-pip openssl mariadb-server build-essential python3-dev libmariadb-dev pkg-config
```

#### 2. Cloner le projet

```bash
git clone --branch main --depth=1 https://github.com/caucrogeGit/Forge.git NomDuProjet
cd NomDuProjet
```

Remplacez `NomDuProjet` par le nom réel de votre application.

Le clone sur un tag laisse le dépôt en *detached HEAD*. Réinitialisez-le immédiatement :

```bash
rm -rf .git
git init
git add -A
git commit -m "init: NomDuProjet — based on Forge main"
```

> `forge new NomDuProjet` fait ces deux étapes automatiquement et est la voie recommandée.

#### 3. Créer l'environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate       # Windows
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

#### 4. Générer les certificats HTTPS locaux

```bash
openssl req -x509 -newkey rsa:2048 \
  -keyout key.pem \
  -out cert.pem \
  -days 365 \
  -nodes \
  -subj "/CN=localhost"
```

#### 5. Préparer l'environnement

```bash
cp env/example env/dev
```

Éditez ensuite `env/dev` avec vos paramètres MariaDB.

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

SSL_CERTFILE=cert.pem
SSL_KEYFILE=key.pem
```

#### 6. Préparer MariaDB avec Forge

```bash
forge db:init
```

Cette commande utilise `DB_ADMIN_*` pour créer la base `DB_NAME`, créer l'utilisateur `DB_APP_LOGIN` si nécessaire, puis appliquer les droits applicatifs sur `DB_NAME.*`.

Ne lancez `forge db:apply` qu'après génération du modèle. `db:init` prépare l'environnement ; `db:apply` applique les SQL déjà générés.

#### 7. Lancer l'application

```bash
python app.py
```

Ouvrir ensuite **https://localhost:8000**.

### Dépendances

**Runtime** (`requirements.txt`)

```txt
mariadb==1.1.14
python-dotenv==1.2.2
jinja2==3.1.6
```

**Développement** (`requirements-dev.txt`)

```txt
-r requirements.txt
pytest>=8.0
```

Les tests n'ont pas besoin d'une instance MariaDB active, mais ils ont besoin des dépendances Python du runtime.

---

<a id="structure-projet"></a>
## 3. Structure du projet

```text
.
├── app.py                        # Point d'entrée — serveur HTTPS
├── forge.py                      # Point d'entrée CLI du projet (non recommandé comme installation principale à ce stade)
├── config.py                     # Chargement des variables d'environnement
│
├── core/                         # Framework — à modifier seulement si vous travaillez sur Forge lui-même
│   ├── forge.py                  # Registre de configuration du noyau
│   ├── application.py            # Dispatcher : middlewares + routage + gestion des erreurs
│   ├── http/
│   │   ├── request.py            # Requête HTTP
│   │   ├── response.py           # Classe Response
│   │   └── helpers.py            # html() — helper de rendu principal
│   ├── templating/
│   │   ├── contracts.py          # Contrat Renderer
│   │   └── manager.py            # Singleton template_manager
│   ├── database/
│   │   ├── connection.py         # Pool MariaDB
│   │   └── sql_loader.py         # Chargeur SQL par environnement
│   ├── forms/                    # Form, Field, cleaned_data, erreurs
│   ├── mvc/
│   │   ├── controller/
│   │   │   └── base_controller.py
│   │   ├── model/
│   │   │   ├── validator.py
│   │   │   └── exceptions.py
│   │   └── view/
│   │       └── pagination.py
│   └── security/
│       ├── session.py
│       ├── hashing.py
│       ├── middleware.py
│       └── decorators.py
│
├── integrations/
│   └── jinja2/
│       └── renderer.py           # Jinja2Renderer
│
├── mvc/
│   ├── routes.py
│   ├── controllers/
│   ├── forms/
│   ├── models/
│   ├── validators/
│   ├── helpers/
│   │   ├── flash.py
│   │   └── form_errors.py
│   └── views/
│       ├── layouts/
│       ├── landing/              # Landing publique Jinja2
│       ├── auth/
│       ├── errors/
│       └── partials/
│
├── tests/
├── cmd/
│   └── make.py                   # CLI historique
├── static/
├── package.json                  # Chaîne front si Tailwind est utilisé
└── env/
    ├── example
    ├── dev
    └── prod
```

---

<a id="configuration"></a>
## 4. Configuration

### Registre `core.forge`

```python
import core.forge as forge

forge.configure(
    app_name="MonApp",
    app_env="prod",
    views_dir="mvc/views",
    db_host="localhost",
    db_port=3306,
    db_name="ma_base",
    db_user="user",
    db_password="secret",
    db_pool_size=10,
)
```

### Clés disponibles

| Clé | Défaut | Description |
|-----|--------|-------------|
| `app_name` | `"Forge"` | Nom de l'application |
| `app_env` | `"dev"` | Environnement |
| `views_dir` | `"mvc/views"` | Dossier des templates |
| `sql_dir` | `"mvc/models/sql"` | Dossier SQL |
| `db_host` | `"localhost"` | Hôte MariaDB |
| `db_port` | `3306` | Port MariaDB |
| `db_name` | `"forge_db"` | Nom de la base |
| `db_user` | `"root"` | Utilisateur |
| `db_password` | `""` | Mot de passe |
| `db_pool_size` | `5` | Taille du pool |
| `css_visible` | `"block"` | Classe CSS visible (pagination) |
| `css_hidden` | `"hidden"` | Classe CSS masquée (pagination) |

### Fichiers d'environnement

```text
env/
├── example     # Commité : variables requises avec valeurs par défaut
├── dev         # Ignoré par git
└── prod        # Ignoré par git
```

`config.py` charge d'abord `env/example`, puis `env/{APP_ENV}` en surcharge.

---

<a id="cycle-vie-requete"></a>
## 5. Cycle de vie d'une requête

```text
Navigateur HTTPS
    ↓
ThreadingHTTPServer + ssl.SSLContext
    ↓
RequestHandler (GET / POST / PUT / PATCH / DELETE)
    ↓
Request(method, path, headers, params, body, json_body, ip)
    ↓
Application.dispatch(request)
    ├─ route absente → 404
    ├─ route protégée → middlewares
    ├─ méthode unsafe → CSRF automatique sauf csrf=False
    └─ handler
       ↓  exception non gérée → 500 automatique
Contrôleur → Modèle → MariaDB
    ↓
html(template, context) ou BaseController.json(data)
    ↓
Response(status, body, headers)
    ↓
Navigateur
```

### Objet `Request`

| Attribut | Type | Description |
|----------|------|-------------|
| `method` | str | `"GET"`, `"POST"`… |
| `path` | str | `"/clients/42"` |
| `params` | dict | Query string |
| `body` | dict | Formulaire POST |
| `json_body` | dict | Corps JSON |
| `ip` | str | IP du client |
| `route_params` | dict | Paramètres dynamiques injectés par le routeur |

> `BaseController.body(request)` aplatit `request.body` en scalaires.

---

<a id="routeur"></a>
## 6. Routeur

### Déclarer des routes

```python
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.auth_controller import AuthController
from mvc.controllers.client_controller import ClientController
from mvc.controllers.webhook_controller import WebhookController

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET",  "/",       HomeController.index,      name="home")
    pub.add("GET",  "/login",  AuthController.login_form, name="login_form")
    pub.add("POST", "/login",  AuthController.login,      name="login")
    pub.add("POST", "/logout", AuthController.logout,     name="logout")

with router.group("", public=False) as protected:
    protected.add("GET",  "/clients",               ClientController.list,      name="client_list")
    protected.add("GET",  "/clients/nouveau",       ClientController.add_form,  name="client_add_form")
    protected.add("POST", "/clients/nouveau",       ClientController.add,       name="client_add")
    protected.add("GET",  "/clients/{id}",          ClientController.show,      name="client_show")
    protected.add("GET",  "/clients/{id}/modifier", ClientController.edit_form, name="client_edit_form")
    protected.add("POST", "/clients/{id}/modifier", ClientController.edit,      name="client_edit")
    protected.add("POST", "/clients/supprimer",     ClientController.delete,    name="client_delete")

with router.group("/api", public=True, api=True, csrf=False) as api:
    api.add("POST", "/webhook", WebhookController.receive, name="webhook")
```

`POST`, `PUT`, `PATCH` et `DELETE` exigent un token CSRF par défaut, même sur une route publique comme `/login`.
Les webhooks et APIs doivent déclarer l'exemption avec `csrf=False`.

### Patterns supportés

| Pattern | Exemple | Paramètres extraits |
|---------|---------|---------------------|
| `/clients` | `/clients` | `{}` |
| `/clients/{id}` | `/clients/42` | `{"id": "42"}` |
| `/clients/{id}/modifier` | `/clients/42/modifier` | `{"id": "42"}` |

---

<a id="controleurs"></a>
## 7. Contrôleurs

Tout contrôleur hérite de `BaseController`. Les handlers sont généralement des `@staticmethod`.

### Méthodes disponibles

```python
from core.mvc.controller.base_controller import BaseController

# Rendu HTML via Jinja2
response = BaseController.render("clients/index.html", context={"clients": data}, request=request)
response = BaseController.render("errors/404.html", 404, request=request)
response = BaseController.render("landing/index.html", request=request)

# Redirection
response = BaseController.redirect("/clients")
response = BaseController.redirect_with_flash(request, "/clients", "Ajouté avec succès.")
response = BaseController.redirect_to_route("clients_show", id=client_id)

# Erreurs HTTP
response = BaseController.bad_request()
response = BaseController.forbidden()
response = BaseController.not_found()
response = BaseController.validation_error("clients/create.html", context={"form": form}, request=request)
response = BaseController.server_error()

# JSON
response = BaseController.json({"id": 1, "nom": "Dupont"})
response = BaseController.json({"erreur": "non trouvé"}, status=404)

# Body POST (dict plat)
data = BaseController.body(request)

# Body JSON
data = BaseController.json_body(request)

# Token CSRF
token = BaseController.csrf_token(request)

# Utilisateur connecté
user = BaseController.current_user(request)

# Message flash
BaseController.set_flash(request, "Ajouté avec succès.")
BaseController.set_flash(request, "Erreur.", level="error")

# Rendu d'un partial Jinja2 (retourne str)
html_fragment = BaseController.include("partials/alerte.html", {"message": "Stock faible"})

# Formulaire (render + form_context)
response = BaseController.render_form("clients/create.html", request, data)
response = BaseController.render_form("clients/create.html", request, data, 400, errors_html)
```

### Exemple complet : contrôleur CRUD

```python
from core.mvc.controller.base_controller import BaseController
from core.mvc.model.exceptions import DoublonError
from core.mvc.view.pagination import Pagination
from mvc.helpers.flash import render_flash_html
from mvc.forms.client_form import ClientForm
from mvc.models.client_model import (
    count_clients, get_clients_page, get_client_by_id,
    add_client, update_client, delete_client,
)


class ClientController(BaseController):

    REDIRECT = "/clients"
    PAR_PAGE = 10

    @staticmethod
    def list(request):
        pagination = Pagination(request, count_clients(), ClientController.PAR_PAGE)
        return BaseController.render(
            "clients/index.html",
            context={
                "clients": get_clients_page(pagination.limit, pagination.offset),
                "flash": render_flash_html(request),
                **pagination.context,
            },
            request=request,
        )

    @staticmethod
    def show(request):
        client_id = request.route_params.get("id")
        client = get_client_by_id(client_id) if client_id else None
        if not client:
            return BaseController.not_found()
        return BaseController.render("clients/show.html", context={"client": client}, request=request)

    @staticmethod
    def add_form(request):
        return BaseController.render("clients/create.html", context={"form": ClientForm()}, request=request)

    @staticmethod
    def add(request):
        form = ClientForm.from_request(request)
        if not form.is_valid():
            return BaseController.render(
                "clients/create.html",
                400,
                context={"form": form, **form.context},
                request=request,
            )
        try:
            add_client(form.cleaned_data)
        except DoublonError as e:
            form.add_error("nom", f"Ce client « {e} » existe déjà.")
            return BaseController.render(
                "clients/create.html",
                400,
                context={"form": form, **form.context},
                request=request,
            )
        return BaseController.redirect_with_flash(
            request,
            ClientController.REDIRECT,
            "Client ajouté avec succès.",
        )
```

---

<a id="templates-jinja2"></a>
## 8. Templates Jinja2

### Moteur de rendu

Forge utilise **Jinja2** avec autoescape HTML activé sur les fichiers `.html`.

- `{{ variable }}` échappe automatiquement le HTML ;
- `{% if %}`, `{% for %}`, `{% include %}` et `{% extends %}` sont disponibles ;
- `{{ url_for("route_name", id=1) }}` génère une URL depuis une route nommée ;
- pour injecter volontairement du HTML déjà construit, utiliser `|safe`.

### Arborescence recommandée

```text
mvc/views/
├── layouts/
│   └── base.html
├── landing/
│   └── index.html
├── clients/
│   ├── index.html
│   ├── create.html
│   ├── edit.html
│   ├── show.html
│   └── partials/
│       └── fields.html
├── partials/
│   └── flash.html
└── errors/
    ├── 403.html
    ├── 404.html
    ├── 429.html
    └── 500.html
```

### Layout recommandé

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{{ app_name }}</title>
    <link rel="stylesheet" href="/static/tailwind.css">
</head>
<body>
    <nav>
        <a href="/">{{ app_name }}</a>
        <form method="post" action="/logout" style="display:inline">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <button type="submit">Déconnexion</button>
        </form>
    </nav>
    <main>
        {% block contenu %}{% endblock %}
    </main>
</body>
</html>
```

> C'est le modèle recommandé pour un layout Jinja2. Les templates qui l'utilisent déclarent `{% extends "layouts/base.html" %}`.

### Template héritant du layout

```html
{% extends "layouts/base.html" %}
{% block contenu %}

<h1>Clients</h1>

{{ flash | safe }}

<table>
  <thead>
    <tr><th>Nom</th><th>Prénom</th><th>Actions</th></tr>
  </thead>
  <tbody>
    {% for client in clients %}
    <tr>
      <td>{{ client.nom }}</td>
      <td>{{ client.prenom }}</td>
      <td>
        <a href="/clients/{{ client.ClientId }}/modifier">Modifier</a>
        <form method="post" action="/clients/supprimer" style="display:inline">
          <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
          <input type="hidden" name="ClientId" value="{{ client.ClientId }}">
          <button type="submit">Supprimer</button>
        </form>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>

<nav>
  <a href="?page={{ prev_page }}" class="{{ has_prev }}">Précédent</a>
  <span>Page {{ page }} / {{ nb_pages }}</span>
  <a href="?page={{ next_page }}" class="{{ has_next }}">Suivant</a>
</nav>

{% endblock %}
```

### Formulaire

```html
{% extends "layouts/base.html" %}
{% block contenu %}

<h1>Nouveau client</h1>

{{ erreurs | safe }}

<form method="post" action="/clients/nouveau">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  {% include "clients/partials/fields.html" %}
  <button type="submit">Créer</button>
</form>

{% endblock %}
```

```html
<!-- clients/partials/fields.html -->
<div>
  <label>Nom</label>
  <input type="text" name="nom" value="{{ nom }}">
</div>
<div>
  <label>Prénom</label>
  <input type="text" name="prenom" value="{{ prenom }}">
</div>
```

### Template autonome

```html
<!DOCTYPE html>
<html lang="fr">
<head><title>Connexion</title></head>
<body>
    {% if erreur %}
    <p class="text-red-600">{{ erreur }}</p>
    {% endif %}
    <form method="POST" action="/login">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <input type="text" name="login">
        <input type="password" name="password">
        <button type="submit">Se connecter</button>
    </form>
</body>
</html>
```

### Rendu brut avec `raw=True`

`raw=True` sert uniquement à retourner un fichier HTML brut sans traitement Jinja2.

À utiliser pour un fichier autonome contenant du JavaScript, du JSX ou des accolades incompatibles avec Jinja2. La landing officielle Forge n'utilise plus ce mode.

```python
BaseController.render("raw/demo.html", raw=True, request=request)
```

---

<a id="modeles-base-donnees"></a>
## 9. Modèles et base de données

### Helper SQL léger

```python
from core.database import db
from core.database.sql_loader import charger_queries

q = charger_queries("client_queries.py")


class ClientModel:
    @staticmethod
    def list(limit, offset, tx=None):
        return db.fetch_all(q.GET_CLIENTS_PAGE, (limit, offset), tx=tx)

    @staticmethod
    def create(data, tx=None):
        return db.insert(q.CREATE_CLIENT, (data["nom"], data["email"]), tx=tx)
```

Le helper DB exécute du SQL fourni explicitement. Il ne construit pas le SQL et ne connaît pas les entités.

### Chargeur SQL

```python
# mvc/models/sql/dev/client_queries.py
COUNT_CLIENTS = "SELECT COUNT(*) AS total FROM client"

GET_CLIENTS_PAGE = """
    SELECT ClientId, nom, prenom, email
    FROM client ORDER BY nom
    LIMIT ? OFFSET ?
"""

CREATE_CLIENT = """
    INSERT INTO client (Nom, Email)
    VALUES (?, ?)
"""
```

### Transactions explicites

```python
from core.database.transaction import transaction

with transaction() as tx:
    client_id = ClientModel.create(form.cleaned_data, tx=tx)
    ClientGroupeModel.replace_for_client(
        client_id,
        form.cleaned_data["groupe_ids"],
        tx=tx,
    )
```

---

<a id="validation"></a>
## 10. Validation

```python
from core.forms import ChoiceField, Form, RelatedIdsField, StringField


class ClientForm(Form):
    nom = StringField(label="Nom", required=True, max_length=60)
    email = StringField(label="Email", required=True, max_length=120)
    ville_id = ChoiceField(label="Ville", required=False, choices_key="allowed_ville_ids")
    groupe_ids = RelatedIdsField(
        label="Groupes",
        required=False,
        allowed_ids_key="allowed_group_ids",
    )
```

```python
form = ClientForm.from_request(
    request,
    allowed_ville_ids=VilleModel.allowed_ids(),
    allowed_group_ids=GroupeModel.allowed_ids(),
)

if not form.is_valid():
    return BaseController.validation_error(
        "clients/create.html",
        context={"form": form, **form.context},
        request=request,
    )
```

Dans les templates :

```html
<input name="nom" value="{{ form.value('nom') }}">
{% if form.has_error('nom') %}
  <p class="text-red-600">{{ form.error('nom') }}</p>
{% endif %}
```

`RelatedIdsField` prépare une liste d'identifiants liés pour un pivot explicite. Il ne charge pas la base et ne persiste rien.

`core.mvc.model.validator.Validator` reste disponible pour l'ancien style de validation, mais Forge V1.0 recommande `core.forms.Form` pour les formulaires applicatifs.

---

<a id="securite"></a>
## 11. Sécurité

### Sessions

```python
from core.security.session import (
    creer_session, get_session, get_session_id,
    supprimer_session, authentifier_session,
    est_authentifie, get_utilisateur, utilisateur_a_role,
    set_flash, get_flash,
)
```

### CSRF

Le token CSRF est injecté dans le contexte quand `request=request` est passé à `BaseController.render()`.
Forge vérifie automatiquement ce token sur `POST`, `PUT`, `PATCH` et `DELETE`, sauf si la route déclare `csrf=False`.

```html
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
```

```python
pub.add("POST", "/login", AuthController.login, name="login")
api.add("POST", "/api/webhook", WebhookController.receive, csrf=False, api=True)
```

Method override pour les formulaires HTML :

```html
<form method="post" action="/clients/12">
  <input type="hidden" name="_method" value="DELETE">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  <button>Supprimer</button>
</form>
```

Forge traite ce formulaire comme `DELETE /clients/12`, après lecture du body et avant le routage.

### Décorateurs

```python
from core.security.decorators import require_auth, require_role

@staticmethod
@require_auth
def list(request): ...

@staticmethod
@require_auth
@require_role("admin")
def dashboard(request): ...
```

`@require_csrf` existe encore pour du code hérité, mais le chemin officiel Forge V1.0 est la protection automatique portée par les routes.

### Hachage des mots de passe

```python
from core.security.hashing import hacher_mot_de_passe, verifier_mot_de_passe

hash = hacher_mot_de_passe("mon_mot_de_passe")
ok = verifier_mot_de_passe("mot_de_passe_saisi", hash)
```

### Messages flash

```python
from mvc.helpers.flash import render_flash_html

BaseController.set_flash(request, "Client créé avec succès.")
flash_html = render_flash_html(request)
return BaseController.render("clients/index.html", context={"flash": flash_html}, request=request)
```

```html
{{ flash | safe }}
```

---

<a id="tests"></a>
## 12. Tests

### Lancer les tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

### `FakeRequest`

```python
from tests.fake_request import FakeRequest

req = FakeRequest("GET", "/clients")
req = FakeRequest("GET", "/clients", params={"page": "2"})
req = FakeRequest("POST", "/clients", body={"nom": "Dupont", "prenom": "Jean"})
req = FakeRequest("POST", "/api/sync", json_body={"ids": [1, 2, 3]})
req = FakeRequest("GET", "/tableau-de-bord", session_id="abc123")
```

### Exemple de test de contrôleur

```python
import pytest
from unittest.mock import patch
from core.security import session as _s
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer
from mvc.controllers.client_controller import ClientController
from tests.fake_request import FakeRequest
import core.forge as _forge


@pytest.fixture(autouse=True)
def _views(tmp_path):
    (tmp_path / "clients").mkdir()
    (tmp_path / "errors").mkdir()
    (tmp_path / "partials").mkdir()
    (tmp_path / "clients" / "index.html").write_text(
        "{% for c in clients %}{{ c.nom }}{% endfor %}", encoding="utf-8"
    )
    (tmp_path / "errors" / "403.html").write_text("403", encoding="utf-8")
    (tmp_path / "errors" / "404.html").write_text("404", encoding="utf-8")
    (tmp_path / "partials" / "flash.html").write_text("{{ message }}", encoding="utf-8")
    _forge._cfg["views_dir"] = str(tmp_path)
    template_manager.register(Jinja2Renderer(str(tmp_path)))


@patch("mvc.controllers.client_controller.get_clients_page", return_value=[])
@patch("mvc.controllers.client_controller.count_clients", return_value=0)
def test_list_retourne_200(_cc, _gcp):
    sid = _s.creer_session()
    new_sid = _s.authentifier_session(sid, {
        "UtilisateurId": 1, "Login": "admin", "Actif": 1, "roles": []
    })
    req = FakeRequest("GET", "/clients", session_id=new_sid)
    resp = ClientController.list(req)
    assert resp.status == 200
```

---

<a id="architecture-des-entites"></a>
## 13. Architecture des entités

Le modèle d'entités officiel repose sur `mvc/entities/` et sépare strictement :

- la source canonique JSON,
- les projections SQL générées,
- la base Python générée,
- la classe métier manuelle.

Exemple :

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

- `contact.json` : définition canonique locale de l'entité
- `contact.sql` : projection SQL locale régénérable
- `contact_base.py` : base Python générée régénérable
- `contact.py` : classe métier manuelle finale, jamais écrasée si elle existe
- `relations.json` : définition canonique globale des relations
- `relations.sql` : projection SQL globale des relations

Règles importantes :

- `contact.py` n'est jamais régénéré s'il existe
- `__init__.py` n'est jamais régénéré s'il existe
- les clés étrangères inter-entités vivent uniquement dans `relations.sql`
- les SQL locaux d'entité ne contiennent pas de FK inter-entité

Le format auteur peut rester concis.
Tout attribut absent prend sa valeur par défaut. Le JSON auteur ne contient que les écarts au comportement standard.

Par exemple, ce JSON est valide :

```json
{
  "entity": "Contact",
  "fields": [
    {
      "name": "id",
      "sql_type": "INT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "nom",
      "sql_type": "VARCHAR(100)",
      "constraints": {
        "not_empty": true,
        "max_length": 100
      }
    }
  ]
}
```

<a id="cli-officielle-du-modele"></a>
## 14. CLI officielle du modèle

Commandes actuellement disponibles :

Après l'installation editable décrite dans la section installation, les commandes officielles sont :

```bash
forge doctor
forge make:entity Contact
forge make:relation
forge sync:entity Contact
forge sync:relations
forge build:model
forge check:model
forge db:init
forge db:apply
forge routes:list
```

Cycle recommandé :

```bash
forge doctor
forge db:init
forge make:entity Contact
# éditer mvc/entities/contact/contact.json
forge sync:entity Contact
forge make:relation
forge sync:relations
forge build:model --dry-run   # vérifier ce qui sera écrit / préservé
forge build:model
forge db:apply
forge routes:list
```

Comportement des commandes disponibles :

- `forge doctor` : diagnostique l'environnement — Python, configuration, structure MVC, entités, SSL, Node.js et connexion base ; produit un rapport `[OK] / [WARN] / [FAIL] / [SKIP]` ; code de sortie 1 si au moins un FAIL
- `forge make:entity Contact` : lance l'assistant interactif de création d'entité, écrit un JSON auteur court puis génère les fichiers dérivés
- `forge make:entity Contact --no-input` : écrit directement un squelette court minimal pour un usage scriptable
- `forge make:relation` : lance l'assistant interactif de création de relation, écrit `mvc/entities/relations.json`, puis laisse `forge sync:relations` régénérer `mvc/entities/relations.sql`
- `forge sync:entity Contact` : relit `mvc/entities/contact/contact.json` et régénère uniquement `contact.sql` et `contact_base.py`
- `forge sync:relations` : relit `mvc/entities/relations.json` et régénère `mvc/entities/relations.sql` pour les relations `many_to_one` supportées en V1
- `forge build:model` : valide le modèle puis régénère les `*.sql`, les `*_base.py`, les fichiers manuels absents et `relations.sql` ; affiche `[ÉCRIT]`, `[CRÉÉ]`, `[PRÉSERVÉ]` pour chaque fichier et une synthèse finale ; `--dry-run` calcule sans écrire
- `forge check:model` : valide tout le modèle sans écrire de fichier
- `forge db:init` : prépare l'environnement MariaDB du projet avec `DB_ADMIN_*`, crée la base si absente, crée l'utilisateur applicatif s'il est absent, réapplique les privilèges limités à `DB_NAME.*` (`SELECT`, `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `ALTER`, `DROP`, `INDEX`, `REFERENCES`) et demande une vérification manuelle si un utilisateur existant est ambigu ou non vérifiable
- `forge db:apply` : applique les SQL déjà générés dans l'ordre entités puis relations dans une base déjà préparée, via `DB_APP_*`
- `forge routes:list` : affiche les routes déclarées, leur statut public, leur protection CSRF, leur marqueur API et leur handler
- `forge upload:init` : crée `storage/uploads/`, les sous-dossiers `images`, `documents`, `tmp` et leurs `.gitkeep`

Doctrine relationnelle V1 :

- `many_to_one` est le seul type de relation supporté directement
- Forge ne fournit pas de `many_to_many` direct ou implicite
- un `many_to_many` se modélise via une entité pivot explicite avec sa propre clé locale `id`
- cette entité pivot porte des FK explicites comme `contact_id`, `groupe_id`
- le lien est alors décrit par deux relations `many_to_one`

<a id="cli-cmd-make"></a>
## 15. CLI historique — cmd/make.py

Cette CLI existe encore pour compatibilité interne et pour certains anciens scripts.

Elle n'est plus le flux officiel de génération du modèle d'entités. Pour tout nouveau projet, utilisez la commande :

```bash
forge
```

Les anciennes commandes sont conservées, mais ne sont plus documentées comme parcours principal.

---

<a id="cli-forge"></a>
## 16. CLI — forge

La CLI `forge` est l'interface officielle du modèle d'entités.

À ce stade, la méthode conseillée reste l'installation manuelle décrite en section 2.

Puis :

```bash
forge db:init
forge make:entity Contact
forge sync:entity Contact
forge check:model
forge db:apply
forge routes:list
python app.py
```

L'ancien `cmd/make.py` reste disponible pour compatibilité, mais il ne doit pas être confondu avec le flux officiel du modèle d'entités.

---

<a id="upload-minimal"></a>
## 17. Upload minimal

Forge fournit un service local simple pour recevoir un fichier depuis un contrôleur.

Initialisez les dossiers :

```bash
forge upload:init
```

Template HTML (dans une vue Jinja2) :

```html
<form method="post" action="/profil/avatar" enctype="multipart/form-data">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="file" name="avatar" accept="image/jpeg,image/png,image/webp">
    <button type="submit">Envoyer</button>
</form>
```

> `enctype="multipart/form-data"` est obligatoire pour les formulaires avec fichier. Sans cet attribut, le navigateur envoie uniquement le nom du fichier, pas son contenu.

Exemple de contrôleur :

```python
from core.mvc.controller import BaseController
from core.uploads.exceptions import UploadError, UploadTooLargeError
from core.uploads.manager import save_upload


class ProfilController(BaseController):
    @staticmethod
    def store_avatar(request):
        try:
            file = request.files.get("avatar")
            saved_file = save_upload(file, category="images")
        except UploadTooLargeError:
            return BaseController.render("errors/413.html", 413)
        except UploadError:
            return BaseController.bad_request()

        return BaseController.redirect_with_flash(
            request,
            "/profil",
            f"Avatar enregistré : {saved_file.filename}",
        )
```

> **Validation MIME :** si `UPLOAD_ALLOWED_MIME_TYPES` est non vide, tout fichier sans type MIME déclaré est refusé (`UploadInvalidMimeTypeError`). Si la liste est vide, la validation MIME est désactivée et seule l'extension est vérifiée.

Limites assumées :

- stockage local uniquement ;
- pas de miniatures ;
- pas de redimensionnement automatique ;
- pas de médiathèque ;
- pas d'interface d'administration.

---

<a id="cycle-crud-complet-forge-makecrud"></a>
## 18. Cycle CRUD complet — forge make:crud

`forge make:crud` génère le scaffolding CRUD d'une entité en une commande, à partir du JSON canonique.

### Prérequis

L'entité doit être définie et validée avant de lancer le CRUD :

```bash
forge make:entity Contact
forge build:model          # génère contact_base.py et contact.sql
forge db:apply             # crée la table en base
```

### Génération

```bash
forge make:crud Contact --dry-run    # prévisualiser sans écrire
forge make:crud Contact              # générer les fichiers
```

Sortie type :

```
[CRÉÉ]      mvc/controllers/contact_controller.py
[CRÉÉ]      mvc/models/contact_model.py
[CRÉÉ]      mvc/forms/contact_form.py
[CRÉÉ]      mvc/views/layouts/app.html
[CRÉÉ]      mvc/views/contact/index.html
[CRÉÉ]      mvc/views/contact/show.html
[CRÉÉ]      mvc/views/contact/form.html

Routes à ajouter dans mvc/routes.py :
──────────────────────────────────────────────────────────────────────
  from mvc.controllers.contact_controller import ContactController

  with router.group("/contacts") as g:
      g.add("GET",  "",              ContactController.index,   name="contact_index")
      g.add("GET",  "/new",          ContactController.new,     name="contact_new")
      g.add("POST", "",              ContactController.create,  name="contact_create")
      g.add("GET",  "/{id}",         ContactController.show,    name="contact_show")
      g.add("GET",  "/{id}/edit",    ContactController.edit,    name="contact_edit")
      g.add("POST", "/{id}",         ContactController.update,  name="contact_update")
      g.add("POST", "/{id}/delete",  ContactController.destroy, name="contact_destroy")
```

### Ajouter les routes manuellement

Copier le bloc affiché dans `mvc/routes.py` :

```python
from mvc.controllers.contact_controller import ContactController

with router.group("/contacts") as g:
    g.add("GET",  "",              ContactController.index,   name="contact_index")
    g.add("GET",  "/new",         ContactController.new,     name="contact_new")
    g.add("POST", "",             ContactController.create,  name="contact_create")
    g.add("GET",  "/{id}",        ContactController.show,    name="contact_show")
    g.add("GET",  "/{id}/edit",   ContactController.edit,    name="contact_edit")
    g.add("POST", "/{id}",        ContactController.update,  name="contact_update")
    g.add("POST", "/{id}/delete", ContactController.destroy, name="contact_destroy")
```

**Important :** `/new` doit être déclaré avant `/{id}` — le routeur parcourt les routes dans l'ordre ; sinon `new` serait capturé comme un id.

### Lancer l'application

```bash
python app.py
```

Accéder à `https://localhost:8000/contacts`.

### Personnalisation après génération

Les fichiers générés sont les points de départ — ils sont lisibles et à adapter :

- **Contrôleur** : ajouter `@require_auth`, pagination, tri, règles métier.
- **Formulaire** : ajouter des validations croisées via `clean()`, remplacer les `StringField` de type `DATE`.
- **Vues** : adapter le style, ajouter des colonnes, affiner les messages.
- **Layout** `mvc/views/layouts/app.html` : ajouter le nom de l'application, le menu de navigation.

Les fichiers manuels ne sont **jamais** régénérés si vous relancez `forge make:crud` — ils sont protégés (`[PRÉSERVÉ]`).

### Limites V1.0

- Relations entre entités non générées (à câbler manuellement).
- Pas de pagination dans le contrôleur généré.
- `DATE` / `DATETIME` → `StringField` avec avertissement `[WARN]` ; remplacer par un champ adapté.
- Routes injectées manuellement (jamais automatiques).
