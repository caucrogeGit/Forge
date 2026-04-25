# Forge — Référence API

Cette référence décrit l'API publique de Forge dans son état actuel.
Les exemples reflètent les conventions réellement supportées dans l'état actuel du projet.

## Sommaire

- [core.forge](#coreforge)
- [core.http.request](#corehttprequest)
- [core.http.response](#corehttpresponse)
- [core.http.helpers](#corehttphelpers)
- [core.http.router](#corehttprouter)
- [core.application](#coreapplication)
- [core.templating.manager](#coretemplatingmanager)
- [integrations.jinja2.renderer](#integrationsjinja2renderer)
- [core.security.session](#coresecuritysession)
- [core.security.hashing](#coresecurityhashing)
- [core.security.middleware](#coresecuritymiddleware)
- [core.security.decorators](#coresecuritydecorators)
- [core.forms](#coreforms)
- [core.uploads](#coreuploads)
- [core.mvc.controller.base_controller](#coremvccontrollerbase_controller)
- [core.mvc.model.validator](#coremvcmodelvalidator)
- [core.mvc.model.exceptions](#coremvcmodelexceptions)
- [core.mvc.view.pagination](#coremvcviewpagination)
- [core.database.db](#coredatabasedb)
- [core.database.transaction](#coredatabasetransaction)
- [core.database.connection](#coredatabaseconnection)
- [core.database.sql_loader](#coredatabasesql_loader)
- [mvc.helpers.flash](#mvchelpersflash)
- [mvc.helpers.form_errors](#mvchelpersform_errors)
- [forge CLI](#forge-cli)

---

## `core.forge`

Registre centralisé de configuration du noyau. Tous les modules `core/` lisent
leurs paramètres via ce registre, jamais via `config.py` directement.

### `configure(**kwargs) -> None`

Configure le noyau Forge. À appeler une seule fois au démarrage.

```python
import core.forge as forge

forge.configure(
    app_name="MonApp",
    app_env="prod",
    db_host="db.exemple.com",
    db_name="ma_base",
    db_user="user",
    db_password="secret",
    css_visible="flex",
    css_hidden="hidden",
)
```

**Raises :** `KeyError` si une clé est inconnue.

Les chemins relatifs (`views_dir`, `sql_dir`) sont résolus en chemins absolus
depuis la racine du projet.

### `get(key: str) -> object`

Retourne une valeur de configuration.

```python
from core.forge import get as _cfg

views_dir = _cfg("views_dir")
app_env = _cfg("app_env")
```

**Raises :** `KeyError` si la clé est inconnue.

**Clés disponibles :**

| Clé | Défaut | Description |
|-----|--------|-------------|
| `app_name` | `"Forge"` | Nom de l'application |
| `app_env` | `"dev"` | Environnement |
| `views_dir` | `"{racine}/mvc/views"` | Dossier des templates |
| `sql_dir` | `"{racine}/mvc/models/sql"` | Dossier des requêtes SQL applicatives |
| `upload_root` | `"{racine}/storage/uploads"` | Racine des fichiers uploadés |
| `upload_max_size` | `5242880` | Taille maximale d'un fichier uploadé |
| `upload_allowed_extensions` | `["jpg", "jpeg", "png", "webp", "pdf"]` | Extensions autorisées |
| `upload_allowed_mime_types` | `["image/jpeg", "image/png", "image/webp", "application/pdf"]` | Types MIME autorisés |
| `db_host` | `"localhost"` | Host MariaDB |
| `db_port` | `3306` | Port MariaDB |
| `db_name` | `"forge_db"` | Nom de la base |
| `db_user` | `"root"` | Utilisateur |
| `db_password` | `""` | Mot de passe |
| `db_pool_size` | `5` | Taille du pool |
| `css_visible` | `"block"` | Classe CSS visible (pagination) |
| `css_hidden` | `"hidden"` | Classe CSS masquée (pagination) |
| `router` | `None` | Routeur actif pour `url_for` et `redirect_to_route` |

---

**Note :** `mvc/models/sql/...` correspond aux requêtes applicatives chargées par le runtime. Ce n'est pas la source canonique du modèle. La source canonique des entités vit sous `mvc/entities/`.

---

## `core.http.request`

### Classe `Request`

Encapsule une requête HTTP entrante. Instanciée automatiquement par le serveur.

**Attributs :**

| Attribut | Type | Description |
|----------|------|-------------|
| `method` | `str` | Verbe HTTP : `"GET"`, `"POST"`… |
| `path` | `str` | Chemin : `"/clients/42"` |
| `headers` | `HTTPMessage` | En-têtes HTTP |
| `params` | `dict[str, list[str]]` | Query string parsée |
| `body` | `dict[str, list[str]]` | Formulaire `POST`, `PUT`, `PATCH` ou `DELETE` parsé |
| `files` | `dict[str, UploadedFile]` | Fichiers reçus en `multipart/form-data` |
| `json_body` | `dict` | Corps JSON |
| `ip` | `str` | Adresse IP client |
| `route_params` | `dict[str, str]` | Paramètres dynamiques injectés par le routeur |

**Notes :**
- `params` et `body` suivent le format `parse_qs` : les valeurs sont des listes.
- Utilisez `BaseController.body(request)` pour obtenir un dict plat.
- `json_body` est vide si le `Content-Type` n'est pas `application/json`.
- `files` est rempli uniquement pour `multipart/form-data`.
- `GET`, `HEAD` et `OPTIONS` n'ont pas de body parsé.
- Le body formulaire classique est limité à 1 Mo. Les requêtes multipart utilisent la limite upload configurée.
- `original_method` conserve la méthode reçue.
- `POST` avec `_method=PUT`, `_method=PATCH` ou `_method=DELETE` est traité comme la méthode indiquée avant le routage et le CSRF effectif.

Exemple method override :

```html
<form method="post" action="/contacts/12">
    <input type="hidden" name="_method" value="DELETE">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <button>Supprimer</button>
</form>
```

---

## `core.http.response`

### Classe `Response`

```python
Response(status=200, body=b"", content_type="text/html; charset=utf-8", headers=None)
```

**Attributs :**

| Attribut | Type | Description |
|----------|------|-------------|
| `status` | `int` | Code HTTP |
| `body` | `bytes` | Contenu (str auto-converti en UTF-8) |
| `content_type` | `str` | Type MIME |
| `headers` | `dict` | En-têtes supplémentaires |

```python
Response(302, headers={"Location": "/clients"})
Response(200, "<h1>OK</h1>")
Response(200, b"\x89PNG...", "image/png")
```

---

## `core.http.helpers`

### `html(template, status=200, context=None, *, raw=False) -> Response`

Rend un template et retourne une `Response`.

```python
from core.http.helpers import html

response = html("contacts/index.html", context={"contacts": contacts})
response = html("contacts/create.html", 422, context=data)
response = html("errors/404.html", 404)
response = html("raw/demo.html", raw=True)
```

**Paramètres :**

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `template` | `str` | — | Chemin relatif depuis `views_dir` |
| `status` | `int` | `200` | Code HTTP de la réponse |
| `context` | `dict \| None` | `None` | Variables injectées dans le template |
| `raw` | `bool` | `False` | Si `True`, retourne le fichier tel quel sans passer par Jinja2 |

**Note :** `raw=True` n'est pas une variante de templating Jinja2. C'est un bypass utile
pour les fichiers contenant du CSS, du JavaScript ou du JSX avec accolades.  
Un rendu `raw=True` ne bénéficie pas de l’injection de contexte Jinja2.

---

## `core.http.router`

### Classe `Router`

```python
from core.http.router import Router

router = Router()
```

### `add(method, pattern, handler, *, name=None, public=False, csrf=True, api=False) -> Router`

Enregistre une route.

```python
router.add("GET", "/clients", ClientController.list)
router.add("POST", "/clients", ClientController.add, name="client_add")
router.add("GET", "/clients/{id}", ClientController.show, name="client_show")
router.add(["GET", "HEAD"], "/ping", ping_handler)
router.add("POST", "/api/webhook", WebhookController.receive, csrf=False, api=True)
```

**Raises :** `ValueError` si le nom est déjà utilisé.

### `group(prefix, *, public=False, csrf=True, api=False) -> RouteGroup`

Crée un groupe de routes partageant un préfixe.

```python
with router.group("", public=True) as pub:
    pub.add("GET", "/", HomeController.index, name="home")
    pub.add("GET", "/login", AuthController.login_form, name="login_form")
    pub.add("POST", "/login", AuthController.login, name="login")

with router.group("/api", public=False) as api:
    api.add("GET", "/clients", ClientController.list)
    api.add("POST", "/clients", ClientController.add)

with router.group("/api", public=True, csrf=False, api=True) as api:
    api.add("POST", "/webhook", WebhookController.receive)
```

Les routes unsafe (`POST`, `PUT`, `PATCH`, `DELETE`) sont protégées par CSRF par défaut.
Une API ou un webhook doit demander l'exemption avec `csrf=False`, jamais par convention implicite.

### `match(method, path) -> tuple | None`

Trouve la première route correspondante et retourne l'objet route avec ses paramètres.

```python
entry, params = router.match("POST", "/clients")
entry.pattern
entry.public
entry.csrf
entry.api
entry.requires_csrf("POST")
```

### `resolve(method, path) -> tuple | None`

Trouve la première route correspondante.

```python
router.resolve("GET", "/clients/42")
# (ClientController.show, {"id": "42"})

router.resolve("GET", "/inconnu")
# None
```

### `is_public(path, method=None) -> bool`

Retourne `True` si le chemin correspond à une route publique.

```python
router.is_public("/")
router.is_public("/login")
router.is_public("/clients")
```

### `iter_routes() -> list[RouteEntry]`

Retourne les routes dans l'ordre de déclaration. Utilisé par `forge routes:list`.

### `url_for(name, **params) -> str`

Génère l'URL d'une route nommée.

```python
router.url_for("home")
router.url_for("client_show", id=42)
router.url_for("client_edit", id="42")
```

**Raises :**
- `KeyError` si le nom de route est inconnu
- `KeyError` si un paramètre requis est manquant

**Patterns supportés :**

| Pattern | URL testée | Paramètres |
|---------|-----------|------------|
| `/clients` | `/clients` | `{}` |
| `/clients/{id}` | `/clients/42` | `{"id": "42"}` |
| `/clients/{id}/modifier` | `/clients/42/modifier` | `{"id": "42"}` |
| `/api/{version}/clients/{id}` | `/api/v2/clients/5` | `{"version": "v2", "id": "5"}` |

---

## `core.application`

### Classe `Application`

```python
from core.application import Application

app = Application(router)
app = Application(router, middlewares=[AuthMiddleware("/login")])
app = Application(router, middlewares=[])
```

### `dispatch(request) -> Response`

Point d'entrée principal. Appelé par le serveur pour chaque requête.

**Flux :**
1. Résout la route et injecte `route_params`
2. Si aucune route n'est trouvée, retourne `errors/404.html`
3. Si la route est protégée, exécute les middlewares dans l'ordre
4. Si la route unsafe exige CSRF, vérifie le token
5. Appelle le handler
6. Toute exception non gérée retourne `errors/500.html`

### Interface middleware

Un middleware expose `check(request) -> Response | None`.

```python
class MonMiddleware:
    def check(self, request):
        if not condition_remplie(request):
            return Response(403, "Interdit")
        return None
```

---

## `core.templating.manager`

### Classe `TemplateManager`

Gestionnaire singleton du renderer de templates.

```python
from core.templating.manager import template_manager
```

`template_manager` est l'instance singleton à utiliser.  
En usage applicatif normal, utilisez toujours ce singleton. Ne pas instancier
`TemplateManager` manuellement sauf en test.

### `register(renderer) -> None`

Enregistre le renderer actif.

```python
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer
import core.forge as forge

forge.configure(...)
template_manager.register(Jinja2Renderer(forge.get("views_dir")))
```

L'appel à `register()` remplace le renderer précédent.

### `render(template, context) -> str`

Rend un template et retourne le HTML sous forme de chaîne.

```python
html = template_manager.render("partials/flash.html", {
    "message": "Enregistré.",
    "classes": "bg-green-100 border-green-400 text-green-800",
})
```

**Raises :** `RuntimeError` si aucun renderer n'a été enregistré.

---

## `integrations.jinja2.renderer`

### Classe `Jinja2Renderer`

Renderer Jinja2 avec autoescape HTML activé sur les fichiers `.html`.

```python
from integrations.jinja2.renderer import Jinja2Renderer

renderer = Jinja2Renderer("/chemin/absolu/mvc/views")
html = renderer.render("contacts/index.html", {"contacts": contacts})
```

### Initialisation

```python
Jinja2Renderer(views_dir: str)
```

- `views_dir` : chemin absolu vers le dossier racine des templates
- autoescape activé sur les fichiers `.html`
- partials via `{% include "chemin/relatif.html" %}`
- héritage de layout via `{% extends "layouts/base.html" %}`
- helper global `url_for()` branché sur le routeur actif

```html
<a href="{{ url_for('contacts_show', id=contact.Id) }}">Voir</a>
```

### Autoescape et `| safe`

| Cas | Syntaxe | Comportement |
|-----|---------|--------------|
| Valeur utilisateur | `{{ nom }}` | Échappée |
| HTML pré-rendu | `{{ flash | safe }}` | Injecté tel quel |
| Bloc de layout | `{% block contenu %}{% endblock %}` | Héritage |

---

## `core.security.session`

### `creer_session() -> str`

Crée une nouvelle session anonyme. Retourne le `session_id`.

```python
from core.security.session import creer_session

sid = creer_session()
```

### `get_session(session_id) -> dict | None`

Retourne les données de la session ou `None`.

```python
session = get_session(sid)
if session:
    csrf = session["csrf_token"]
```

### `supprimer_session(session_id) -> None`

Supprime immédiatement la session.

### `authentifier_session(session_id, utilisateur) -> str | None`

Marque la session comme authentifiée et effectue une rotation du `session_id`.

```python
nouveau_sid = authentifier_session(sid, {
    "UtilisateurId": 1,
    "Login": "admin",
    "Prenom": "Jean",
    "Nom": "Dupont",
    "Email": "jean@exemple.com",
    "Actif": 1,
    "roles": ["admin"],
})
```

### `get_session_id(request) -> str | None`

Extrait le `session_id` depuis le cookie de la requête.

### `est_authentifie(request) -> bool`

Retourne `True` si l'utilisateur est authentifié et repousse l'expiration.

### `get_utilisateur(request) -> dict | None`

Retourne le profil de l'utilisateur connecté.

### `utilisateur_a_role(request, role) -> bool`

Retourne `True` si l'utilisateur possède le rôle demandé.

### `set_flash(session_id, message, level="success") -> None`

Stocke un message flash.

```python
set_flash(get_session_id(request), "Enregistré.", "success")
set_flash(get_session_id(request), "Erreur.", "error")
```

### `get_flash(session_id) -> dict | None`

Récupère puis supprime le message flash.

```python
flash = get_flash(sid)
```

**Structure d'une session :**

```python
{
    "authentifie": bool,
    "utilisateur": dict | None,
    "csrf_token": str,
    "expire_a": float,
    "flash": dict,
}
```

**Durée de session :** 1 heure, renouvelée à chaque appel réussi à `est_authentifie()`.

---

## `core.security.hashing`

### `hacher_mot_de_passe(mot_de_passe) -> str`

Retourne un hash sécurisé au format `"sel:hash"`.

```python
hash = hacher_mot_de_passe("mon_secret")
```

### `verifier_mot_de_passe(mot_de_passe, hash_stocke) -> bool`

Compare un mot de passe avec son hash stocké.

```python
ok = verifier_mot_de_passe("saisie_utilisateur", hash_en_base)
```

### `enregistrer_tentative(ip) -> None`

Enregistre une tentative de connexion échouée pour cette IP.

### `est_limite(ip) -> bool`

Retourne `True` si l'IP a atteint la limite de tentatives.

```python
if est_limite(request.ip):
    from core.http.helpers import html
    return html("errors/429.html", 429)
```

**Spécifications :**
- PBKDF2-HMAC-SHA256
- 260 000 itérations
- sel aléatoire de 16 octets
- comparaison via `hmac.compare_digest()`
- fenêtre de rate limiting de 60 secondes

---

## `core.security.middleware`

### Classe `AuthMiddleware`

```python
from core.security.middleware import AuthMiddleware

middleware = AuthMiddleware(login_url="/login")
```

### `check(request) -> Response | None`

Retourne une redirection 302 vers `login_url` si non authentifié, `None` sinon.

### Classe `CsrfMiddleware`

```python
from core.security.middleware import CsrfMiddleware

middleware = CsrfMiddleware()
```

Vérifie le token CSRF d'une requête unsafe déjà déclarée comme protégée par le routeur.
En usage normal, `Application` l'utilise automatiquement.

### `check(request) -> Response | None`

Retourne `errors/403.html` si le token est absent ou invalide, `None` sinon.

---

## `core.security.decorators`

### `@require_auth`

Redirige vers `/login` si non authentifié.

```python
@staticmethod
@require_auth
def list(request): ...
```

### `@require_csrf`

Retourne 403 si le token CSRF du formulaire ne correspond pas à la session.
Depuis Forge V1.0, la protection officielle passe par les métadonnées de route et `Application`.
Le décorateur reste disponible pour du code hérité ou des appels directs.

```python
@staticmethod
@require_auth
@require_csrf
def add(request): ...
```

### `@require_role(role)`

Redirige vers `/login` si non authentifié. Retourne 403 si le rôle est absent.

```python
@staticmethod
@require_auth
@require_role("admin")
def dashboard(request): ...
```

---

## `core.forms`

Mécanique générique des formulaires Forge. Les formulaires applicatifs vivent dans `mvc/forms/`.

### Classe `Form`

```python
from core.forms import Form, StringField, IntegerField


class ContactForm(Form):
    nom = StringField(label="Nom", required=True, max_length=80)
    age = IntegerField(label="Age", required=False, min_value=0)
```

### `Form.from_request(request, **options) -> Form`

Construit un formulaire depuis `request.body`. Les `options` servent à fournir
explicitement des listes ou paramètres de validation au formulaire.

```python
form = ContactForm.from_request(request)
form = ContactForm.from_request(request, allowed_group_ids={1, 3, 5})
```

### `is_valid() -> bool`

Nettoie les données, remplit `cleaned_data` et expose les erreurs.

```python
if form.is_valid():
    ContactModel.create(form.cleaned_data)
else:
    return BaseController.render(
        "contacts/create.html",
        400,
        context={"form": form, **form.context},
        request=request,
    )
```

### Helpers de rendu

```python
form.value("nom")
form.error("nom")
form.has_error("nom")
```

Ces helpers servent à réafficher les anciennes valeurs et erreurs dans les templates.
Ils ne rendent pas de HTML.

### Attributs

| Attribut | Description |
|----------|-------------|
| `data` | données d'origine aplaties, utiles pour réafficher le formulaire |
| `cleaned_data` | données converties et validées |
| `errors` | erreurs par champ |
| `non_field_errors` | erreurs globales |
| `context` | dict prêt à injecter dans un template |

### Champs disponibles

| Champ | Rôle |
|-------|------|
| `Field` | champ générique |
| `StringField` | chaîne avec `min_length`, `max_length`, `pattern` |
| `IntegerField` | entier avec `min_value`, `max_value` |
| `DecimalField` | nombre décimal |
| `BooleanField` | booléen de formulaire |
| `ChoiceField` | choix explicite fourni au champ ou au formulaire |
| `RelatedIdsField` | liste d'identifiants liés pour pivot explicite |

Un formulaire Forge ne fait pas de SQL, ne crée pas d'objet en base et ne décide pas d'une redirection.

### `ChoiceField`

Valide une valeur parmi une liste de choix fournie explicitement. Le champ ne charge jamais les choix depuis la base.

```python
from core.forms import ChoiceField, Form


class ContactForm(Form):
    ville_id = ChoiceField(required=False, choices_key="allowed_ville_ids")


form = ContactForm.from_request(
    request,
    allowed_ville_ids=VilleModel.allowed_ids(),
)
```

### `RelatedIdsField`

Lit une liste d'identifiants depuis un formulaire HTML, convertit en entiers,
supprime les doublons et valide contre une liste autorisée fournie explicitement.

```python
from core.forms import Form, RelatedIdsField, StringField


class ContactForm(Form):
    nom = StringField(required=True)
    groupe_ids = RelatedIdsField(
        required=False,
        allowed_ids_key="allowed_group_ids",
    )
```

```python
form = ContactForm.from_request(
    request,
    allowed_group_ids=GroupeModel.allowed_ids(),
)
```

`RelatedIdsField` ne charge jamais les identifiants autorisés depuis la base.
Il ne connaît pas le modèle applicatif SQL, ne connaît pas la table pivot et ne persiste rien.

---

## `core.mvc.controller.base_controller`

### Classe `BaseController`

### `render(template, status=200, context=None, *, request=None, raw=False) -> Response`

Génère une réponse HTML. Si `request` est fourni, Forge injecte automatiquement
le `csrf_token` dans le contexte. La mise en page est gérée côté template via Jinja2.

```python
BaseController.render("contacts/index.html", context={"contacts": contacts})
BaseController.render("contacts/index.html", context=ctx, request=request)
BaseController.render("errors/404.html", 404)
BaseController.render("raw/demo.html", raw=True)
```

**Note :** ne comptez pas sur un ancien mécanisme de layout injecté depuis Python.

### `redirect(location, *, request=None, flash=None, level="success") -> Response`

```python
BaseController.redirect("/clients")
BaseController.redirect("/clients", request=request, flash="Client créé.")
```

### `redirect_with_flash(request, location, message, level="success") -> Response`

Flux POST-Redirect-GET : stocke un message flash puis redirige.

```python
BaseController.redirect_with_flash(request, "/clients", "Client créé.")
```

### `redirect_to_route(name, *, request=None, flash=None, level="success", **params) -> Response`

Redirige vers une route nommée.

```python
BaseController.redirect_to_route("contacts_show", id=contact_id)
BaseController.redirect_to_route(
    "contacts_index",
    request=request,
    flash="Contact créé.",
)
```

### `not_found() -> Response`

Retourne `errors/404.html` avec statut 404.

### Erreurs HTTP standardisées

```python
BaseController.bad_request()          # 400
BaseController.forbidden()            # 403
BaseController.not_found()            # 404
BaseController.validation_error()      # 422
BaseController.server_error()         # 500
```

Pour un formulaire invalide :

```python
return BaseController.validation_error(
    "contacts/create.html",
    context={"form": form},
    request=request,
)
```

### `json(data, status=200) -> Response`

```python
BaseController.json({"id": 1, "nom": "Dupont"})
BaseController.json({"erreur": "non trouvé"}, status=404)
```

### `body(request) -> dict`

Retourne le formulaire POST sous forme de dict plat.

```python
data = BaseController.body(request)
```

### `json_body(request) -> dict`

Retourne le corps JSON parsé.

### `csrf_token(request) -> str`

Retourne le token CSRF de la session courante.

### `current_user(request) -> dict | None`

Retourne le profil de l'utilisateur connecté.

### `set_flash(request, message, level="success") -> None`

Stocke un message flash.

### `include(partial, context=None) -> str`

Rend un partial Jinja2 et retourne son HTML.

```python
html = BaseController.include("partials/flash.html", {"message": "OK"})
```

### `render_form(template, request, data, status=200, erreurs="") -> Response`

Raccourci : `render()` + `form_context()`.

```python
BaseController.render_form("contacts/create.html", request, {})
BaseController.render_form("contacts/create.html", request, data, 400, erreurs_html)
```

### `form_context(request, data, erreurs="") -> dict`

Construit le contexte commun à un formulaire.

```python
{
    "nom": "Dupont",
    "prenom": "Jean",
    "csrf_token": "a3f8...",
    "erreurs": "<ul>...</ul>",
}
```

**Note :** les données sont injectées brutes. L'autoescape Jinja2 protège le rendu.
Utilisez `{{ erreurs | safe }}` dans le template uniquement pour cette sortie HTML contrôlée.

---

## `core.mvc.model.validator`

### Classe `Validator`

```python
from core.mvc.model.validator import Validator

class ClientValidator(Validator):
    def __init__(self, data):
        super().__init__()
        self.required(data.get("nom", ""), "Nom")
        self.max_length(data.get("nom", ""), 60, "Nom")
```

### `required(value, label) -> Validator`

Erreur si `value` est vide, `None`, ou ne contient que des espaces.

### `max_length(value, max_len, label) -> Validator`

Erreur si `len(str(value)) > max_len`. Sans effet si `value` est vide.

### `add_error(message) -> Validator`

Ajoute un message d'erreur.

### `is_valid() -> bool`

`True` si aucune erreur enregistrée.

### `errors() -> list[str]`

Retourne une copie de la liste des erreurs.

---

## `core.mvc.model.exceptions`

### `DoublonError(Exception)`

Levée lorsqu'une contrainte d'unicité est violée.

```python
try:
    add_client(data)
except DoublonError as e:
    validator.add_error(f"Ce nom « {e} » existe déjà.")
```

---

## `core.mvc.view.pagination`

### Classe `Pagination`

```python
from core.mvc.view.pagination import Pagination

pagination = Pagination(request, count_clients(), par_page=10)
items = get_clients_page(limit=pagination.limit, offset=pagination.offset)
```

### Attributs

| Attribut | Type | Description |
|----------|------|-------------|
| `page` | `int` | Page courante |
| `nb_pages` | `int` | Nombre total de pages |
| `pages` | `int` | Alias de `nb_pages` |
| `total` | `int` | Nombre total d'éléments |
| `par_page` | `int` | Taille de page |
| `limit` | `int` | Limite SQL recommandée |
| `offset` | `int` | Décalage SQL recommandé |
| `has_previous` | `bool` | Page précédente disponible |
| `has_next` | `bool` | Page suivante disponible |
| `previous_page` | `int | None` | Numéro de page précédente |
| `next_page` | `int | None` | Numéro de page suivante |

### Propriété `context -> dict`

Retourne le dict prêt à injecter dans le template.

```python
{
    "page": 2,
    "nb_pages": 5,
    "prev_page": 1,
    "next_page": 3,
    "has_prev": "block",
    "has_next": "block",
    "limit": 10,
    "offset": 10,
    "pagination": {
        "page": 2,
        "nb_pages": 5,
        "limit": 10,
        "offset": 10,
    },
}
```

Les classes CSS proviennent de `forge.get("css_visible")` et `forge.get("css_hidden")`.

### `to_dict() -> dict`

Retourne un bloc standard sans classes CSS, utile pour les APIs internes ou les contextes modernes.

---

## `core.database.db`

Helper SQL léger. Il exécute uniquement du SQL fourni explicitement par le développeur.

```python
from core.database import db
from mvc.models.sql.dev.contact_queries import CREATE_CONTACT


contact_id = db.insert(CREATE_CONTACT, params)
```

### `fetch_one(sql, params=(), *, tx=None)`

Retourne une ligne avec `cursor(dictionary=True)`.

### `fetch_all(sql, params=(), *, tx=None)`

Retourne toutes les lignes avec `cursor(dictionary=True)`.

### `execute(sql, params=(), *, tx=None)`

Exécute une requête et retourne `rowcount`.

### `insert(sql, params=(), *, tx=None)`

Exécute une insertion et retourne `lastrowid`.

Règles :

- le helper ne construit pas le SQL ;
- il ne connaît pas les entités ;
- il ne fait pas d'ORM ;
- hors transaction, il ouvre, exécute, commit et ferme ;
- dans une transaction, il réutilise `tx` et ne commit jamais lui-même.

---

## `core.database.transaction`

### `transaction()`

Ouvre une transaction explicite.

```python
from core.database.transaction import transaction

with transaction() as tx:
    contact_id = ContactModel.create(data, tx=tx)
    ContactGroupeModel.replace_for_contact(contact_id, groupe_ids, tx=tx)
```

La transaction est visible. Le développeur choisit où elle commence et où elle finit.

---

## `core.database.connection`

### `get_connection() -> mariadb.Connection`

Emprunte une connexion depuis le pool.

```python
from core.database.connection import get_connection, close_connection

conn = None
try:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM client WHERE ClientId = ?", (client_id,))
    return cursor.fetchone()
finally:
    close_connection(conn)
```

**Raises :** `mariadb.PoolError` si le pool est épuisé ou la connexion impossible.

### `close_connection(connection) -> None`

Restitue la connexion au pool. Sans effet si `connection` est `None`.

**Notes :**
- pool initialisé au premier appel
- import `mariadb` paresseux
- configuration lue depuis `forge.get()`

---

## `core.database.sql_loader`

### `charger_queries(nom_fichier) -> module`

Charge un module de requêtes SQL depuis `{sql_dir}/{app_env}/`.

```python
from core.database.sql_loader import charger_queries

q = charger_queries("client_queries.py")
cursor.execute(q.COUNT_CLIENTS)
```

**Raises :** `FileNotFoundError` si le fichier n'existe pas.

---

## `core.uploads`

Service minimal d'upload local. Il valide les fichiers, génère un nom sûr, évite l'écrasement et stocke sous `storage/uploads/<category>/`.

### Configuration

```python
forge.configure(
    upload_root="storage/uploads",
    upload_max_size=5 * 1024 * 1024,
    upload_allowed_extensions=["jpg", "jpeg", "png", "webp", "pdf"],
    upload_allowed_mime_types=[
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
    ],
)
```

### `save_upload(file, category="documents") -> SavedUpload`

Lève `UploadStorageError("Aucun fichier reçu.")` si `file` est `None` (champ absent du formulaire).

**Comportement de la validation MIME :**

| `allowed_mime_types` | MIME reçu | Résultat |
|----------------------|-----------|---------|
| vide `[]` | peu importe | pas de validation MIME |
| non vide | présent et autorisé | accepté |
| non vide | présent et non autorisé | `UploadInvalidMimeTypeError` |
| non vide | absent (`None`) | `UploadInvalidMimeTypeError` |

```python
from core.mvc.controller import BaseController
from core.uploads.exceptions import UploadError, UploadTooLargeError
from core.uploads.manager import save_upload


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
        f"Fichier enregistré : {saved_file.filename}",
    )
```

`SavedUpload` expose :

| Attribut | Description |
|----------|-------------|
| `filename` | Nom sûr généré |
| `original_name` | Nom reçu depuis le navigateur |
| `path` | Chemin complet du fichier enregistré |
| `category` | Sous-dossier utilisé |
| `size` | Taille en octets |
| `mime_type` | Type MIME reçu si disponible |

### `delete_upload(path) -> bool`

Supprime un fichier sous `upload_root`. Retourne `False` si le fichier n'existe pas. Refuse les chemins hors du dossier d'upload.

### `get_upload_path(filename, category="documents") -> Path`

Retourne le chemin attendu pour un fichier d'une catégorie.

### Exceptions

- `UploadError`
- `UploadTooLargeError`
- `UploadInvalidExtensionError`
- `UploadInvalidMimeTypeError`
- `UploadStorageError`

Ces exceptions peuvent être converties en réponse HTTP `400` ou `413` dans un contrôleur.

---

## `mvc.helpers.flash`

### `render_flash_html(request) -> str`

Récupère puis supprime le message flash de la session et retourne son HTML pré-rendu.

```python
from mvc.helpers.flash import render_flash_html

flash = render_flash_html(request)
return BaseController.render("clients/index.html", context={
    "clients": clients,
    "flash": flash,
}, request=request)
```

Dans le template, injecter avec `{{ flash | safe }}`.

Retourne `""` si aucun flash n'est en session.

**Niveaux CSS :**

| Niveau | Classes Tailwind |
|--------|-----------------|
| `success` | `bg-green-100 border-green-400 text-green-800` |
| `error` | `bg-red-100 border-red-400 text-red-800` |
| `warning` | `bg-gray-100 border-gray-300 text-gray-800` |
| `info` | `bg-gray-100 border-gray-300 text-gray-800` |

Partials standards disponibles :

```text
partials/flash.html
partials/form_errors.html
partials/csrf.html
partials/pagination.html
```

---

## `mvc.helpers.form_errors`

### `render_errors_html(errors) -> str`

Convertit une liste d'erreurs en bloc HTML.

```python
from mvc.helpers.form_errors import render_errors_html

html = render_errors_html([
    "Le champ Nom est obligatoire.",
    "Email invalide.",
])
```

Retourne `""` si la liste est vide. Les messages sont échappés via `html.escape()`.

Dans le template, injecter avec `{{ erreurs | safe }}`.

---

## `forge` CLI

La CLI `forge` est l'interface officielle du modèle d'entités et du provisioning MariaDB du projet.

### Workflow minimal

```bash
forge new NomProjet
forge doctor
forge db:init
forge make:entity Contact
forge sync:entity Contact
forge make:relation
forge sync:relations
forge sync:landing --check
forge upload:init
forge check:model
forge build:model --dry-run
forge build:model
forge db:apply
forge make:crud Contact --dry-run
forge make:crud Contact
forge routes:list
forge deploy:init
forge deploy:check
forge starter:list
forge help
```

### Tableau des commandes

| Commande | Rôle | Écrit des fichiers |
|----------|------|--------------------|
| `forge new NomProjet` | Crée un nouveau projet Forge depuis le squelette officiel | Oui, dans le nouveau projet |
| `forge doctor` | Diagnostique l'environnement du projet courant | Non |
| `forge make:entity Entity` | Crée une entité JSON canonique, interactive ou minimale | Oui |
| `forge make:crud Entity` | Génère le squelette CRUD MVC d'une entité | Oui |
| `forge make:crud Entity --dry-run` | Prévisualise le CRUD sans écrire | Non |
| `forge make:relation` | Ajoute une relation globale via assistant interactif | Oui |
| `forge sync:entity Entity` | Régénère SQL et base Python d'une entité | Oui |
| `forge sync:relations` | Régénère `mvc/entities/relations.sql` | Oui |
| `forge sync:landing` | Copie la landing canonique vers `docs/index.html` | Oui |
| `forge sync:landing --check` | Vérifie que `docs/index.html` est synchronisé | Non |
| `forge upload:init` | Initialise les dossiers de stockage upload | Oui |
| `forge build:model` | Valide et régénère tout le modèle | Oui |
| `forge build:model --dry-run` | Valide et prévisualise sans écrire | Non |
| `forge check:model` | Valide le modèle sans écrire | Non |
| `forge db:init` | Prépare la base MariaDB et l'utilisateur applicatif | Oui, côté base de données |
| `forge db:apply` | Applique les SQL générés en base | Oui, côté base de données |
| `forge routes:list` | Liste les routes déclarées | Non |
| `forge deploy:init` | Génère des exemples Nginx, systemd et README de déploiement | Oui |
| `forge deploy:check` | Diagnostique l'environnement de production local | Non |
| `forge starter:list` | Liste les starter apps disponibles | Non |
| `forge help` | Affiche l'aide CLI intégrée | Non |

### `forge new <NomProjet>`

Crée un nouveau projet Forge à partir du squelette officiel.

```bash
forge new GestionVentes
```

- clone le tag `_FORGE_VERSION` du dépôt Forge
- configure `env/dev` avec le nom du projet et le nom de base dérivé
- crée l'environnement virtuel Python et installe les dépendances
- génère les certificats HTTPS locaux via OpenSSL
- réinitialise le dépôt Git avec un commit initial propre

**Prérequis :** `git`, `openssl`, Python 3.11+.
Node.js / npm est optionnel ; un avertissement est émis s'il est absent.

### `forge make:entity <Entity>`

Crée ou initialise une entité sous `mvc/entities/`.

```bash
forge make:entity Contact          # mode interactif
forge make:entity Contact --no-input  # squelette minimal sans prompt
```

`--no-input` écrit directement un JSON auteur minimal, utile en scripting ou CI.

### `forge make:crud <Entity> [--dry-run]`

Génère le scaffolding CRUD complet depuis l'entité JSON canonique.

```bash
forge make:crud Contact              # génère les fichiers
forge make:crud Contact --dry-run    # rapport sans écriture
```

**Fichiers générés ou préservés :**

```
[CRÉÉ]      mvc/controllers/contact_controller.py
[CRÉÉ]      mvc/models/contact_model.py
[CRÉÉ]      mvc/forms/contact_form.py
[CRÉÉ]      mvc/views/layouts/app.html
[CRÉÉ]      mvc/views/contact/index.html
[CRÉÉ]      mvc/views/contact/show.html
[CRÉÉ]      mvc/views/contact/form.html
```

Si un fichier existe déjà : `[PRÉSERVÉ]` — jamais écrasé.

**Bloc de routes affiché sur stdout (à ajouter manuellement dans `mvc/routes.py`) :**

```python
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

**Doctrine :**

- Source : `mvc/entities/contact/contact.json` (entité JSON canonique).
- Requêtes SQL paramétrées avec `?` — jamais d'interpolation directe.
- CSRF injecté automatiquement par `BaseController.render()` sur toutes les vues.
- Le contrôleur génère `_form_data_from_contact()` pour convertir les colonnes SQL (`Nom`) en noms de champs formulaire (`nom`).
- Types SQL non mappés exactement (ex. `DATE`, `DATETIME`) → `[WARN]` sur stdout, champ `StringField` à personnaliser.
- Relations : hors périmètre V1.0 — à ajouter manuellement après génération.
- Layout Jinja2 partagé `mvc/views/layouts/app.html` avec `{% block content %}` — personnalisable librement.

### `forge sync:entity <Entity>`

Relit le JSON canonique de l'entité et régénère le SQL local ainsi que la base Python générée.
Les fichiers manuels (`<entity>.py`) ne sont jamais touchés.

```
[ÉCRIT]     mvc/entities/contact/contact.sql
[ÉCRIT]     mvc/entities/contact/contact_base.py
[PRÉSERVÉ]  mvc/entities/contact/contact.py  ← fichier manuel, non touché
```

### `forge make:relation`

Ajoute une relation globale dans `mvc/entities/relations.json` via l'assistant interactif.

### `forge sync:relations`

Relit `relations.json` et régénère `relations.sql`.

### `forge sync:landing [--check]`

Synchronise la landing applicative canonique vers la page d'accueil MkDocs.

```bash
forge sync:landing          # écrit docs/index.html
forge sync:landing --check  # vérifie sans écrire
```

Source canonique :

```text
mvc/views/landing/index.html
```

Copie générée :

```text
docs/index.html
```

`docs/index.html` contient un commentaire en tête indiquant qu'il est généré et ne doit pas être modifié manuellement.

Sortie attendue en synchronisation :

```text
[ÉCRIT]     docs/index.html
[OK]        Landing synchronisée depuis mvc/views/landing/index.html
```

Sortie attendue en vérification :

```text
[OK]        docs/index.html est synchronisé
```

Si la copie est désynchronisée :

```text
[ERREUR]    docs/index.html est désynchronisé — lancez forge sync:landing
```

### `forge upload:init`

Initialise le stockage local des uploads.

```bash
forge upload:init
```

Crée les dossiers :

```text
storage/uploads/
storage/uploads/images/
storage/uploads/documents/
storage/uploads/tmp/
```

Chaque dossier reçoit un `.gitkeep`. Les fichiers uploadés sont ignorés par Git via `.gitignore`.

### `forge build:model`

Valide et régénère tout le modèle : SQL locaux, bases Python et relations SQL.

```bash
forge build:model             # régénère tous les fichiers
forge build:model --dry-run   # valide + calcule sans écrire
```

Chaque fichier est classé dans l'une des trois catégories :

| Tag | Signification |
|-----|---------------|
| `[ÉCRIT]` | Fichier généré ou régénéré (SQL, `*_base.py`, `relations.sql`) |
| `[CRÉÉ]` | Fichier manuel squelette créé car absent (`<entity>.py`, `__init__.py`) |
| `[PRÉSERVÉ]` | Fichier manuel existant — non touché |

Exemple de sortie :

```
[ÉCRIT]     mvc/entities/contact/contact.sql
[ÉCRIT]     mvc/entities/contact/contact_base.py
[PRÉSERVÉ]  mvc/entities/contact/contact.py
[PRÉSERVÉ]  mvc/entities/contact/__init__.py
[ÉCRIT]     mvc/entities/relations.sql

3 régénéré(s), 0 créé(s), 2 préservé(s).
```

Avec `--dry-run`, aucun fichier n'est écrit et la ligne finale indique :

```
[DRY-RUN] Aucun fichier modifié.
```

### `forge check:model`

Valide le modèle sans écrire de fichier.

### `forge db:init`

Prépare l'environnement MariaDB avec `DB_ADMIN_*` : création de la base, création éventuelle de l'utilisateur applicatif et application des privilèges sur `DB_NAME.*`.

### `forge db:apply`

Applique les SQL générés avec `DB_APP_*`, dans l'ordre : entités puis relations.

### `forge routes:list`

Affiche les routes déclarées par `APP_ROUTES_MODULE`.

Colonnes affichées :

- méthode HTTP ;
- chemin ;
- nom de route ;
- route publique ou protégée ;
- CSRF effectivement requis pour la méthode ;
- marqueur API ;
- handler Python.

### `forge deploy:init`

Génère des fichiers de déploiement indicatifs dans `deploy/`.

```bash
forge deploy:init
```

Fichiers créés si absents :

```text
deploy/nginx/forge-app.conf
deploy/systemd/forge-app.service
deploy/README_DEPLOY.md
```

La commande n'écrase pas les fichiers existants. Elle affiche `[CRÉÉ]` pour un fichier créé et `[PRÉSERVÉ]` pour un fichier déjà présent.

Le modèle généré suit la doctrine actuelle de déploiement :

- Nginx termine HTTPS côté public ;
- Forge écoute en HTTP local en mode `prod` ;
- le service systemd lance `app.py --env prod` ;
- aucune commande système n'est exécutée automatiquement.

### `forge deploy:check`

Vérifie l'environnement de déploiement depuis le projet courant.

```bash
forge deploy:check
```

Checks principaux :

- racine projet Forge détectée ;
- Python disponible ;
- `.venv` présent ;
- `env/prod` présent ;
- variables `DB_APP_HOST`, `DB_NAME`, `DB_APP_LOGIN` présentes ;
- `UPLOAD_ROOT` configuré ;
- `storage/` et `storage/uploads/` présents ;
- modules `mariadb` et `jinja2` importables ;
- fichiers `deploy/` présents si `forge deploy:init` a été lancé ;
- cohérence HTTP local / proxy HTTPS.

La commande quitte avec le code `1` si au moins une erreur bloquante est détectée.

### `forge starter:list`

Affiche la liste des starter apps disponibles.

```bash
forge starter:list
```

Cette commande est informative : elle n'écrit aucun fichier. Les starters restent des parcours documentés et reconstructibles, pas une génération applicative magique.

### `forge doctor`

Diagnostique l'environnement du projet et produit un rapport lisible.

```
Forge doctor — v1.0.0

  [OK  ]  Python — 3.14.4 (≥ 3.11 requis)
  [OK  ]  Configuration — env/dev chargé — clés essentielles présentes
  [OK  ]  Structure MVC — mvc/ valide
  [OK  ]  Entités — 3 entité(s) valide(s)
  [WARN]  Certificats SSL — Absent : cert.pem — relance openssl pour les générer
  [WARN]  Node.js / npm — npm absent — relance npm install && npm run build:css
  [SKIP]  Base de données — env/dev absent — connexion non vérifiable avant configuration

  2 avertissement(s).
```

Statuts possibles :

| Statut | Signification |
|--------|---------------|
| `OK`   | Check passé |
| `WARN` | Anomalie non bloquante — le projet peut démarrer |
| `FAIL` | Problème bloquant — à corriger avant de continuer |
| `SKIP` | Check ignoré faute de contexte suffisant |

Checks effectués dans l'ordre :

| Check | Source | FAIL si | WARN si | SKIP si |
|-------|--------|---------|---------|---------|
| Python | `sys.version_info` | < 3.11 | — | — |
| Environnement | `env/example` + `env/dev` | `env/example` absent ou clé requise manquante | `env/dev` absent | — |
| Structure MVC | filesystem | `mvc/`, `mvc/routes.py`, `mvc/entities/`, `mvc/entities/relations.json`, `mvc/views/` ou `mvc/controllers/` absent | — | — |
| Entités | `forge_cli.entities.model.check_model()` | modèle invalide | aucune entité détectée | `mvc/entities/` absent |
| Certificats SSL | `SSL_CERTFILE` / `SSL_KEYFILE` via `config.py` | — | fichiers absents | `config.py` non chargeable |
| Node.js / npm | `shutil.which("npm")` | — | npm absent | — |
| Base de données | driver `mariadb` + credentials `DB_APP_*` via `config.py` | — | driver absent ou connexion refusée | `env/dev` absent ou credentials vides |

**Code de sortie :** `0` si aucun `FAIL`, `1` sinon.

### `forge help`

Affiche l'aide intégrée de la CLI officielle.

```bash
forge help
forge --help
forge -h
```

La sortie liste les commandes disponibles et quelques exemples d'utilisation. Cette commande n'écrit aucun fichier et quitte avec le code `0`.

`DB_APP_PWD` et `DB_ADMIN_PWD` peuvent être vides en développement local sans déclencher de FAIL.

La configuration effective est chargée en chargeant `config.py` du projet via `importlib` sans polluer `sys.modules`. Les checks SSL et base de données lisent les valeurs depuis ce module (`SSL_CERTFILE`, `SSL_KEYFILE`, `DB_APP_*`).
