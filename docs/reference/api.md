# Index API

Chaque entrée ci-dessous est repliée par défaut. Ouvrez uniquement la partie utile pour lire le détail de l'API sans quitter l'index.

<details markdown="1" id="coreforge">
<summary><code>core.forge</code> - Configuration centrale</summary>

`core.forge` est le registre de configuration du noyau. Les modules `core/` lisent leurs paramètres avec `get()`.

### Fonctions

| API | Signature | Description |
|---|---|---|
| `configure` | `configure(**kwargs) -> None` | Configure Forge. Lève `KeyError` si une clé est inconnue. |
| `get` | `get(key: str) -> object` | Retourne une valeur. Lève `KeyError` si la clé est inconnue. |

### Clés disponibles

| Clé | Défaut | Description |
|---|---|---|
| `app_name` | `"Forge"` | Nom de l'application |
| `app_env` | `"dev"` | Environnement actif |
| `views_dir` | `mvc/views` | Dossier des templates |
| `sql_dir` | `mvc/models/sql` | Dossier des requêtes SQL |
| `upload_root` | `storage/uploads` | Racine des uploads |
| `upload_max_size` | `5242880` | Taille maximale d'un fichier |
| `upload_allowed_extensions` | `["jpg", "jpeg", "png", "webp", "pdf"]` | Extensions autorisées |
| `upload_allowed_mime_types` | `["image/jpeg", "image/png", "image/webp", "application/pdf"]` | MIME autorisés |
| `mail_host` | `""` | Hôte SMTP |
| `mail_port` | `587` | Port SMTP |
| `mail_username` | `""` | Utilisateur SMTP |
| `mail_password` | `""` | Mot de passe SMTP |
| `mail_from` | `""` | Expéditeur par défaut |
| `mail_use_tls` | `False` | Active `STARTTLS` |
| `mail_use_ssl` | `False` | Utilise `SMTP_SSL` |
| `mail_timeout` | `10` | Timeout SMTP en secondes |
| `mail_enabled` | `True` | Active ou désactive l'envoi réel |
| `db_host` | `"localhost"` | Hôte MariaDB |
| `db_port` | `3306` | Port MariaDB |
| `db_name` | `"forge_db"` | Nom de la base |
| `db_user` | `"root"` | Utilisateur MariaDB |
| `db_password` | `""` | Mot de passe |
| `db_pool_size` | `5` | Taille du pool |
| `css_visible` | `"block"` | Classe pagination visible |
| `css_hidden` | `"hidden"` | Classe pagination masquée |
| `router` | `None` | Routeur actif pour `url_for()` |

Les chemins relatifs `views_dir`, `sql_dir` et `upload_root` sont résolus depuis la racine du projet.

### Exemple

```python
from core.forge import configure, get

configure(
    app_name="Carnet",
    app_env="dev",
    db_name="carnet_dev",
    db_user="carnet_app",
)

print(get("app_name"))
```

</details>

<details markdown="1" id="corehttprequest">
<summary><code>core.http.request</code> - Requête HTTP</summary>

### Classes

| API | Description |
|---|---|
| `Request` | Représente une requête HTTP entrante. |
| `UploadedFile` | Fichier reçu dans un formulaire `multipart/form-data`. |
| `RequestEntityTooLarge` | Exception levée si le body dépasse la limite autorisée. |

### `Request`

Attributs principaux :

| Attribut | Type | Description |
|---|---|---|
| `original_method` | `str` | Méthode reçue avant override. |
| `method` | `str` | Méthode effective. `POST` peut devenir `PUT`, `PATCH` ou `DELETE` via `_method`. |
| `path` | `str` | Chemin sans query string. |
| `headers` | `HTTPMessage` | En-têtes HTTP. |
| `params` | `dict[str, list[str]]` | Query string parsée avec `parse_qs`. |
| `body` | `dict[str, list[str]]` | Formulaire parsé. |
| `json_body` | `dict` | JSON parsé si `Content-Type` vaut `application/json`. |
| `files` | `dict[str, UploadedFile]` | Fichiers uploadés. |
| `ip` | `str` | Adresse IP client. |
| `route_params` | `dict[str, str]` | Paramètres injectés par le routeur. |

### Exemple

```python
def create_contact(request):
    name = request.body.get("name", [""])[0]
    avatar = request.files.get("avatar")

    if avatar:
        print(avatar.filename, avatar.content_type, avatar.size)

    return Response(201, f"Contact {name} créé")
```

Notes :

- `GET`, `HEAD` et `OPTIONS` ne lisent pas de body.
- La limite de body par défaut est `1_048_576` octets.
- Les uploads multipart utilisent au minimum `1 MiB` et ajoutent une marge de `65_536` octets à `upload_max_size`.

</details>

<details markdown="1" id="corehttpresponse">
<summary><code>core.http.response</code> - Réponse HTTP</summary>

### Classe

```python
Response(status=200, body=b"", content_type="text/html; charset=utf-8", headers=None)
```

| Attribut | Type | Description |
|---|---|---|
| `status` | `int` | Code HTTP. |
| `body` | `bytes` | Corps de réponse. Une `str` est encodée en UTF-8. |
| `content_type` | `str` | Type MIME. |
| `headers` | `dict` | En-têtes additionnels. |

### Exemples

```python
from core.http.response import Response

def health(request):
    return Response(200, "OK", content_type="text/plain; charset=utf-8")
```

```python
return Response(
    302,
    "",
    headers={"Location": "/login"},
)
```

</details>

<details markdown="1" id="corehttphelpers">
<summary><code>core.http.helpers</code> - Helpers HTML et JSON</summary>

### Fonctions

| API | Signature | Description |
|---|---|---|
| `html` | `html(template, status=200, context=None, raw=False) -> Response` | Rend un template et retourne une `Response`. |
| `json_response` | `json_response(data, status=200) -> Response` | Sérialise `data` en JSON et retourne une `Response` avec `Content-Type: application/json; charset=utf-8`. |
| `api_success` | `api_success(data=None, status=200, meta=None) -> Response` | Réponse JSON de succès structurée : `{"success": true, "data": ...}`. |
| `api_error` | `api_error(message, status=400, code="error", details=None) -> Response` | Réponse JSON d'erreur structurée : `{"success": false, "error": {...}}`. |

`raw=True` lit le fichier depuis `views_dir` sans passer par Jinja2.

`json_response` accepte tout type sérialisable par `json.dumps` : `dict`, `list`, `str`, `int`, `float`, `bool`, `None`. Lève `ValueError` si les données ne sont pas sérialisables.

`api_success` et `api_error` utilisent `json_response` en interne.

### Convention de réponse réussie

```json
{"success": true, "data": {"id": 1, "nom": "Contact"}}
```

Avec liste et métadonnées :

```json
{"success": true, "data": [...], "meta": {"count": 2}}
```

### Convention de réponse d'erreur

```json
{"success": false, "error": {"code": "not_found", "message": "Ressource introuvable"}}
```

Avec détails de validation :

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Données invalides",
    "details": {"email": "Champ obligatoire"}
  }
}
```

### Statuts HTTP recommandés

| Cas | Statut |
|---|---|
| Succès lecture | 200 |
| Création | 201 |
| Requête invalide | 400 |
| Non authentifié | 401 |
| Interdit | 403 |
| Introuvable | 404 |
| Erreur de validation | 422 |
| Erreur serveur | 500 |

### Exemple — HTML

```python
from core.http.helpers import html

def dashboard(request):
    return html("dashboard/index.html", context={"title": "Tableau de bord"})
```

### Exemple — JSON simple

```python
from core.http import json_response

def status(request):
    return json_response({"status": "ok", "service": "forge"})
```

### Exemple — JSON structuré

```python
from core.http import api_success, api_error

def index(request):
    contacts = [{"id": 1, "nom": "Alice"}, {"id": 2, "nom": "Bob"}]
    return api_success(contacts, meta={"count": len(contacts)})

def show(request):
    contact = None  # non trouvé
    if contact is None:
        return api_error("Ressource introuvable", status=404, code="not_found")
    return api_success(contact)

def create(request):
    return api_success({"id": 42}, status=201)
```

### Convention mvc/api_routes.py

Les routes API se déclarent dans un fichier optionnel `mvc/api_routes.py`. Si le fichier
est présent, `Application` le charge automatiquement au démarrage. S'il est absent,
l'application fonctionne normalement.

```python
# mvc/api_routes.py
from core.http import api_success, api_error

def _status(request):
    return api_success({"status": "ok", "service": "forge"})

def _introuvable(request):
    return api_error("Ressource introuvable", status=404, code="not_found")

def register_api_routes(router):
    router.add("GET", "/api/status", _status, public=True, api=True)
    router.add("GET", "/api/missing", _introuvable, public=True, api=True)
```

La fonction `register_api_routes(router)` est la convention attendue. Elle reçoit le routeur
et y ajoute les routes API. La séparation avec `mvc/routes.py` est organisationnelle :
les deux fichiers partagent le même routeur.

Pour désactiver le chargement automatique, passer `api_routes_module=None` à `Application` :

```python
app = Application(router, api_routes_module=None)
```

### Convention mvc/api_routes.py avec protection

```python
# mvc/api_routes.py
from core.http import api_success, api_error
from core.security.api_auth import require_api_token

@require_api_token
def _status(request):
    return api_success({"status": "ok", "service": "forge"})

def register_api_routes(router):
    router.add("GET", "/api/status", _status, public=True, api=True)
```

Requête :

```http
GET /api/status
Authorization: Bearer <token>
```

Réponse si token valide :

```json
{"success": true, "data": {"status": "ok", "service": "forge"}}
```

### Limites actuelles

- Pas de parsing automatique du body JSON entrant (voir `request.json_body`).
- Pas de pagination avancée.
- Pas de validation de payload.
- Auth API par token statique uniquement — pas de JWT, pas d'OAuth.

</details>

<details markdown="1" id="coresecurityapiauth">
<summary><code>core.security.api_auth</code> - Auth API par token Bearer</summary>

### Fonctions et décorateur

| API | Signature | Description |
|---|---|---|
| `require_api_token` | `require_api_token(func)` | Décorateur — protège une route API par token Bearer. |
| `get_api_token_from_request` | `get_api_token_from_request(request) -> str \| None` | Extrait le token du header `Authorization`. Retourne `None` si absent ou format invalide. |
| `is_valid_api_token` | `is_valid_api_token(request) -> bool` | Retourne `True` si le token correspond à `API_TOKEN`. |

### Configuration

Le token attendu est lu depuis la variable d'environnement `API_TOKEN` :

```bash
# env/dev ou env/prod
API_TOKEN=votre-token-secret
```

Si `API_TOKEN` n'est pas configuré ou est vide, **toutes les requêtes sont refusées** (comportement fail-secure).

Ne jamais versionner ce fichier. Ne jamais exposer la valeur dans les logs, les réponses ou les traces.

### Réponses d'erreur

| Situation | Statut | `error.code` |
|---|---|---|
| Header `Authorization` absent | 401 | `unauthorized` |
| Format invalide (pas `Bearer <token>`) | 401 | `invalid_authorization_header` |
| Token invalide ou `API_TOKEN` non configuré | 401 | `invalid_token` |

### Décorateur `require_api_token`

```python
from core.http import api_success
from core.security.api_auth import require_api_token

@require_api_token
def status(request):
    return api_success({"status": "ok"})
```

Le décorateur s'applique directement sur la fonction handler. Il n'interfère pas avec les routes HTML, CSRF ou RBAC.

### Limites

- Token statique unique — pas de multi-token, pas de scopes.
- Pas de JWT ni d'OAuth.
- Pas de rate limiting (ticket `API-RATE-LIMIT-001` futur).
- Ne pas utiliser en production sans HTTPS.

</details>

<details markdown="1" id="coreapiroutesloader">
<summary><code>core.api_routes_loader</code> - Chargement optionnel des routes API</summary>

### Fonction

| API | Signature | Description |
|---|---|---|
| `load_api_routes` | `load_api_routes(router, module_path="mvc.api_routes")` | Charge le module API s'il existe et appelle `register_api_routes(router)`. |

Comportement :

| Situation | Résultat |
|---|---|
| Module absent | Retour silencieux — aucune erreur |
| Module présent, `register_api_routes` définie | Routes ajoutées au routeur |
| Module présent, sans `register_api_routes` | Avertissement loggé, aucune route ajoutée |
| Module présent, erreur Python | `ImportError` levé avec message explicite |

### Exemple

```python
from core.api_routes_loader import load_api_routes
from core.http.router import Router

router = Router()
load_api_routes(router)  # charge mvc/api_routes.py si présent
```

</details>

<details markdown="1" id="corehttprouter">
<summary><code>core.http.router</code> - Router, routes et URL nommées</summary>

### Classes et constantes

| API | Description |
|---|---|
| `Router` | Registre de routes. |
| `RouteEntry` | Route compilée avec méthode, pattern, handler et options. |
| `RouteGroup` | Groupe de routes partageant un préfixe et des options. |
| `SAFE_METHODS` | `{"GET", "HEAD", "OPTIONS"}` |
| `UNSAFE_METHODS` | `{"POST", "PUT", "PATCH", "DELETE"}` |

### Méthodes publiques de `Router`

| API | Signature | Description |
|---|---|---|
| `add` | `add(method, pattern, handler, name=None, public=False, csrf=True, api=False) -> Router` | Ajoute une route. |
| `group` | `group(prefix, public=False, csrf=True, api=False) -> RouteGroup` | Crée un groupe utilisable avec `with`. |
| `match` | `match(method, path) -> tuple[RouteEntry, dict] \| None` | Retourne la route et ses paramètres. |
| `resolve` | `resolve(method, path) -> tuple[handler, dict] \| None` | Retourne le handler et ses paramètres. |
| `is_public` | `is_public(path, method=None) -> bool` | Indique si une route est publique. |
| `iter_routes` | `iter_routes() -> list[RouteEntry]` | Liste les routes déclarées. |
| `url_for` | `url_for(name, **params) -> str` | Génère une URL depuis une route nommée. |

### Patterns supportés

| Pattern | URL | Paramètres |
|---|---|---|
| `/contacts` | `/contacts` | `{}` |
| `/contacts/{id}` | `/contacts/42` | `{"id": "42"}` |
| `/api/{version}/contacts/{id}` | `/api/v1/contacts/5` | `{"version": "v1", "id": "5"}` |

### Exemples

```python
from core.http.router import Router

router = Router()
router.add("GET", "/", home, name="home", public=True, csrf=False)
router.add("POST", "/contacts", create_contact, name="contacts.create")

url = router.url_for("contacts.create")
```

```python
with router.group("/admin", public=False) as admin:
    admin.add("GET", "", admin_index, name="admin.index")
    admin.add("POST", "/users", create_user, name="admin.users.create")
```

Une route `POST`, `PUT`, `PATCH` ou `DELETE` est protégée par CSRF par défaut, sauf si `csrf=False`.

</details>

<details markdown="1" id="coreapplication">
<summary><code>core.application</code> - Dispatch applicatif</summary>

### Classe

```python
Application(router, middlewares=None, login_url="/login", csrf_middleware=None,
            *, api_routes_module="mvc.api_routes")
```

Le paramètre `api_routes_module` indique le module Python à charger pour les routes API.
Valeur par défaut : `"mvc.api_routes"`. Passer `None` pour désactiver le chargement.

### Méthode

| API | Signature | Description |
|---|---|---|
| `dispatch` | `dispatch(request) -> Response` | Résout la route, applique CSRF et middlewares, appelle le handler. |

### Flux réel

1. Recherche de la route.
2. Si aucune route ne correspond, retourne `errors/404.html`.
3. Injection de `request.route_params`.
4. Vérification CSRF pour les méthodes unsafe si la route le demande.
5. Exécution des middlewares pour les routes non publiques.
6. Appel du handler.
7. En cas d'exception non gérée, retourne `errors/500.html`.

### Exemple middleware

```python
from core.http.response import Response

class AdminOnly:
    def check(self, request):
        if not request.headers.get("X-Admin"):
            return Response(403, "Interdit")
        return None
```

</details>

<details markdown="1" id="coretemplating-et-jinja2">
<summary><code>core.templating</code> et <code>integrations.jinja2</code> - Templates</summary>

### API

| Élément | Signature | Description |
|---|---|---|
| `template_manager` | singleton `TemplateManager` | Renderer actif. |
| `TemplateManager.register` | `register(renderer) -> None` | Enregistre ou remplace le renderer. |
| `TemplateManager.render` | `render(template, context) -> str` | Rend un template. Lève `RuntimeError` sans renderer. |
| `Jinja2Renderer` | `Jinja2Renderer(views_dir: str)` | Renderer Jinja2 avec autoescape HTML. |

`Jinja2Renderer` expose le helper global `url_for(name, **params)`, branché sur `core.forge.get("router")`.

### Exemples

```python
from core.forge import configure, get
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer

configure(views_dir="mvc/views", router=router)
template_manager.register(Jinja2Renderer(get("views_dir")))
```

```html
<a href="{{ url_for('contacts.show', id=contact.ContactId) }}">
  Voir
</a>
```

</details>

<details markdown="1" id="coresecurity">
<summary><code>core.security</code> - Sessions, auth, CSRF et mots de passe</summary>

Pour l'authentification des nouveaux projets, utiliser `core.auth`. Les modules `core.security` historiques restent présents pour les briques transversales officielles (`core.security.session`, `core.security.csrf`). Le RBAC (`Role`, `Permission`, `require_permission`) est disponible via `forge-mvc-rbac`. Voir [docs/auth.md — Frontière API](../auth.md#api-officielle-et-compatibilite-legacy).

### Sessions mémoire

| API | Description |
|---|---|
| `create_session()` | Crée une session et retourne son identifiant. |
| `get_session(session_id)` | Retourne la session ou `None`. |
| `delete_session(session_id)` | Supprime une session. |
| `regenerate_session(old_session_id)` | Crée une nouvelle session en copiant les données. |
| `authenticate_session(session_id, user)` | Marque une session comme authentifiée et retourne un nouveau `session_id`. |
| `get_session_id(request)` | Lit le cookie `session_id`. |
| `is_authenticated(request)` | Vérifie l'authentification. |
| `get_user(request)` | Retourne l'utilisateur de session. |
| `user_has_role(request, role)` | Vérifie un rôle. |
| `set_flash(session_id, message, level="success")` | Stocke un message flash. |
| `get_flash(session_id)` | Lit et consomme le flash. |

Le stockage de session délègue au backend actif via `core.sessions.get_session_store()`. Le backend par défaut est `MemorySessionStore` (dict Python en mémoire, thread-safe). Il convient au développement et aux petites applications mono-processus derrière Nginx. Les sessions sont perdues au redémarrage, ne sont pas partagées entre workers et ne conviennent pas au scaling horizontal. Voir [ADR-002 — Stratégie de session](../adr/002-session-strategy.md) et la [section sessions mémoire du guide de déploiement](../deployment.md#9-limite-importante-sessions-memoire).

Le package `core.sessions` expose le contrat de backend :

| API | Description |
|---|---|
| `SessionStore` | Protocol minimal (`create`, `get`, `set`, `delete`, `regenerate`) |
| `MemorySessionStore` | Backend par défaut (dict Python + RLock, sessions perdues au redémarrage) |
| `FileSessionStore` | Backend fichier JSON (persistance locale, mono-machine) |
| `MariaDbSessionStore` | Backend MariaDB (sessions partagées entre processus) |
| `get_session_store()` | Retourne le backend actif (MemorySessionStore par défaut) |

`FileSessionStore(sessions_dir="storage/sessions", ttl=3600)` — persistance entre redémarrages, sans dépendance externe. Ne supporte pas le multi-worker concurrent.

`MariaDbSessionStore(fetch_one=None, execute=None, ttl=3600)` — sessions partagées via la table `forge_sessions` (voir `mvc/models/sql/forge_sessions.sql`). Prépare les déploiements multi-processus. Doit être configuré explicitement.

### Middleware et décorateurs

| API | Description |
|---|---|
| `AuthMiddleware(login_url="/login")` | Redirige vers `/login` si la session n'est pas authentifiée. |
| `CsrfMiddleware(field_name="csrf_token", header_name="X-CSRF-Token")` | Vérifie le token CSRF sur les routes unsafe. |
| `require_auth` | Décorateur de handler authentifié. |
| `require_csrf` | Décorateur de handler avec CSRF. |
| `require_role(role)` | Décorateur de handler limité à un rôle. |

### Mots de passe et limitation

Pour créer de nouveaux hashes, utiliser `core.auth.password.hash_password` (Argon2id, API officielle).
`core.security.hashing` est désormais **lecture seule** — vérification des hashes PBKDF2 legacy uniquement.

| API | Description |
|---|---|
| `verifier_mot_de_passe(password, stored)` | Vérifie un hash PBKDF2 existant (format versionné et format legacy). |
| `pbkdf2_needs_rehash(stored)` | Retourne toujours `True` — tout hash PBKDF2 doit migrer vers Argon2id. |
| `update_password_hash(id, hash)` | Met à jour le `PasswordHash` de l'utilisateur (`auth_model`). |
| `enregistrer_tentative(ip)` | Enregistre une tentative par IP. |
| `est_limite(ip)` | Limite après `5` tentatives dans une fenêtre de `60` secondes. |

### Exemples

```python
from core.security.session import authenticate_session, create_session, get_session

session_id = create_session()
session_id = authenticate_session(session_id, {
    "UtilisateurId": 1,
    "Login": "roger",
    "roles": ["admin"],
})

session = get_session(session_id)
print(session["user"]["login"])
```

```python
from core.security.decorators import require_role

@require_role("admin")
def admin_dashboard(request):
    return self.render("admin/dashboard.html", request=request)
```

```html
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
```

### Nonce CSP optionnel

`core.security.csp` fournit un mécanisme de nonce par requête pour autoriser des scripts inline sans `unsafe-inline`.

Activer dans `env/dev` ou `env/prod` :

```dotenv
APP_CSP_NONCE_ENABLED=true
```

Dans un template Jinja :

```html
<script nonce="{{ csp_nonce() }}">/* script inline autorisé */</script>
```

| API | Description |
|---|---|
| `generate_nonce()` | Génère un nonce URL-safe 128 bits (`secrets.token_urlsafe(16)`). |
| `set_request_nonce(nonce)` | Stocke le nonce de la requête courante (thread-local). |
| `get_request_nonce()` | Retourne le nonce courant ou `None`. |
| `build_csp_header(nonce=None)` | Construit l'en-tête CSP — avec ou sans nonce, jamais `unsafe-inline`. |
| `csp_nonce()` | Helper Jinja — retourne le nonce ou `""` si désactivé. |

Comportement CSP selon la configuration :

| `APP_CSP_NONCE_ENABLED` | `script-src` généré |
|---|---|
| `false` (défaut) | `script-src 'self'` |
| `true` | `script-src 'self' 'nonce-<valeur>'` |

`unsafe-inline` n'est jamais ajouté automatiquement.

</details>

<details markdown="1" id="coreforms">
<summary><code>core.forms</code> - Formulaires et champs</summary>

### Classe `Form`

| API | Description |
|---|---|
| `Form(data=None, **options)` | Instancie un formulaire. |
| `Form.from_request(request, **options)` | Crée un formulaire depuis `request.body` et `request.files`. |
| `is_bound` | Indique si le formulaire a reçu des données. |
| `errors` | Erreurs par champ. |
| `non_field_errors` | Erreurs globales. |
| `field_errors(name)` | Erreurs d'un champ. |
| `value(name, default="")` | Valeur nettoyée ou brute. |
| `error(name)` | Première erreur d'un champ. |
| `has_error(name)` | Indique si un champ a une erreur. |
| `add_error(name, message)` | Ajoute une erreur. |
| `is_valid()` | Lance la validation et retourne un booléen. |
| `clean()` | Hook de validation globale à surcharger. |
| `context()` | Contexte prêt pour le template. |

### Champs

| Champ | Valeur nettoyée | Usage |
|---|---|---|
| `StringField` | `str` | Texte, longueur, regex. |
| `IntegerField` | `int` | Entiers, min, max. |
| `DecimalField` | `Decimal` | Valeurs décimales précises. |
| `BooleanField` | `bool` | Checkbox. |
| `ChoiceField` | `str` | Valeur parmi une liste. |
| `RelatedIdsField` | `list[int]` | Liste d'identifiants reliés. |
| `EmailField` | `str` | Adresse email (max 254 car., RFC 5321). |
| `PhoneField` | `str` | Numéro de téléphone français (format local ou +33). |
| `UrlField` | `str` | URL http:// ou https:// (max 2048 car.). |
| `DateField` | `datetime.date` | Date HTML natif, format strict `YYYY-MM-DD`. |
| `DateTimeField` | `datetime.datetime` | Date/heure HTML natif, format `YYYY-MM-DDTHH:MM` ou `YYYY-MM-DDTHH:MM:SS`. |
| `TextAreaField` | `str` | Texte long, rendu HTML `<textarea>`, support `min_length`/`max_length`, `render()` avec échappement XSS. |
| `RelationField` | `str` ou `int` | Relation `many_to_one`, validée par liste de choix, destinée aux clés étrangères. |
| `SlugField` | `str` | Slug URL-safe en minuscules, chiffres et tirets (max 120 car. par défaut). |
| `FileField` | `UploadedFile` | Fichier uploadé, validation extension, taille maximale et type MIME optionnel. |
| `ImageField` | `UploadedFile` | Image uploadée, extensions et MIME image contrôlés, sans sauvegarde automatique. |

### Exemple

```python
from core.forms import Form, StringField, IntegerField

class ContactForm(Form):
    prenom = StringField(required=True, max_length=100)
    age = IntegerField(required=False, min_value=0)

    def clean(self):
        if self.cleaned_data.get("prenom") == "admin":
            self.add_error("prenom", "Ce prénom est réservé.")


form = ContactForm.from_request(request)
if form.is_valid():
    contact.prenom = form.cleaned_data["prenom"]
```

`DecimalField` retourne un `Decimal`. Les CRUD générés gardent la doctrine Forge actuelle : les champs JSON de type Python `float` restent convertis en `float`.

### Champs de formulaire avancés — notes d'usage

- **`FileField` / `ImageField`** — valident uniquement les métadonnées (extension, taille, MIME). Ils ne sauvegardent rien et ne créent aucune entrée en base. La persistance est assurée par `save_upload` + `attach_media_to_entity` appelés depuis le contrôleur généré par `make:crud`.
- **`RelationField`** — hérite de `ChoiceField`. Ne fait aucune requête SQL ; la liste de choix est fournie par le contrôleur ou le formulaire via `options`.
- **`DateField` / `DateTimeField`** — retournent des objets Python typés (`datetime.date` / `datetime.datetime`). `make:crud` génère ces champs directement pour les colonnes `DATE` / `DATETIME`.
- **`SlugField`** — valide le format slug, ne slugifie pas automatiquement. Les caractères accentués, majuscules et underscores sont refusés.
- **`TextAreaField`** — fournit un helper `render()` pour générer une balise `<textarea>` avec échappement XSS. Le rendu principal reste assuré par les templates Jinja2.

</details>

<details markdown="1" id="coremvccontroller">
<summary><code>core.mvc.controller</code> - BaseController</summary>

> Ticket : `BASE-CONTROLLER-API-DOC-001`.
> Audit de surface : `docs/history/audits/base-controller-surface-audit-001.md`.

`BaseController` expose **18 méthodes statiques** : 17 canoniques, 1 legacy
(`current_user()`), 2 à surveiller (`set_flash()`, `csrf_token()`).

### Méthodes canoniques

| Méthode | Signature | Description |
|---|---|---|
| `render` | `render(template, status=200, context=None, base="layouts/base.html", *, request=None, raw=False)` | Génère une réponse HTML via Jinja2. Si `request` est fourni et `raw=False`, injecte `csrf_token` et appelle les fournisseurs de contexte Jinja enregistrés. |
| `redirect` | `redirect(location, *, request=None, flash=None, level="success")` | Génère une réponse 302. Si `flash` est fourni avec `request`, stocke un message flash avant de rediriger. |
| `redirect_with_flash` | `redirect_with_flash(request, location, message, level="success")` | Flux POST-Redirect-GET : stocke `message` en flash puis redirige vers `location`. |
| `redirect_to_route` | `redirect_to_route(name, *, request=None, flash=None, level="success", **params)` | Redirige vers une route nommée via le routeur actif. Lève `RuntimeError` si aucun routeur n'est configuré. |
| `not_found` | `not_found()` | Retourne une réponse 404. |
| `bad_request` | `bad_request(context=None)` | Retourne une réponse 400. |
| `forbidden` | `forbidden(context=None)` | Retourne une réponse 403. |
| `validation_error` | `validation_error(template="errors/422.html", context=None, *, request=None)` | Retourne une réponse 422 via `render()`. |
| `server_error` | `server_error(context=None)` | Retourne une réponse 500. |
| `include` | `include(partial, context=None)` | Rend un partial Jinja2 et retourne son HTML sous forme de chaîne. |
| `json` | `json(data, status=200)` | Génère une réponse `application/json; charset=utf-8`. |
| `body` | `body(request)` | Aplatit `request.body` en dict `{champ: première_valeur}`. |
| `json_body` | `json_body(request)` | Retourne `request.json_body` (dict parsé). Vide si `Content-Type != application/json`. |
| `render_form` | `render_form(template, request, data, status=200, erreurs="")` | Raccourci `render()` + `form_context()` en une ligne. |
| `form_context` | `form_context(request, data, erreurs="")` | Construit le contexte formulaire : fusionne `data`, `csrf_token` et `erreurs`. |

### Méthodes À_SURVEILLER

Stables et utilisables, mais dépendent de fonctions du module `core.security.session`
qui n'est pas déprécié mais est qualifié de legacy. Elles seront réévaluées si ce
module devait être supprimé à terme.

| Méthode | Signature | Dépendance |
|---|---|---|
| `set_flash` | `set_flash(request, message, level="success")` | `core.security.session.set_flash`, `get_session_id` |
| `csrf_token` | `csrf_token(request)` | `core.security.session.get_session_id`, `get_session` |

### Méthode legacy — à ne pas utiliser

| Méthode | Signature | Statut |
|---|---|---|
| `current_user` | `current_user(request)` | **LEGACY** — appelle `core.security.session.get_user()` qui émet un `DeprecationWarning`. Absente de tous les starters post-9.1. |

Alternative canonique :

```python
from core.auth.session import get_authenticated_user_id
from mvc.models.auth_model import get_user_by_id

user_id = get_authenticated_user_id(request)
utilisateur = get_user_by_id(user_id) if user_id else None
```

### Exemple d'utilisation canonique

```python
from core.mvc.controller import BaseController

class ContactController(BaseController):
    def index(self, request):
        contacts = fetch_all("SELECT * FROM Contact")
        return self.render(
            "contacts/index.html",
            context={"contacts": contacts},
            request=request,
        )

    def create(self, request):
        data = self.body(request)
        # validation ...
        return self.redirect_with_flash(request, "/contacts", "Contact créé.")

    def api_index(self, request):
        return self.json({"contacts": fetch_all("SELECT * FROM Contact")})
```

Dans les CRUD générés, les identifiants de route sont parsés avant usage.
Une valeur invalide comme `/contacts/abc` retourne `not_found()` au lieu de
provoquer une erreur serveur.

</details>

<details markdown="1" id="coremvcmodel">
<summary><code>core.mvc.model</code> - Validation MVC minimale</summary>

### API

| Élément | Description |
|---|---|
| `Validator` | Validateur simple avec erreurs par champ. |
| `DoublonError` | Exception métier pour signaler un doublon. |

### `Validator`

| Méthode | Description |
|---|---|
| `required(field, value, message=None)` | Vérifie une présence. |
| `max_length(field, value, max_len, message=None)` | Vérifie une longueur maximale. |
| `add_error(field, message)` | Ajoute une erreur. |
| `is_valid()` | Retourne `True` sans erreur. |
| `errors` | Dictionnaire des erreurs. |

### Exemple

```python
from core.mvc.model.validator import Validator

validator = Validator()
validator.required("Email", email)
validator.max_length("Nom", nom, 100)

if not validator.is_valid():
    return self.validation_error({"errors": validator.errors})
```

</details>

<details markdown="1" id="coremvcview">
<summary><code>core.mvc.view</code> - Pagination</summary>

### Classe

```python
Pagination(request, total, par_page)
```

### Attributs et méthodes

| API | Description |
|---|---|
| `total` | Nombre total d'éléments. |
| `par_page` | Taille de page. |
| `nb_pages` | Nombre de pages. |
| `page` | Page courante, lue depuis `?page=`. |
| `limit` | Limite SQL. |
| `offset` | Offset SQL. |
| `pages` | Liste des numéros de page. |
| `context` | Contexte avec classes CSS `css_visible` / `css_hidden`. |
| `to_dict()` | Version dictionnaire avec booléens `has_prev` et `has_next`. |

### Exemple

```python
pagination = Pagination(request, total=125, par_page=20)
rows = fetch_all("SELECT * FROM Contact LIMIT ? OFFSET ?", [
    pagination.limit,
    pagination.offset,
])

return self.render("contacts/index.html", {
    "contacts": rows,
    "pagination": pagination.context,
})
```

</details>

<details markdown="1" id="mvchelpers">
<summary><code>mvc.helpers</code> - Fragments HTML utiles aux vues</summary>

### API

| Élément | Signature | Description |
|---|---|---|
| `render_flash_html` | `render_flash_html(request) -> str` | Lit le flash de session, le consomme et rend `partials/flash.html`. |
| `render_errors_html` | `render_errors_html(errors: list[str]) -> str` | Convertit une liste d'erreurs en `<ul>` HTML échappée. |

### Niveaux de flash

| Niveau | Classes CSS |
|---|---|
| `success` | `bg-green-100 border-green-400 text-green-800` |
| `error` | `bg-red-100 border-red-400 text-red-800` |
| `warning` | `bg-gray-100 border-gray-300 text-gray-800` |
| `info` | `bg-gray-100 border-gray-300 text-gray-800` |

### Exemples

```python
from mvc.helpers.flash import render_flash_html

flash = render_flash_html(request)
return self.render("contacts/index.html", {
    "flash": flash,
}, request=request)
```

```html
{{ flash | safe }}
```

```python
from mvc.helpers.form_errors import render_errors_html

errors_html = render_errors_html(["Le nom est obligatoire."])
```

</details>

<details markdown="1" id="coredatabase">
<summary><code>core.database</code> - MariaDB, transactions et SQL loader</summary>

### API canonique

Tout accès SQL applicatif passe par `core.database.db`. Ces quatre fonctions couvrent tous les cas courants :

| API | Description |
|---|---|
| `fetch_one(query, params=(), tx=None)` | Retourne une ligne ou `None`. |
| `fetch_all(query, params=(), tx=None)` | Retourne toutes les lignes. |
| `execute(query, params=(), tx=None)` | Exécute une requête, retourne le nombre de lignes affectées. |
| `insert(query, params=(), tx=None)` | Exécute un INSERT, retourne le dernier id. |

Sans transaction explicite, chaque helper gère connexion, commit et rollback automatiquement.

### Cas avancés — connexion directe

Pour les transactions multi-statement ou les opérations en bulk, utiliser `core.database.transaction` :

```python
from core.database.transaction import transaction
from core.database.db import execute

with transaction() as tx:
    execute("DELETE FROM pivot WHERE source_id = ?", (source_id,), tx=tx)
    for target_id in selected_ids:
        execute("INSERT INTO pivot VALUES (?, ?)", (source_id, target_id), tx=tx)
```

`get_connection()` / `close_connection()` de `core.database.connection` sont une API interne — ne pas les utiliser directement dans le code applicatif.

### Transactions

| API | Description |
|---|---|
| `Transaction` | Transaction explicite avec connexion dédiée. |
| `transaction()` | Context manager transactionnel. |

### SQL loader

| API | Description |
|---|---|
| `charger_queries(nom_fichier)` | Charge un fichier depuis `{sql_dir}/{app_env}/` et le met en cache. |

Le cache est invalidé si la taille ou `mtime_ns` du fichier change.

### Exemples

```python
from core.database.db import fetch_all

contacts = fetch_all("SELECT * FROM Contact ORDER BY Nom")
```

```python
from core.database.transaction import transaction
from core.database.db import execute, insert

with transaction() as tx:
    contact_id = insert(
        "INSERT INTO Contact (Nom) VALUES (?)",
        ["Dupont"],
        tx=tx,
    )
    execute(
        "INSERT INTO Log (Message) VALUES (?)",
        [f"Contact {contact_id} créé"],
        tx=tx,
    )
```

```python
from core.database.sql_loader import charger_queries

queries = charger_queries("contacts.sql")
rows = fetch_all(queries["select_all"])
```

En production, l'utilisateur applicatif MariaDB doit rester limité aux droits runtime (`SELECT`, `INSERT`, `UPDATE`, `DELETE`). Les droits de migration (`CREATE`, `ALTER`, `DROP`, `INDEX`, `REFERENCES`) doivent être réservés à un utilisateur d'administration ou de migration.

### Table technique `forge_migrations`

`forge db:init` prépare aussi la table `forge_migrations` dans la base du
projet avec `CREATE TABLE IF NOT EXISTS`. Cette table est le socle des
migrations SQL versionnées de Forge.

Elle stocke la version, le nom, le fichier, le checksum, la date d'application
et le temps d'exécution d'une migration. Les migrations restent des fichiers SQL
lisibles dans `mvc/migrations/`.

Le workflow complet est documenté dans [Migrations SQL](../migrations.md).

### `forge migration:status`

`forge migration:status` compare les fichiers SQL locaux avec les lignes de
`forge_migrations`. Elle est en lecture seule et affiche `APPLIED`, `PENDING`,
`CHANGED` ou `MISSING`.

### `forge migration:make`

`forge migration:make <nom>` crée une migration SQL vide dans `mvc/migrations/`.
La commande accepte aussi des sources explicites :

- `--from-entity <Entite>` : copie le SQL généré d'une entité ;
- `--from-entities` : concatène tous les SQL d'entités ;
- `--from-diff <Entite>` : génère seulement les changements prudents du diff.

Forge n'applique jamais une migration au moment de sa création.

### `forge migration:diff`

`forge migration:diff --entity <Entite>` compare le JSON canonique d'une entité
avec les colonnes réelles de la table MariaDB. La commande est strictement en
lecture seule.

### `forge migration:apply`

`forge migration:apply` applique uniquement les migrations locales en statut
`PENDING`, dans l'ordre croissant de version. Chaque fichier SQL reste lisible
dans `mvc/migrations/`.

La commande refuse l'exécution si une migration `CHANGED` ou `MISSING` existe.
Elle arrête immédiatement au premier échec SQL et n'enregistre pas la migration
échouée dans `forge_migrations`.

</details>

<details markdown="1" id="frontcss">
<summary>Front et CSS</summary>

Tailwind est le framework CSS officiel de Forge pour les templates générés.
Forge ne maintient pas plusieurs variantes Bootstrap, Bulma, Foundation ou
autres frameworks CSS.

Le fichier source Tailwind est `static/src/input.css`. Le fichier compilé servi
par l'application est `static/tailwind.css`.

```bash
npm install
npm run build:css
```

Node.js/npm est nécessaire uniquement pour recompiler le CSS, pas pour exécuter
le serveur Python Forge lorsque `static/tailwind.css` existe déjà.

Voir aussi : [Front et CSS](../front.md).

</details>

<details markdown="1" id="coreuploads">
<summary><code>core.uploads</code> - Uploads et stockage</summary>

### Gestionnaire

| API | Description |
|---|---|
| `SavedUpload` | Résultat d'un upload sauvegardé. |
| `upload_root()` | Racine des fichiers uploadés. |
| `save_upload(file, category="documents", variants=False)` | Valide puis sauvegarde un fichier. |
| `delete_media_file(path, variants=False)` | Supprime un fichier média relatif, et ses variantes si demandé. |
| `serve_media_file(path)` | Retourne une réponse HTTP pour un fichier média relatif sûr. |
| `delete_upload(path_or_saved_upload)` | Supprime un fichier. |
| `get_upload_path(relative_path)` | Résout un chemin d'upload. |
| `normalize_media_path(path)` | Normalise un chemin média relatif à `storage/uploads`. |
| `media_path_to_storage_path(path, root=...)` | Résout un chemin média relatif sous la racine d'upload. |
| `generate_image_variants(path, root=...)` | Génère les variantes `medium` et `thumbnail` d'une image. |

### Stockage

| API | Description |
|---|---|
| `ensure_upload_dirs()` | Crée les dossiers nécessaires. |
| `safe_category(category)` | Nettoie un nom de catégorie. |
| `secure_filename(filename)` | Nettoie un nom de fichier. |
| `generate_unique_filename(filename)` | Génère un nom unique. |
| `category_dir(category)` | Retourne le dossier de catégorie. |
| `save_bytes(data, filename, category)` | Sauvegarde des octets. |
| `delete_file(relative_path)` | Supprime un fichier. |

### Validation et exceptions

| API | Description |
|---|---|
| `validate_upload_metadata(filename, size, content_type)` | Valide nom, taille, extension et MIME. |
| `UploadError` | Exception de base. |
| `UploadTooLargeError` | Fichier trop volumineux. |
| `UploadInvalidExtensionError` | Extension refusée. |
| `UploadInvalidMimeTypeError` | MIME refusé. |
| `UploadStorageError` | Erreur d'écriture ou suppression. |

### Exemple

```python
from core.uploads.manager import save_upload

def upload_avatar(request):
    file = request.files.get("avatar")
    if not file:
        return self.bad_request()

    saved = save_upload(file, category="avatars")
    return self.json({
        "filename": saved.filename,
        "path": saved.path,
        "size": saved.size,
    })
```

Pour une image, les variantes restent optionnelles :

```python
saved = save_upload(file, category="images", variants=True)

saved.path
# "images/photo.png"

saved.variants
# {
#     "medium": "images/medium/photo.png",
#     "thumbnail": "images/thumbnail/photo.png",
# }
```

Sans `variants=True`, `save_upload()` conserve le comportement historique et
ne génère que le fichier original. L'option est réservée à `category="images"`.

Supprimer un fichier média :

```python
from core.uploads import delete_media_file

delete_media_file("images/photo.png", variants=True)
# {
#     "images/photo.png": True,
#     "images/medium/photo.png": True,
#     "images/thumbnail/photo.png": True,
# }
```

Par défaut, seule la cible est supprimée. Avec `variants=True`, Forge calcule
les chemins `medium` et `thumbnail` avec la même convention que la génération
des variantes. Les chemins doivent rester relatifs à `storage/uploads`; les
chemins absolus, URL et traversals (`..`) sont refusés.

Servir un fichier média :

```text
/media/images/photo.png
/media/images/medium/photo.png
/media/documents/contrat.pdf
```

La route `/media/<chemin-relatif>` lit uniquement dans `storage/uploads/`.
Un chemin dangereux ou absent retourne `404`. Le `Content-Type` est déduit avec
la bibliothèque standard `mimetypes`, avec fallback `application/octet-stream`.

Créer et lister des métadonnées `Media` :

```python
from forge_mvc_media import create_media_record, list_media_for_entity

media_id = create_media_record(
    entity_name="hebergement",
    entity_id=12,
    path="images/photo.png",
    original_name="photo.png",
    mime_type="image/png",
    role="gallery",
    position=1,
)

medias = list_media_for_entity("hebergement", 12)
```

`create_media_record()` normalise `path`, renseigne `role="default"` et
`position=0` si rien n'est fourni, puis insère une ligne SQL explicite.
`list_media_for_entity()` filtre par `entity_name`, `entity_id`, optionnellement
par `role`, et trie par `position ASC`, puis `id ASC`.

Supprimer un média complet :

```python
from forge_mvc_media import delete_media

result = delete_media(
    media_id,
    delete_files=True,
    variants=True,
)
```

`delete_media_record()` supprime seulement la ligne SQL. `delete_media_file()`
supprime seulement les fichiers. `delete_media()` combine les deux, mais garde
`delete_files=False` par défaut pour éviter une suppression physique
accidentelle.

Récupérer une galerie ordonnée :

```python
from forge_mvc_media import get_media_gallery

gallery = get_media_gallery("hebergement", 12)
```

Par défaut, une galerie utilise `role="gallery"`. Chaque élément contient
`path`, `url`, et, pour les images, `medium_url` et `thumbnail_url`. Les
documents non-image gardent `medium_url` et `thumbnail_url` à `None`.
Forge ne génère pas de galerie HTML dans cette API.

Récupérer l'image de couverture :

```python
from forge_mvc_media import get_cover_media

cover = get_cover_media("hebergement", 12)
```

La convention est `role="cover"`. L'élément retourné utilise la même structure
que la galerie, avec `url`, `medium_url` et `thumbnail_url` pour les images. Si
aucun cover n'existe, la fonction retourne `None`. Avec
`fallback_to_gallery=True`, Forge peut retourner la première image de galerie,
sans choisir de document non-image et sans modifier la base.

### Tests E2E upload (E2E-UPLOAD-HTTP-001)

Le cycle upload est testé en quasi-E2E via `Application.dispatch()` dans
`tests/test_e2e_upload_http.py` (30 tests). Ce qui est couvert :

- parsing multipart `Request._parse_multipart()` et `Request` complet ;
- fichier reçu dans `request.files` ;
- `Application.dispatch()` → contrôleur → `save_upload()` → stockage disque ;
- upload valide : 201, chemin relatif sous `images/`, contenu exact ;
- extension interdite (`.php`, `.exe`) : 422, aucun fichier créé ;
- fichier trop gros : 422, aucun fichier créé ;
- champ absent : 422, aucun fichier créé ;
- path traversal (`../../evil.png`) : stockage sécurisé sans sortie de `uploads/`.

Ce qui reste hors périmètre :
- magic bytes / MIME sniffing binaire ;
- les headers de sécurité globaux (HSTS, CSP, X-Frame-Options) sont appliqués
  par `app.py._send_response()`, pas par `dispatch()` — ils restent testés dans
  `test_security_headers.py` (E2E TCP réel).

### Rate limiting upload (SECURITY-UPLOAD-RATE-LIMIT-001)

`core.uploads.rate_limit` fournit une fenêtre glissante en mémoire, thread-safe,
distincte du rate limiting de connexion (`core.security.hashing`).

```python
from core.uploads.rate_limit import is_upload_rate_limited, record_upload_attempt

def upload_avatar(request):
    if is_upload_rate_limited(request.ip):
        body = json.dumps({
            "success": False,
            "error": {"code": "rate_limited", "message": "Trop d'uploads."},
        }).encode()
        return Response(429, body, "application/json")
    record_upload_attempt(request.ip)
    # ... save_upload(...)
```

| Symbole | Type | Rôle |
|---|---|---|
| `UPLOAD_MAX_PAR_FENETRE` | `int` (10) | Uploads autorisés par IP par fenêtre |
| `UPLOAD_RATE_LIMIT_WINDOW` | `int` (60) | Durée de la fenêtre glissante (secondes) |
| `is_upload_rate_limited(ip)` | `bool` | `True` si la limite est atteinte |
| `record_upload_attempt(ip)` | `None` | Enregistre un upload dans la fenêtre |

Testé dans `tests/test_security_upload_rate_limit.py` (17 tests).

</details>

<details markdown="1" id="media-entity">
<summary><code>mvc/entities/media</code> - Socle Media v2</summary>

Forge fournit une entité canonique `Media` comme première base de Média v2.
Elle décrit uniquement les métadonnées persistables d'un fichier déjà stocké,
sans ajouter de galerie, miniature, route publique ou intégration CRUD.

`Media.path` stocke toujours un chemin relatif normalisé sous `storage/uploads`,
jamais un chemin absolu système. Par exemple :

```text
Media.path = "images/photo.jpg"
```

désigne le fichier :

```text
storage/uploads/images/photo.jpg
```

Les chemins absolus, URL et traversals (`..`) sont refusés par
`normalize_media_path()`.

### Variantes image

Forge peut générer trois chemins de variantes pour une image stockée :

```text
images/photo.png
images/medium/photo.png
images/thumbnail/photo.png
```

- `original` : fichier conservé tel quel.
- `medium` : image redimensionnée dans un maximum de `1280 x 1280`.
- `thumbnail` : image redimensionnée dans un maximum de `300 x 300`.

Les proportions sont conservées. Les formats acceptés sont `jpg`, `jpeg`, `png`
et `webp`. Les chemins retournés restent relatifs à `storage/uploads`.

L'intégration CRUD complète (formulaires, upload, remplacement, suppression, preview) est disponible via la clé `"media"` dans `entity.json` — voir la section *Génération CRUD media* ci-dessous. Les galeries `multiple=true` et les permissions média restent à venir.

Dans le flux d'upload générique, `save_upload(file, category="images",
variants=True)` génère `medium` et `thumbnail` explicitement. Le chemin
`saved.path` reste celui de l'original ; `saved.variants` contient uniquement
les variantes redimensionnées.

`delete_media_file("images/photo.png", variants=True)` supprime l'original et
les variantes fichier si elles existent. Une variante absente retourne `False`
dans le résultat, sans faire échouer la suppression. La suppression en base de
l'entité `Media` reste à la charge d'un futur ticket.

La route `/media/<chemin-relatif>` permet de servir ces fichiers sans exposer
directement le système de fichiers. Exemple : `Media.path = "images/photo.png"`
devient `/media/images/photo.png`. Les variantes sont accessibles si elles
existent, par exemple `/media/images/medium/photo.png`.

Les métadonnées SQL sont manipulées avec l'API `forge_mvc_media` :
`create_media_record()`, `get_media_record()`, `list_media_for_entity()` et
`delete_media_record()`. La suppression SQL ne supprime pas les fichiers physiques ;
utiliser `delete_media_file()` (core) séparément lorsque c'est voulu.

`attach_media_to_entity()` (dans `forge_mvc_media`) relie un `SavedUpload` à une
entité métier en créant une ligne `media`. Elle ne déplace pas le fichier, ne
régénère pas les variantes et ne déclenche aucune suppression automatique.

`delete_media(media_id, delete_files=True, variants=True)` (dans `forge_mvc_media`)
supprime d'abord les fichiers demandés, puis la ligne SQL. Si le chemin stocké est
dangereux, la suppression est refusée et la ligne SQL n'est pas supprimée silencieusement.

`get_media_gallery("hebergement", 12)` (dans `forge_mvc_media`) retourne les médias
`role="gallery"` triés par `position`, puis `id`, avec les URLs locales `/media/...`.
Les images reçoivent aussi les URLs `medium` et `thumbnail` ; les documents non-image
n'ont pas de variantes inventées.

`get_cover_media("hebergement", 12)` (dans `forge_mvc_media`) retourne le premier
média `role="cover"` trié par `position`, puis `id`. Le fallback vers la galerie est
optionnel via `fallback_to_gallery=True` et reste une aide de lecture, sans génération
HTML ni modification des enregistrements.

### Champs

| Champ | Rôle |
|---|---|
| `id` | Clé primaire technique. |
| `entity_name` | Nom de l'entité applicative liée. |
| `entity_id` | Identifiant de l'enregistrement applicatif lié. |
| `path` | Chemin relatif du fichier stocké. |
| `original_name` | Nom original du fichier. |
| `mime_type` | Type MIME déclaré ou détecté. |
| `size` | Taille du fichier en octets. |
| `role` | Rôle générique du média, par défaut `default`. |
| `position` | Ordre d'affichage futur, par défaut `0`. |
| `alt_text` | Texte alternatif optionnel. |
| `created_at` | Date de création du média. |

Les projections standard `media.sql` et `media_base.py` sont générées depuis
`mvc/entities/media/media.json` avec le mécanisme habituel `forge build:model`.

### Limites

Les variantes d'images (`thumbnail`, `medium`), l'intégration `FileField` / `ImageField` dans `make:crud`, l'upload CRUD et les routes publiques média sont disponibles. Les galeries `multiple=true`, les permissions média et les règles métier applicatives restent à venir.

</details>

<details markdown="1" id="forgemvcmedia">
<summary><code>forge_mvc_media</code> - Helpers applicatifs médias (opt-in)</summary>

`forge_mvc_media` est un module opt-in source-only (`forge-mvc-media`) qui fournit
les helpers applicatifs liés à la table `media`. Il n'est pas publié sur PyPI ; il
s'installe depuis les sources (`pip install -e ./packages/forge-mvc-media`).

Les nouveaux fichiers générés par `forge make:crud --media` importent depuis ce module.

### Repository

| API | Description |
|---|---|
| `create_media_record(entity_name, entity_id, path, ...)` | Insère une ligne dans la table `media`. |
| `attach_media_to_entity(saved_upload, entity_name, entity_id, ...)` | Crée une ligne `media` depuis un `SavedUpload`. |
| `get_media_record(media_id)` | Récupère un média par identifiant. |
| `list_media_for_entity(entity_name, entity_id, role=None)` | Liste les médias liés à une entité, triés position+id. |
| `update_media_alt_text(media_id, alt_text)` | Met à jour le texte alternatif d'un média. |
| `update_media_position(media_id, position)` | Met à jour la position d'un média dans une galerie. |
| `delete_media_record(media_id)` | Supprime uniquement la ligne SQL `media`. |
| `delete_media(media_id, delete_files=False, variants=True)` | Supprime une ligne `media` et, explicitement, ses fichiers. |

### Galerie

| API | Description |
|---|---|
| `media_url(path)` | Construit une URL locale `/media/...` depuis un chemin média sûr. |
| `get_media_gallery(entity_name, entity_id, role="gallery")` | Galerie ordonnée enrichie avec URLs et variantes. |
| `get_cover_media(entity_name, entity_id, role="cover")` | Image de couverture d'une entité, ou `None`. |

### Imports applicatifs médias

Les anciens imports `from core.uploads import attach_media_to_entity` ne sont
plus supportés depuis `MEDIA-SHIMS-REMOVE-001`. L'import correct est
`from forge_mvc_media import ...`.

</details>

<details markdown="1" id="corei18n">
<summary><code>core.i18n</code> - Internationalisation</summary>

`core.i18n` fournit une API Python minimale pour traduire des clés depuis un
catalogue JSON local.

Le catalogue français est :

```text
translations/fr.json
```

Il contient des clés génériques plates en notation pointée (`common.save`,
`crud.create`, `validation.required`, etc.).

### Utilisation

```python
from core.i18n import trans, load_catalog

# Traduction d'une clé (locale fr par défaut)
trans("common.save")                      # → "Enregistrer"
trans("common.save", locale="fr")         # → "Enregistrer"

# Clé absente : la clé est retournée telle quelle
trans("clé.inconnue")                     # → "clé.inconnue"

# Chargement explicite du catalogue
catalog = load_catalog("fr")
catalog = load_catalog("fr", translations_dir="translations")
```

### API disponible

| API | Description |
|---|---|
| `trans(key, locale=None, translations_dir="translations")` | Traduit une clé avec fallback. Utilise la langue par défaut si `locale` est absent. Retourne la clé si introuvable partout. |
| `load_catalog(locale, translations_dir="translations")` | Charge et valide un catalogue JSON. Lève `TranslationCatalogError` si absent, invalide ou mal formé. Les catalogues sont mis en cache après chargement. |
| `clear_translation_cache()` | Vide le cache des catalogues. Utile en tests ou en mode développement. |
| `get_default_locale()` | Retourne la langue par défaut active (`"fr"` initialement). |
| `set_default_locale(locale)` | Change la langue par défaut. Lève `I18nError` si la valeur est vide ou non-chaîne. |
| `get_fallback_locale()` | Retourne la locale de fallback active (`"fr"` initialement). |
| `set_fallback_locale(locale)` | Change la locale de fallback. Accepte `None` pour désactiver. Lève `I18nError` si chaîne vide. |
| `I18nError` | Exception de base de la brique i18n. |
| `TranslationCatalogError` | Catalogue absent, JSON invalide, ou structure incorrecte. |

### Langue par défaut et fallback

La langue par défaut et la langue de fallback sont toutes deux `"fr"` initialement :

```python
from core.i18n import get_default_locale, set_default_locale
from core.i18n import get_fallback_locale, set_fallback_locale

get_default_locale()          # → "fr"
get_fallback_locale()         # → "fr"
set_default_locale("fr")
set_fallback_locale("fr")     # None pour désactiver le fallback
```

Elles peuvent aussi être définies au démarrage via le registre Forge :

```python
import core.forge as forge
forge.configure(i18n_default_locale="fr", i18n_fallback_locale="fr")
```

### Comportement de `trans()` avec fallback

```
trans("common.save", locale="en")
 1. cherche dans translations/en.json
 2. si clé absente → cherche dans translations/fr.json  (fallback)
 3. si clé absente partout → retourne "common.save"
```

Le catalogue de la locale demandée doit exister (lève `TranslationCatalogError` sinon).
Le catalogue de fallback absent est ignoré silencieusement.

### Utilisation dans les templates Jinja

`trans()` est disponible comme global Jinja dans tous les templates Forge et utilise la même langue par défaut :

```html
{{ trans("common.save") }}           {# → Enregistrer #}
{{ trans("validation.required") }}   {# → Ce champ est obligatoire. #}
{{ trans("cle.inconnue") }}          {# → cle.inconnue #}
{{ trans("common.save", locale="fr") }}
```

### Commandes CLI

#### `forge i18n:init`

Initialise la structure i18n d'un projet Forge :

```bash
forge i18n:init
```

Crée `translations/` et `translations/fr.json` avec le catalogue français minimal si absents.
**Idempotente** : ne modifie rien si les fichiers existent déjà.
Ne crée pas `en.json` ni `es.json`.

#### `forge i18n:check`

Vérifie les catalogues présents dans `translations/` :

```bash
forge i18n:check
```

**Vérifie :**

- présence de `translations/`
- présence de `translations/fr.json`
- validité JSON de chaque `*.json` trouvé
- chaque catalogue est un objet JSON
- toutes les clés sont des chaînes non vides
- toutes les valeurs sont des chaînes non vides
- les clés utilisent la notation pointée (`common.save`, `crud.create`…)
- aucune clé métier évidente (`commune`, `sejour`, `hebergement`, `reservation`…)

**Ne fait pas :**

- ne crée aucun fichier
- ne corrige rien automatiquement
- ne synchronise pas les catalogues

**Clés publiques dans `translations/fr.json`** — les générateurs de pages
publiques (`make:public-page`, `make:public-list`, `make:public-show`,
`make:public-form`, `make:public-contact`) utilisent `{{ trans('key') }}`
pour les chaînes génériques. Ces clés sont présentes dans `translations/fr.json` :
`public.page.generated`, `public.list.empty`, `public.show.back`,
`public.show.not_found`, `public.form.submit`, `public.form.success`,
`public.contact.title`, `public.contact.intro`, `public.contact.coordinates`,
`public.contact.address`, `public.contact.email_label`, `public.contact.phone`,
`public.contact.address_placeholder`. Si une clé est absente du catalogue,
`trans()` retourne la clé elle-même — la page reste fonctionnelle. Les noms
d'entités et les routes ne sont pas traduits automatiquement.

**Exemples de sortie :**

```
[OK]         Dossier translations présent
[OK]         Catalogue fr.json valide — 18 clés vérifiées
```

En cas d'erreur :

```
[ERREUR]     translations/fr.json : JSON invalide
[ERREUR]     translations/fr.json : la clé "commonsave" n'utilise pas la notation pointée
```

Retourne `0` si tout est valide, `1` si au moins une erreur est détectée.

### `make:crud` et i18n

`forge make:crud` génère des templates qui utilisent les clés i18n génériques via `trans()` :

| Clé Jinja générée | Clé catalogue |
|---|---|
| `{{ trans('common.save') }}` | Enregistrer |
| `{{ trans('common.cancel') }}` | Annuler |
| `{{ trans('common.back') }}` | Retour |
| `{{ trans('common.search') }}` | Rechercher |
| `{{ trans('crud.show') }}` | Voir |
| `{{ trans('crud.edit') }}` | Modifier |
| `{{ trans('crud.delete') }}` | Supprimer |
| `{{ trans('crud.empty') }}` | Aucun élément à afficher. |
| `{{ trans('crud.actions') }}` | Actions |

Les noms d'entités et de champs (`Contact`, `nom`, `email`…) **ne sont pas traduits automatiquement** — les traductions métier appartiennent à l'application, pas au core Forge.

`translations/fr.json` fournit les clés génériques de base.
`forge i18n:check` permet de vérifier les catalogues.

### Limites actuelles

- aucun catalogue `translations/en.json` ou `translations/es.json` n'est encore fourni ;
- aucune synchronisation automatique des clés entre catalogues n'est faite ;
- les traductions métier (noms d'entités, champs) restent à la charge de l'application.

</details>

<details markdown="1" id="coremail">
<summary><code>core.mail</code> - Mail SMTP minimal</summary>

`core.mail` fournit une brique mail générique avec transports interchangeables, rendu de templates et journalisation optionnelle. Elle ne contient pas de logique métier.

### API

| API | Description |
|---|---|
| `MailMessage` | Message texte ou HTML avec alternative texte, protection injection headers. |
| `Mailer.from_config()` | Construit un expéditeur depuis `core.forge` (transport configurable). |
| `Mailer.send(message, *, message_type, related_entity, related_id)` | Envoie via le transport actif, journalise si `MAIL_LOG_ENABLED=true`. |
| `MailTemplateRenderer` | Rendu Jinja2 de templates `*_subject.txt` / `*_text.txt` / `*_html.html`. |
| `MailLogger` | Journalisation dans `mail_log` (sans corps du message). |
| `FakeTransport` | Transport mémoire pour les tests unitaires. |
| `MailConfigurationError` | Configuration incomplète ou incohérente. |
| `MailSendError` | Erreur SMTP pendant l'envoi. `Mailer.send()` l'intercepte en `TransportResult(success=False)`. |

> `SMTPMailer` (`core/mail/smtp.py`) est conservé provisoirement pour compatibilité.
> Le système recommandé depuis Forge 1.2 est `Mailer + SmtpTransport`.

### Exemple

```python
from core.mail import Mailer, MailMessage

message = MailMessage(
    subject="Bienvenue",
    to="test@example.com",
    body_text="Bonjour",
    body_html="<p>Bonjour</p>",
)
result = Mailer.from_config().send(message)
```

En développement, `MAIL_ENABLED=false` est la valeur par défaut — aucun mail ne part sans activation explicite.
Les destinataires `bcc` sont utilisés dans l'enveloppe SMTP mais ne sont pas ajoutés aux en-têtes visibles du message.

</details>

<details markdown="1" id="corevalidation">
<summary><code>core.validation</code> - Décorateurs de validation des entités</summary>

Ces décorateurs vivent dans `core/validation/decorators.py` et lèvent `ValidationError`, l'exception centrale de validation.

### Décorateurs autorisés

| Décorateur | Description |
|---|---|
| `typed(expected_type)` | Vérifie le type Python sans transformation implicite. `bool` est refusé pour `int`. |
| `nullable` | Marque explicitement une propriété nullable. |
| `not_empty` | Refuse les chaînes vides ou blanches. |
| `min_length(size)` | Longueur minimale d'une chaîne. |
| `max_length(size)` | Longueur maximale d'une chaîne. |
| `min_value(limit)` | Valeur numérique minimale. |
| `max_value(limit)` | Valeur numérique maximale. |
| `pattern(regex)` | Expression régulière avec `fullmatch`. |

### Exemple

```python
from core.validation.decorators import max_length, not_empty, typed

class ContactBase:
    @property
    def nom(self):
        return self._nom

    @nom.setter
    @typed(str)
    @not_empty
    @max_length(100)
    def nom(self, value):
        self._nom = value
```

Les fichiers générés `*_base.py` peuvent utiliser ces décorateurs. La classe métier manuelle reste le bon endroit pour ajouter du comportement applicatif.

</details>

<details markdown="1" id="forge-cli">
<summary><code>forge</code> CLI - Commandes officielles</summary>

L'interface officielle est la commande `forge`. La version actuelle est `2.5.0`.

### Commandes

| Commande | Rôle |
|---|---|
| `forge --version` | Affiche la version CLI. |
| `forge new NomProjet [--ref REF]` | Crée un projet depuis le dernier tag stable. `--ref main` est explicite pour le développement. |
| `forge make:entity NomEntite` | Crée le JSON canonique d'une entité. |
| `forge make:crud NomEntite [--dry-run]` | Génère contrôleur, vues et routes CRUD, avec champs relationnels `many_to_one`, formulaires `many_to_many` côté source, affichage `many_to_many` dans list/show côté source et partials internes de liste. |
| `forge make:public-page <nom>` | Génère une page publique simple, son template, son contrôleur et sa route dédiée. |
| `forge make:public-list <Entite>` | Génère une liste publique depuis une entité existante, séparée du CRUD admin. Intègre une colonne image si l'entité déclare un média `field: image`. |
| `forge make:public-show <Entite>` | Génère une fiche publique depuis une entité existante, séparée du CRUD admin. Affiche les médias déclarés en lecture seule (image, galerie, fichier). |
| `forge make:public-form <Entite>` | Génère un formulaire public (GET `/new` + POST `/`) avec validation serveur, INSERT SQL visible et redirect flash. Non destructif sur un contrôleur public existant. |
| `forge make:public-contact` | Génère une page contact publique statique (`/contact`) avec coordonnées et adresse placeholder. Aucun traitement serveur, aucun envoi de mail. |
| `forge make:relation` | Assistant de création de relation. |
| `forge sync:entity NomEntite` | Régénère `*_base.py` et SQL depuis le JSON. |
| `forge sync:relations` | Régénère `relations.sql` depuis `relations.json`, y compris les tables pivot `many_to_many` simples ou enrichies via `pivot_fields`. |
| `forge sync:landing [--check]` | Synchronise ou vérifie la landing. |
| `forge upload:init` | Prépare les dossiers d'uploads. |
| `forge media:init` | Prépare les dossiers de variantes d'images. |
| `forge auth:init` | Crée ou préserve les SQL Auth/User optionnels. |
| `forge auth:doctor` | Vérifie les modules, contrats et SQL optionnels Auth/User sans accès base. |
| `forge auth:status` | Affiche les briques Auth/User disponibles dans le projet. |
| `forge auth:list-sql` | Liste les fichiers SQL Auth/User optionnels connus sans les appliquer. |
| `forge auth:user:create --email <email> [--password ...\|--password-prompt]` | Crée un utilisateur local avec mot de passe hashé. |
| `forge auth:user:list` | Liste les utilisateurs locaux sans afficher de secret. |
| `forge auth:user:show (--id <id>\|--email <email>)` | Affiche un utilisateur local sans afficher de secret. |
| `forge auth:user:disable (--id <id>\|--email <email>)` | Désactive un compte utilisateur local (is_active=FALSE) sans le supprimer. |
| `forge auth:user:enable (--id <id>\|--email <email>)` | Réactive un compte utilisateur local (is_active=TRUE). |
| `forge auth:user:password (--id <id>\|--email <email>) [--password ...\|--password-prompt]` | Change le mot de passe d'un utilisateur local (hash Argon2id). Aucun secret affiché. |
| `forge auth:user:role:add (--id <id>\|--email <email>) --role <role>` | Attribue un rôle RBAC existant à un utilisateur. |
| `forge auth:user:role:remove (--id <id>\|--email <email>) --role <role>` | Retire une association `user_roles`. |
| `forge auth:user:roles (--id <id>\|--email <email>)` | Liste les rôles RBAC attribués à un utilisateur. |
| `forge mail:init` | Crée templates mail, dossier log et SQL `mail_log`. |
| `forge mail:doctor` | Vérifie la configuration mail. |
| `forge mail:test --to <email>` | Envoie un message de test via le transport configuré. |
| `forge mail:render <tpl> [--context f.json]` | Affiche le rendu d'un template sans envoyer. |
| `forge mail:logs [--limit N]` | Affiche les derniers enregistrements de `mail_log`. |
| `forge build:model` | Régénère les modèles. |
| `forge check:model` | Vérifie la cohérence des modèles. |
| `forge db:init` | Prépare l'environnement MariaDB et la table technique `forge_migrations`. |
| `forge db:apply` | Applique le SQL généré. |
| `forge migration:status` | Affiche l'état des migrations SQL versionnées, sans les appliquer. |
| `forge migration:make` | Crée un fichier SQL de migration vide dans `mvc/migrations/`. |
| `forge migration:make <nom> --from-diff <Entite>` | Génère une migration prudente depuis le diff d'une entité. |
| `forge migration:diff --entity <Entite>` | Compare en lecture seule une entité JSON avec les colonnes MariaDB. |
| `forge migration:apply` | Applique les migrations SQL locales en attente. |
| `forge routes:list` | Liste les routes de l'application. |
| `forge deploy:init` | Prépare les fichiers de déploiement. |
| `forge deploy:check` | Vérifie la configuration de déploiement. |
| `forge starter:list` | Liste les starter apps. |
| `forge starter:build` | Reconstruit une starter app. |
| `forge module:list [--path modules]` | Liste les modules Forge locaux sans rien installer. |
| `forge module:install <nom> [--path modules] [--dry-run]` | Enregistre déclarativement un module dans `forge_modules.json`. |
| `forge module:files <nom> [--dry-run]` | Copie prudemment les fichiers déclarés d'un module déjà installé. |
| `forge module:routes <nom> [--dry-run]` | Génère `mvc/routes_<nom>.py` et affiche les lignes à ajouter dans `mvc/routes.py`. Ne modifie jamais `mvc/routes.py`. |
| `forge doctor` | Lance les diagnostics projet (lecture seule, sans modification). |
| `forge project:check` | Vérifie la conformité structurelle et contractuelle du projet (CI-friendly, code de sortie fiable). |
| `forge project:audit` | Produit un rapport d'audit détaillé non destructif (structure, config, entités, routes, templates, modules, migrations, docs, tests). |
| `forge help` | Affiche l'aide. |

### forge project:check — vérification structurelle

`forge project:check` vérifie qu'un projet Forge respecte les conventions contractuelles de Forge 1.x. Elle est plus stricte que `forge doctor` et peut être utilisée avant un commit, avant une release locale ou dans une CI.

**Différence avec `forge doctor` :**

| | `forge doctor` | `forge project:check` |
|---|---|---|
| Objectif | état général du projet | conformité structurelle |
| Zones optionnelles | acceptées (SKIP/WARN) | certaines absences = FAIL |
| Modules manquants | WARN | FAIL |
| Templates manquants | SKIP | FAIL |
| Utilisable en CI | non recommandé | oui |
| Code de sortie 1 | si FAIL | si FAIL |

**Ce que `forge project:check` vérifie :**

| Famille | FAIL si… | WARN si… |
|---|---|---|
| Structure | `app.py`, `config.py`, `mvc/`, `mvc/routes.py`, `mvc/controllers/`, `mvc/views/`, `mvc/entities/` absent | — |
| Configuration | `env/example` absent | `env/dev` absent |
| Entités | `relations.json` absent ou invalide, JSON d'entité absent ou invalide | — |
| Routes | `mvc/routes.py` absent, erreur de syntaxe Python | `mvc/routes.py` vide |
| Templates | `mvc/views/` absent | aucun `.html` trouvé |
| Modules | `forge_modules.json` invalide, source déclarée absente | — |
| Migrations | — | noms non conformes, fichiers vides |

`forge project:check` doit être lancé depuis la racine d'un projet Forge. Si `app.py` et `mvc/` sont absents, la commande échoue immédiatement avec un message explicite.

Code de sortie : `0` si aucun FAIL, `1` si au moins un FAIL. Les WARN n'influencent pas le code de sortie.

### forge project:audit — rapport d'audit détaillé

`forge project:audit` produit un rapport d'audit complet d'un projet Forge. Contrairement à `project:check` (strict, CI-ready), `project:audit` est informatif et distingue les problèmes bloquants, les avertissements et les observations neutres (INFO).

**Différence entre les trois commandes de diagnostic :**

| | `forge doctor` | `forge project:check` | `forge project:audit` |
|---|---|---|---|
| Objectif | Diagnostic environnement | Conformité contractuelle | Rapport détaillé |
| Tolérance | Tolérant (SKIP possibles) | Strict (FAIL = non-conforme) | Multi-niveaux (OK/WARN/FAIL/INFO) |
| Code de sortie 1 | Si FAIL | Si FAIL | Si FAIL |
| Connexion externe | MariaDB | Non | Non |
| Usage typique | Aide immédiate | Avant commit / CI | Avant release / revue |

**Familles auditées :**

| Famille | Ce qui est audité |
|---|---|
| Structure | `app.py`, `config.py`, `mvc/` et sous-dossiers, `static/` (optionnel) |
| Configuration | `env/example`, `env/dev`, clés essentielles |
| Entités | `relations.json`, fichiers JSON, `.sql` et `_base.py` générés |
| Routes | Présence, syntaxe, déclaration de `router` |
| Templates | Présence et nombre de fichiers `.html`, template `base.html` |
| Modules | `forge_modules.json`, sources déclarées, modules non déclarés |
| Migrations | Noms conformes (`YYYYMMDDHHMMSS_nom.sql`), fichiers vides, timestamps dupliqués |
| Documentation | Présence du README |
| Tests | Présence du dossier `tests/` et des fichiers `test_*.py` |

Code de sortie : `0` si aucun FAIL (même avec des WARN ou INFO), `1` si au moins un FAIL ou si lancé hors projet Forge.

`forge project:audit` ne modifie aucun fichier. Il ne corrige rien automatiquement.

### forge doctor — détails

`forge doctor` est une commande de lecture seule. Elle ne modifie aucun fichier.

Résultats possibles : `OK`, `WARN`, `FAIL`, `SKIP`. Un `FAIL` retourne un code de sortie 1. Un `WARN` ne bloque pas.

| Famille | Ce qui est vérifié |
|---|---|
| Python | Version >= {{python_min}} |
| Environnement | Présence et cohérence de `env/example` + `env/dev`, clés requises |
| Structure MVC | `mvc/`, `mvc/routes.py`, `mvc/entities/`, `mvc/views/`, `mvc/controllers/` |
| Entités | Validité des JSON d'entités dans `mvc/entities/` |
| Migrations | `mvc/migrations/*.sql` : noms conformes `YYYYMMDDHHMMSS_nom.sql`, fichiers non vides |
| i18n | `translations/*.json` : présence et lisibilité des catalogues (optionnel) |
| Templates | Présence de fichiers `.html` dans `mvc/views/` |
| Modules | Cohérence de `forge_modules.json` : JSON valide, sources déclarées présentes |
| Certificats SSL | Présence des fichiers `SSL_CERTFILE` et `SSL_KEYFILE` |
| Node.js / npm | Présence de `npm` (optionnel, Tailwind uniquement) |
| Base de données | Connexion MariaDB avec les credentials applicatifs |
| MFA (opt-in) | Détecte les indices d'usage MFA dans le projet — WARN si `forge_mvc_mfa` absent |

Ce que `forge doctor` ne vérifie pas : contenu des templates, syntaxe SQL, validité des migrations appliquées, configuration Auth/User (voir `forge auth:doctor`), configuration mail (voir `forge mail:doctor`).

**Diagnostic MFA (opt-in)** — `forge doctor` détecte les indices d'usage MFA dans un projet (nom de contrôleur, routes, imports). Si des indices sont trouvés mais que le module `forge_mvc_mfa` n'est pas installé, un `WARN` non bloquant est émis. MFA est une brique opt-in/source-only : `forge-mvc` (core) n'inclut ni `forge_mvc_mfa` ni `pyotp` dans ses dépendances runtime. Pour supprimer le warning, installez les dépendances du module MFA (`pip install forge-mvc-mfa`) ou retirez le flux MFA du projet.

`forge auth:init` crée ou préserve les fichiers SQL suivants sans les appliquer :
`users.sql`, `auth_tokens.sql`, `auth_mfa_factors.sql`,
`auth_mfa_recovery_codes.sql`, `user_roles.sql`, `auth_audit_log.sql` et
`auth_rate_limit_attempts.sql`.

Les commandes Auth dispatchables dans cette version sont celles listées
ci-dessus. Les commandes `auth:user:role:*` manipulent uniquement les
associations `user_roles` et ne créent ni rôle, ni permission, ni utilisateur.
Aucune commande de consultation audit/rate limit n'est exposée par la CLI
actuelle.

### Format de l'aide CLI

`forge help`, `forge --help`, `forge -h` et `forge` (sans argument) affichent la même aide groupée par famille. L'aide est générée par `forge_cli/help.py` (`build_help(version)`).

Familles présentées : Projet, Entités, Pages publiques, Base de données, Starters et modules, Auth / Sécurité, Mail, Médias et JavaScript, Déploiement.

La différence entre `forge doctor` (diagnostic large, tolérant, lecture seule) et `forge project:check` (contrôle strict des conventions, CI-ready) est expliquée dans l'aide générale.

### Format des erreurs CLI et conseils de récupération

Toutes les erreurs de dispatch CLI suivent la convention :

```
Erreur : <message>
Conseil : <suggestion>   # optionnel
```

- Le message et le conseil sont écrits sur **stderr**.
- Le code de sortie est **1** (erreur utilisateur) sauf cas spéciaux (ex. 130 pour `Ctrl+C`).
- `[ERREUR]` (tag de générateur) est distinct : il appartient aux sorties de génération d'artefacts, pas aux erreurs de dispatch.

Les conseils de récupération sont présents pour les erreurs les plus fréquentes :

| Situation | Conseil fourni |
|---|---|
| Commande inconnue | `forge help` pour la liste des commandes |
| Argument manquant (`new`, `make:entity`, `make:crud`, `starter:build`) | Exemple concret avec nom plausible |
| `forge new --ref` sans valeur | Exemple avec branche |
| `forge new --profile` sans valeur | Liste des profils disponibles |
| `forge project:check` hors projet | `forge new <NomProjet>` pour créer un projet |
| `forge routes:list` avec arguments en trop | Usage correct sans argument |

Les conseils enrichissent la sortie mais **ne corrigent jamais automatiquement** le projet.

### Exemples

```bash
forge --version
forge new GestionVentes
forge new ForgeDev --ref main
```

```bash
forge make:entity Contact
forge sync:entity Contact
forge make:crud Contact --dry-run
forge make:crud Contact
```

```bash
forge check:model
forge db:init
forge db:apply
forge routes:list
```

</details>

<details markdown="1" id="forgeclieentities">
<summary><code>forge_cli.entities</code> - Génération et validation des entités</summary>

Cette partie suit la doctrine décrite dans l'[architecture des entités](../entity_architecture.md).

### Doctrine générée

| Source | Statut | Règle |
|---|---|---|
| `mvc/entities/<entite>/<entite>.json` | Canonique | Décrit l'entité, ses champs et contraintes. |
| `mvc/entities/<entite>/<entite>_base.py` | Régénérable | Classe Python générée avec validation. |
| `mvc/entities/<entite>/<entite>.sql` | Régénérable | SQL de table. |
| `mvc/entities/<entite>/<entite>.py` | Manuel | Classe métier, jamais écrasée si elle existe. |
| `mvc/entities/<entite>/__init__.py` | Manuel | Jamais régénéré s'il existe. |
| `mvc/entities/relations.json` | Canonique | Relations globales. |
| `mvc/entities/relations.sql` | Régénérable | Contraintes de clés étrangères et tables pivot `many_to_many`, y compris colonnes `pivot_fields`. |

### Validation importante

| Sujet | Règle actuelle |
|---|---|
| Noms | `snake_case` pour dossiers, tables et champs Python. Colonnes SQL en `PascalCase`. |
| Mots réservés SQL | Les noms comme `order`, `user`, `group` ou `select` sont refusés. |
| Relations | Les relations `many_to_one` et `many_to_many` sont supportées. `sync:relations` génère les pivots simples ou enrichis via `pivot_fields`. `make:crud` génère `RelationField` pour les `many_to_one`, un `LEFT JOIN` avec alias `<fk>_label` dans les requêtes de liste, un `<select multiple>` côté source pour les formulaires `many_to_many`, et l'affichage texte des libellés liés dans list/show côté source. |
| Clés primaires | Les entités sont limitées à une clé primaire simple. |
| Types SQL de FK | Les types SQL normalisés doivent être compatibles. `INT` vers `BIGINT` ou `INT UNSIGNED` est refusé. |
| Génération | Un JSON invalide bloque la génération. |

### Exemple JSON entité

```json
{
  "entity": "Contact",
  "table": "contact",
  "primary_key": {
    "name": "contact_id",
    "sql": "ContactId",
    "python_type": "int",
    "sql_type": "INT",
    "auto_increment": true
  },
  "fields": [
    {
      "name": "prenom",
      "sql": "Prenom",
      "python_type": "str",
      "sql_type": "VARCHAR(100)",
      "nullable": false,
      "constraints": {
        "not_empty": true,
        "max_length": 100
      }
    }
  ]
}
```

### Exemple relation

```json
{
  "relations": [
    {
      "name": "contact_ville",
      "type": "many_to_one",
      "from_entity": "contact",
      "from_field": "ville_id",
      "to_entity": "ville",
      "to_field": "ville_id",
      "on_delete": "RESTRICT",
      "on_update": "CASCADE"
    }
  ]
}
```

### Exemples de cycle complet

```bash
forge make:entity Ville
forge make:entity Contact
forge sync:entity Ville
forge sync:entity Contact
forge make:relation
forge sync:relations
forge check:model
```

```bash
forge db:apply
forge make:crud Contact
```

La génération CRUD applique la correction de robustesse sur les identifiants invalides : un `id` de route non entier est traité comme une ressource introuvable.

### Pages publiques simples

`forge make:public-page accueil` génère une page publique indépendante du CRUD
admin :

```text
mvc/views/public/accueil.html
mvc/controllers/public_pages_controller.py
mvc/routes.py
```

Le template étend `layouts/public.html`, définit les blocs publics stables
`title` et `content`, et affiche un contenu minimal. Le layout public expose
aussi le bloc `scripts` pour les ajouts explicites de projet. La commande ajoute
une route publique prudente `/accueil` et un handler dans
`PublicPagesController`.

La génération est non destructive : un template existant est conservé, une route
existante n'est pas dupliquée et le contrôleur est complété seulement quand
l'insertion est sûre. Cette commande ne génère ni liste publique, ni fiche, ni
formulaire, ni média, ni HTMX, ni JavaScript personnalisé. Elle ne remplace pas
le CRUD admin et prépare seulement les pages publiques génériques de la Phase 6.

Convention publique stabilisée :

```text
mvc/views/layouts/public.html  # layout visiteur
mvc/views/public/              # pages publiques générées
mvc/views/components/          # composants Jinja génériques réutilisables
```

Le layout public charge Tailwind et reste indépendant de HTMX, Alpine.js et i18n.
Les pages publiques générées ne doivent pas exposer un CRUD admin brut aux
visiteurs.

### Listes publiques simples

`forge make:public-list Hebergement` génère une liste publique depuis une entité
existante :

```text
mvc/views/public/hebergements/index.html
mvc/controllers/public_hebergements_controller.py
mvc/routes.py
```

La route publique générée est `/hebergements`. Le template étend
`layouts/public.html`, utilise les blocs `title`, `content` et `scripts`, affiche
un titre, un tableau simple et un état vide. Le contrôleur contient une requête
SQL lisible de type `SELECT ... FROM table ORDER BY id DESC`, sans ORM, sans
recherche, sans filtre et sans pagination.

La liste publique affiche les champs simples déclarés dans l'entité et exclut
les champs techniques ou sensibles évidents comme `id`, `created_at`,
`updated_at`, `password`, `password_hash`, `token` et `secret`. Les champs de
relation simples en `_id` et les relations complexes ne sont pas traités.

Si l'entité déclare au moins un média `field: image` dans sa configuration
`media`, la liste ajoute une colonne miniature. Le contrôleur appelle
`get_cover_media` pour chaque ligne après la requête principale.

Cette commande ne génère pas de formulaire public, pas de back-office, pas de
bouton modifier/supprimer et n'expose aucune route CRUD admin. HTMX, Alpine.js
et i18n restent optionnels et ne sont pas imposés.

### Fiches publiques simples

`forge make:public-show Hebergement` génère une fiche publique de consultation
depuis une entité existante :

```text
mvc/views/public/hebergements/show.html
mvc/controllers/public_hebergements_controller.py
mvc/routes.py
```

La route publique générée est `/hebergements/{id}`. Le template étend
`layouts/public.html`, utilise les blocs `title`, `content` et `scripts`, affiche
un titre, les champs publics simples et un lien de retour vers `/hebergements`.
Si la ligne demandée n'existe pas, le contrôleur renvoie `BaseController.not_found()`.

Le contrôleur public est créé si nécessaire ou complété quand la classe attendue
existe déjà. La requête SQL reste visible et simple :
`SELECT ... FROM table WHERE id = ?`. Il n'y a pas d'ORM, pas de jointure, pas de
recherche, pas de filtre, pas de pagination et pas de slug public.

Si l'entité déclare des médias dans sa configuration `media`, la fiche affiche
chaque entrée en lecture seule dans l'ordre de la déclaration. Le contrôleur
appelle `get_cover_media` pour les éléments uniques et `list_media_for_entity`
pour les galeries.

La fiche publique exclut les mêmes champs techniques ou sensibles que la liste
publique, ainsi que les champs relationnels bruts en `_id`. Elle ne génère aucun
bouton modifier/supprimer, ne crée pas de formulaire, n'expose pas d'upload ni de
suppression de média côté public et ne remplace pas le CRUD admin.

### Médias dans les pages publiques

`forge make:public-list` et `forge make:public-show` intègrent les médias
déclarés dans la clé `media` de la définition JSON d'une entité.

**Comportement liste** — si au moins un média `field: image` est déclaré, la
liste générée ajoute une colonne miniature. Le SELECT inclut `pk AS _entity_id`.
Le contrôleur enrichit chaque ligne avec `get_cover_media(snake, row["_entity_id"], role=...)`.
Les entités sans déclaration `media` ou avec uniquement des fichiers ne reçoivent
aucune colonne supplémentaire.

**Comportement fiche** — chaque entrée `media` produit une section d'affichage :

| Type | Rendu |
|---|---|
| `field: image`, `multiple: false` | `<img>` thumbnail ou URL originale |
| `field: image`, `multiple: true` | grille de `<img>` |
| `field: file`, `multiple: false` | lien vers le fichier |
| `field: file`, `multiple: true` | liste de liens |

Le contrôleur appelle `get_cover_media` pour les éléments uniques et
`list_media_for_entity` pour les galeries. Les imports `forge_mvc_media` sont
ajoutés automatiquement pour les helpers applicatifs. La génération est non destructive : un
contrôleur existant est complété, jamais écrasé.

**Limites strictes** — aucun upload public, aucune suppression publique, aucune
réorganisation, aucun carrousel JavaScript, aucune lightbox, aucun HTMX, aucun
Alpine.js. Ces fonctionnalités restent réservées au CRUD admin ou à des tickets
dédiés.

### Formulaires publics

`forge make:public-form <Entite>` génère un formulaire de saisie public depuis
une entité existante :

```text
mvc/views/public/{plural}/form.html
mvc/controllers/public_{plural}_controller.py
mvc/routes.py
```

Exemple : `forge make:public-form DemandeSejour` génère :

- `mvc/views/public/demande_sejours/form.html`
- `mvc/controllers/public_demandes_sejours_controller.py`
- Routes : `GET /demande_sejours/new` et `POST /demande_sejours`

**Champs inclus** — les champs non sensibles de l'entité (hors clé primaire,
clés étrangères `_id`, `created_at`, `updated_at`, `password*`, `token*`,
`secret*`, `is_admin`, `is_active`, `email_verified_at`, `last_login_at`).

**Types d'input détectés automatiquement** — `textarea` (sql TEXT), `checkbox`
(bool), `number` (int/float), `date`, `datetime-local`, `email` (nom contenant
`email`), `url` (nom contenant `url`, `website` ou `site`), `tel` (nom contenant
`phone`), `text` par défaut.

**Validation serveur** — chaque champ non nullable est marqué `required`. En cas
d'erreur, le formulaire est ré-affiché avec les messages d'erreur et les valeurs
saisies. En cas de succès, un INSERT SQL visible est exécuté et l'utilisateur est
redirigé vers le formulaire vide avec un message flash.

**Non destructif** — si le contrôleur public existe déjà, les méthodes `new()` et
`create()` ainsi que les constantes `INSERT_PUBLIC_FORM` et `FORM_FIELDS` sont
ajoutées sans toucher aux méthodes existantes.

**Limites strictes** — pas d'envoi d'email, pas de captcha, pas de workflow,
pas d'upload, pas de HTMX, pas d'Alpine.js, pas d'exposition de routes admin,
pas de pagination, pas d'i18n.

### Page contact publique

`forge make:public-contact` génère une page contact statique sans argument :

```text
mvc/views/public/contact.html
mvc/controllers/public_pages_controller.py
mvc/routes.py
```

La route générée est `GET /contact`. La méthode `contact()` est ajoutée à
`PublicPagesController` (le même contrôleur que `make:public-page`). Le template
contient un titre, une introduction, un bloc coordonnées (lien mailto + téléphone)
et un bloc adresse — tous avec des valeurs placeholder à remplacer manuellement.

La commande est non destructive et idempotente : elle ne recrée pas la page si
elle existe déjà, n'ajoute pas la route si elle est déjà présente, et ne modifie
pas les méthodes existantes du contrôleur.

**Ce que cette commande ne fait pas :** envoi d'email, traitement de formulaire,
création d'entité ou de table, captcha, HTMX, Alpine.js, i18n forcé. Pour un
formulaire de contact traité côté serveur, utiliser `make:public-form`.

### Partials CRUD générés

`forge make:crud` génère maintenant la page liste complète et trois partials
internes :

```text
mvc/views/<entite>/index.html
mvc/views/<entite>/_table.html
mvc/views/<entite>/_pagination.html
mvc/views/<entite>/_results.html
```

`index.html` reste la page HTML classique : elle étend le layout, affiche le
titre, le formulaire GET de recherche, les filtres, puis inclut `_results.html`
dans un conteneur stable `#crud-results`.
`_table.html` contient la table, les colonnes classiques, les colonnes
relationnelles déjà supportées, les actions, les formulaires de suppression et
les états vides contextuels.
`_pagination.html` contient les liens Précédent / Suivant et conserve `q`, les
filtres, `sort` et `direction`. Ces liens restent de vrais liens `href` et
reçoivent aussi les attributs HTMX progressifs `hx-get`,
`hx-target="#crud-results"`, `hx-swap="innerHTML"` et `hx-push-url="true"`.
`_results.html` combine `_table.html` et `_pagination.html` pour fournir un
fragment unique quand la liste est rafraîchie par HTMX.

Le formulaire de recherche et de filtre reste un formulaire `GET` standard.
Il reçoit aussi les attributs HTMX progressifs `hx-get`, `hx-target="#crud-results"`,
`hx-swap="innerHTML"` et `hx-push-url="true"`. HTMX n'est pas obligatoire : sans
HTMX chargé, la recherche/les filtres rechargent la page complète comme avant.
Quand l'en-tête `HX-Request: true` est présent, le contrôleur rend uniquement
`_results.html`, sans layout complet. Aucun JavaScript personnalisé, aucune
recherche live `keyup` et aucun `debounce` ne sont générés.

**Lien Réinitialiser**

Un lien « Réinitialiser » est généré dans le formulaire. Il apparaît dès que
`pagination.q` est non vide **ou** que `pagination.filters` contient au moins
un filtre actif :

```html
{% if pagination.q or pagination.filters %}
<a href="/contacts"
   hx-get="/contacts" hx-target="#crud-results" hx-swap="innerHTML" hx-push-url="true"
   class="...">Réinitialiser</a>
{% endif %}
```

Le lien a un `href` classique (fallback sans HTMX) et les mêmes attributs HTMX
que le formulaire. Cliquer dessus revient à l'URL de base du CRUD, sans paramètre.

Les formulaires de suppression restent en `method="post"` avec le champ CSRF ;
ils reçoivent aussi `hx-post`, `hx-target="#crud-results"`, `hx-swap="innerHTML"`
et `hx-confirm` pour remplacer uniquement les résultats quand HTMX est disponible.
Forge n'utilise pas `hx-delete` dans le CRUD généré.

### Listes CRUD générées : recherche et pagination

Les vues liste générées par `make:crud` embarquent une recherche texte et une pagination.

**Recherche**

Paramètre GET `q` :

```
/contacts?q=roger
```

La recherche utilise `LIKE %q%` sur tous les champs textuels (`VARCHAR`, `CHAR`, `TEXT`). Les champs numériques (`INT`, `DECIMAL`…), les dates, les booléens et les clés étrangères sont exclus. La clause SQL est toujours paramétrée (aucune concaténation directe). Il s'agit d'une recherche simple côté serveur : pas de full-text search, pas de moteur externe et pas de JavaScript personnalisé. HTMX améliore seulement la soumission du formulaire quand il est disponible.

**Pagination**

Paramètre GET `page`, 20 éléments par page dans le CRUD généré :

```
/contacts?page=2
/contacts?q=roger&page=2
```

- `page` absent ou invalide → page 1.
- `page < 1` → page 1.
- `page` trop grand est borné à la dernière page.
- `limit` est fixe dans le CRUD généré ; aucun paramètre GET `limit` n'est généré.
- `q`, les filtres, `sort` et `direction` sont conservés dans les liens Précédent / Suivant.
- Les liens Précédent / Suivant restent des `href` classiques ; sans HTMX, ils rechargent la page complète.
- Avec HTMX, ces liens remplacent uniquement `#crud-results` et poussent l'URL dans l'historique.

Le contrôleur généré utilise la classe commune `core.mvc.view.pagination.Pagination` pour calculer `page`, `nb_pages`, `limit`, `offset`, `has_prev` et `has_next`, puis ajoute les paramètres de liste actifs au contexte :

```python
pagination_state = Pagination(request, total, limit)
pagination = pagination_state.to_dict()
pagination.update({
    "q": q,
    "sort": sort,
    "direction": direction,
    "filters": filters,
})
```

Ce ticket ne fournit pas d'infinite scroll ou de taille de page dynamique.

**Suppression**

Les actions de suppression générées restent des formulaires HTML classiques :

```html
<form method="post" action="/contacts/12/delete?...">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <button type="submit">Supprimer</button>
</form>
```

Le formulaire conserve `method="post"`, l'`action`, le bouton `submit` et le
champ `csrf_token`. Le CRUD généré n'ajoute pas de `_method` car la route
générée reste une route `POST /<ressource>/{id}/delete`; si une application a
un override de méthode personnalisé, il reste à sa charge.

Le même formulaire reçoit une amélioration HTMX progressive :

```html
hx-post="/contacts/12/delete?..."
hx-target="#crud-results"
hx-swap="innerHTML"
hx-confirm="{{ trans('crud.confirm_delete') }}"
```

Sans HTMX, la suppression redirige vers la liste comme avant. Avec
`HX-Request: true`, le contrôleur supprime l'enregistrement, recharge la liste
avec `q`, filtres, `sort`, `direction` et `page`, puis rend `_results.html` sans
layout complet. Aucun JavaScript personnalisé et aucun `hx-delete` ne sont
générés.

**SQL généré (exemple)**

```sql
SELECT * FROM contact
WHERE Nom LIKE ? OR Email LIKE ?
ORDER BY Id DESC
LIMIT ? OFFSET ?
```

### Intégration HTMX CRUD — vue d'ensemble

HTMX est une **amélioration progressive** dans les CRUD générés par Forge. Chaque action reste utilisable sans HTMX ; la bibliothèque améliore seulement l'expérience en remplaçant partiellement la page.

**Cible unique : `#crud-results`**

Tous les éléments HTMX de la liste pointent vers la même cible :

```html
<div id="crud-results">
    {% include "contact/_results.html" %}
</div>
```

La zone `#crud-results` contient `_table.html` + `_pagination.html`. Quand HTMX intercepte une action, il remplace uniquement l'intérieur de cette div — sans rechargement complet.

**Tableau de cohérence**

| Élément | Fallback sans HTMX | Avec HTMX |
|---|---|---|
| Formulaire recherche / filtres | `method="get"` | `hx-get` + `hx-target="#crud-results"` + `hx-push-url="true"` |
| Lien Réinitialiser | `href="/contacts"` | `hx-get="/contacts"` + `hx-push-url="true"` |
| En-têtes de colonnes (tri) | `href="?sort=..."` | `hx-get="?sort=..."` + `hx-push-url="true"` |
| Liens de pagination | `href="?page=..."` | `hx-get="?page=..."` + `hx-push-url="true"` |
| Formulaire suppression unitaire | `method="post"` + `onsubmit="return confirm(...)"` | `hx-post` + `hx-confirm` |
| Formulaire suppression groupée | `method="post"` (toujours) | intentionnellement sans HTMX |

**Convention HTMX cohérente**

Tous les éléments utilisent :
- `hx-target="#crud-results"` — cible unique
- `hx-swap="innerHTML"` — remplacement du contenu
- `hx-push-url="true"` — mise à jour de l'URL (sauf suppression unitaire qui ne pousse pas l'URL)

**Fragment `_results.html`**

Le contrôleur généré renvoie `_results.html` pour les requêtes HTMX et `index.html` pour les navigations classiques :

```python
template = "contact/_results.html" if _is_hx_request(request) else "contact/index.html"
```

`_results.html` n'a pas de `{% extends %}` — c'est un fragment pur.

**Conservation des paramètres**

| Paramètre | Pagination | Tri | Reset |
|---|---|---|---|
| `q` | ✅ conservé | ✅ conservé | ✗ effacé |
| filtres | ✅ conservés | ✅ conservés | ✗ effacés |
| `sort` + `direction` | ✅ conservés | — | ✗ effacés |
| `page` | — | ✗ réinitialisé (retour p.1) | ✗ effacée |

**Pas de JavaScript personnalisé**

Aucun `<script>`, `keyup`, `debounce`, `oninput` ou recherche live n'est généré. Le formulaire de recherche est soumis manuellement (bouton ou touche Entrée).

**Suppression groupée — HTML classique intentionnel**

Le formulaire `bulk-delete-form` est un `POST` classique, sans attributs HTMX. La page de confirmation est une navigation complète. Ce comportement est intentionnel : la suppression groupée est une action lourde qui ne bénéficie pas d'un remplacement partiel.

**Limites restantes**

- Pas de recherche live (pas de `hx-trigger="keyup"`).
- Pas de suppression groupée HTMX.
- Pas d'édition inline.
- Pas de modales HTMX.

### Tri de colonnes CRUD généré

`forge make:crud` génère le tri de colonnes dans les listes. Toutes les colonnes non-PK sont triables par défaut.

**Convention**

Toutes les colonnes non-PK déclarées dans `entity.json` sont triables. Aucune annotation `list.sort: true` n'est nécessaire — la whitelist est construite automatiquement à la génération.

**Paramètres GET**

```
/contacts?sort=nom&direction=asc
/contacts?sort=email&direction=desc
```

- `sort` : nom de champ (non-PK ou PK) ; valeur inconnue ignorée → tri par défaut (PK).
- `direction` : `asc` ou `desc` ; valeur invalide normalisée à `asc`.

**Whitelist SQL `_ALLOWED_SORT`**

Le modèle généré contient une whitelist explicite :

```python
_ALLOWED_SORT = {
    "nom":   "contact.Nom",
    "email": "contact.Email",
    "id":    "contact.Id",
}
_DEFAULT_SORT = "contact.Id"
```

Le SQL utilise toujours `_ALLOWED_SORT.get(sort, _DEFAULT_SORT)` — jamais la valeur brute du paramètre `sort`.

**SQL générée**

```sql
SELECT * FROM contact
ORDER BY contact.Nom ASC
LIMIT ? OFFSET ?
```

Aucune concaténation directe de la valeur utilisateur dans `ORDER BY`.

**Liens de tri**

Les en-têtes de colonnes dans `_table.html` sont des liens qui inversent la direction si la colonne est active :

```html
<a href="?sort=nom&direction=asc"
   hx-get="?sort=nom&direction=asc"
   hx-target="#crud-results"
   hx-swap="innerHTML"
   hx-push-url="true">
    Nom
    {% if pagination.sort == 'nom' %}
    {{ '↑' if pagination.direction == 'asc' else '↓' }}
    {% endif %}
</a>
```

**Conservation des paramètres**

Les liens de tri conservent `q` et les filtres. Ils **réinitialisent la page** (retour à la page 1 lors d'un changement de tri).

**Compatibilité HTMX**

Les liens de tri portent `hx-get`, `hx-target="#crud-results"`, `hx-swap="innerHTML"` et `hx-push-url="true"`. Quand HTMX est disponible, un clic sur un en-tête de colonne met à jour uniquement la zone `#crud-results` sans rechargement complet. Le `href` classique assure le fallback sans HTMX.

**Limites restantes**

- Tri multi-colonnes non supporté.
- Tri relationnel profond non supporté (colonnes de tables liées).
- Tri naturel avancé (ex. tri de nombres stockés en VARCHAR) non supporté.
- Tri configurable ou sauvegardé par utilisateur non supporté.

### Suppression groupée CRUD générée

`forge make:crud` génère une suppression groupée (bulk delete) par cases à cocher, sans JavaScript ni HTMX.

**Flux**

1. L'utilisateur coche une ou plusieurs lignes dans la liste et clique **Supprimer la sélection**.
2. Le formulaire poste vers `POST /contacts/bulk-delete`.
3. Le contrôleur valide les IDs, stocke la liste et affiche une page de confirmation.
4. L'utilisateur confirme via `POST /contacts/bulk-delete/confirm`.
5. La suppression est exécutée en base avec une requête SQL paramétrée `IN (?, ?, ?)`.
6. Redirection vers la liste avec un message flash.

**Routes générées**

```python
g.add("POST", "/bulk-delete",         ContactController.bulk_delete,         name="contact_bulk_delete")
g.add("POST", "/bulk-delete/confirm", ContactController.bulk_delete_confirm,  name="contact_bulk_delete_confirm")
```

**HTML — attribut `form` HTML5**

Les cases à cocher sont dans le `<tbody>` du tableau ; le formulaire `bulk-delete-form` est déclaré en dehors du tableau pour éviter l'imbrication invalide de `<form>` :

```html
<form id="bulk-delete-form" method="post" action="/contacts/bulk-delete">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <button type="submit">Supprimer la sélection</button>
</form>

<table>
    <tbody>
        {% for contact in contacts %}
        <tr>
            <td>
                <input type="checkbox" name="ids" value="{{ contact.Id }}"
                       form="bulk-delete-form">
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

**Validation des IDs (`_parse_bulk_ids`)**

- Accepte une valeur scalaire ou une liste depuis `request.body["ids"]`.
- Filtre les non-entiers et les valeurs `<= 0`.
- Déduplique (via un ensemble `seen`).
- Renvoie une liste vide si aucun ID valide → redirection immédiate sans suppression.

**SQL paramétrée**

```python
placeholders = ", ".join("?" for _ in ids)
cursor.execute(
    "DELETE FROM contact WHERE Id IN (" + placeholders + ")",
    list(ids),
)
```

Aucune concaténation directe des IDs dans la requête SQL.

**CSRF**

Les deux formulaires (`bulk-delete-form` et le formulaire de confirmation) contiennent `{{ csrf_token }}` et sont protégés par le middleware CSRF de Forge.

**RBAC**

Si la définition d'entité contient un bloc `rbac` avec la permission `delete`, le bouton de sélection et les cases à cocher sont conditionnés par `{% if can('contacts.delete') %}`. Sans RBAC, ils sont toujours affichés.

**Pas de JavaScript, pas de HTMX**

La suppression groupée n'utilise ni `<script>`, ni attributs `hx-*`. Elle fonctionne avec du HTML standard.

### Export CSV CRUD généré

`forge make:crud` génère un export CSV minimal sur la route `GET /{plural}/export.csv`.

**Route générée**

```python
g.add("GET", "/export.csv", ContactController.export_csv, name="contact_export_csv")
```

**Modèle — `_EXPORT_LIMIT` et `find_{plural}_for_export`**

```python
_EXPORT_LIMIT = 1000

def find_contacts_for_export(q=None, sort=None, direction="asc", filters=None):
    return find_contacts_paginated(
        q=q, sort=sort, direction=direction,
        limit=_EXPORT_LIMIT, offset=0, filters=filters,
    )
```

L'export réutilise `find_{plural}_paginated` avec les mêmes whitelists (`_ALLOWED_SORT`, `_ALLOWED_FILTERS`) et les mêmes placeholders SQL. La pagination est ignorée ; la limite de 1 000 lignes est une contrainte de sécurité indépendante.

**Colonnes exportées**

- Toutes les colonnes non-PK affichées dans la vue `index`.
- Pour les relations `many_to_one` : la colonne `{field_name}_label` (alias de la jointure SQL), qui affiche le libellé plutôt que la clé étrangère brute.

Le mappage `(en-tête CSV, clé de la ligne)` est calculé à la génération et embarqué comme constante :

```python
_CSV_COLS = [('Nom', 'nom'), ('Client id', 'client_id_label')]
```

**Protection injection CSV**

```python
@staticmethod
def _csv_escape(value: str) -> str:
    if value and value[0] in ("=", "+", "-", "@"):
        return "'" + value
    return value
```

Mitigation OWASP : tout préfixe dangereux est neutralisé par un apostrophe. Le writer utilise `csv.QUOTE_ALL` pour encadrer toutes les cellules de guillemets doubles.

**Headers HTTP**

```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="contacts.csv"
Cache-Control: no-store
```

**RBAC**

Si la permission `index` est déclarée dans la définition d'entité, `export_csv` est protégé par `@require_permission("{entity}.index")`. Sans RBAC, l'export est toujours accessible (comme la liste).

**Lien dans la vue**

Le lien d'export est un `<a href>` classique, sans attributs HTMX, placé entre le formulaire de recherche/filtres et `<div id="crud-results">` :

```html
<div class="mb-2">
    <a href="/contacts/export.csv?q={{ pagination.q | urlencode }}&amp;sort={{ pagination.sort }}&amp;direction={{ pagination.direction }}{% for key, val in pagination.filters.items() %}{% if val %}&amp;{{ key }}={{ val | urlencode }}{% endif %}{% endfor %}"
       class="text-sm text-blue-600 hover:underline">Exporter CSV</a>
</div>
```

Le lien conserve `q`, `sort`, `direction` et les filtres actifs. Il ne conserve pas `page` — l'export couvre l'ensemble filtré sans limite de pagination.

**Pas de HTMX sur l'export**

Un clic sur le lien déclenche un téléchargement de fichier. HTMX intercepterait la réponse et tenterait de l'injecter dans `#crud-results`, ce qui est incorrect. Le lien n'a aucun attribut `hx-*`.

### Listes CRUD générées : états vides contextuels

Les vues liste générées par `make:crud` affichent un état vide standard quand la collection affichée est vide. Le contrôleur transmet aussi `empty_context` au template pour distinguer les absences de résultats dues à une recherche ou à des filtres :

```jinja
{% else %}
<div class="rounded-xl border border-dashed border-gray-300 bg-white p-6 text-center text-gray-600">
    {% if empty_context == "search" %}
    {{ trans('crud.empty_search') }}
    {% elif empty_context == "filters" %}
    {{ trans('crud.empty_filters') }}
    {% elif empty_context == "search_filters" %}
    {{ trans('crud.empty_search_filters') }}
    {% else %}
    {{ trans('crud.empty') }}
    {% endif %}
</div>
{% endif %}
```

Les cas retenus sont :

| Contexte | Condition | Clé i18n |
|---|---|---|
| Liste vide générale | ni recherche active, ni filtre actif | `crud.empty` |
| Recherche sans résultat | `q` non vide après `strip()` | `crud.empty_search` |
| Filtres sans résultat | au moins un filtre réellement actif | `crud.empty_filters` |
| Recherche + filtres sans résultat | `q` actif et filtre actif | `crud.empty_search_filters` |

Les contrôles actifs restent visibles : `pagination.q`, `pagination.filters`, `pagination.sort` et `pagination.direction` sont conservés dans le contexte. Les relations `many_to_many` sans lien affichent `—` dans la liste et `Aucun <EntitéCible>` dans la fiche show. Ce comportement est rendu côté serveur/Jinja : pas de JavaScript, pas de HTMX et pas de composant lourd.

### Listes CRUD générées : tri simple

Les vues liste générées par `make:crud` embarquent un tri simple côté serveur sur les colonnes de l'entité affichées dans la liste.

Paramètres GET :

```text
/contacts?sort=nom&direction=asc
/contacts?sort=email&direction=desc&q=roger&page=2
```

Règles :

- `sort` doit être une clé connue de l'entité générée ;
- `sort` invalide est ignoré et le modèle utilise le tri par défaut ;
- `direction` accepte uniquement `asc` ou `desc` ;
- `direction` invalide revient à `asc` ;
- les liens de tri conservent `q` et les filtres actifs ;
- les liens de pagination conservent `q`, les filtres, `sort` et `direction`.

Le SQL `ORDER BY` n'utilise jamais directement une valeur GET comme nom de colonne. Le modèle généré crée une allowlist :

```python
_ALLOWED_SORT = {"nom": "Nom", "email": "Email", "id": "Id"}
sort_col = _ALLOWED_SORT.get(sort, _DEFAULT_SORT)
sort_dir = "DESC" if direction == "desc" else "ASC"
```

Le nom de colonne est donc choisi depuis l'allowlist, puis concaténé au SQL. C'est la méthode retenue car les noms de colonnes ne peuvent pas être passés proprement comme paramètres SQL `?`.

Limites :

- pas de tri multi-colonnes ;
- pas de tri `many_to_many` ;
- pas de tri relationnel avancé par libellé joint ;
- pas de HTMX ou JavaScript.

### Listes CRUD générées : filtres simples

En plus de la recherche texte `q`, chaque champ non-PK peut exposer un filtre d'égalité via la métadonnée `"list"`.

```json
{
  "name": "statut",
  "sql_type": "VARCHAR(50)",
  "python_type": "str",
  "nullable": false,
  "constraints": {},
  "list": { "filter": true }
}
```

**Types SQL supportés pour `list.filter=true`** :

| Famille | Exemples |
|---|---|
| Chaînes courtes | `VARCHAR(n)`, `CHAR(n)` |
| Entiers | `INT`, `BIGINT`, `SMALLINT`, `TINYINT`, `MEDIUMINT` |
| Booléens | `BOOL`, `BOOLEAN` |

Types **non supportés** (erreur à la validation) : `TEXT`, `DATE`, `DATETIME`, `TIMESTAMP`, `DECIMAL`, `FLOAT`, `DOUBLE`.

**Comportement généré**

- Champ `VARCHAR`/`CHAR`/`INT` → `<input type="text">` dans le formulaire de recherche.
- Champ `BOOL`/`BOOLEAN` → `<select>` avec Tous / Oui / Non.
- Valeur filtrée transmise en GET : `/contacts?statut=actif&actif=1&q=roger&page=2`
- Filtres conservés dans les liens de tri et de pagination via une boucle Jinja2 générique.
- `list.filter=false` ou `"list"` absent → comportement actuel inchangé.

**SQL généré**

Recherche `q` et filtres sont combinés avec `AND` ; chaque groupe de LIKE est entre parenthèses :

```sql
SELECT * FROM contact
WHERE (Nom LIKE ? OR Email LIKE ?)
  AND Statut = ?
ORDER BY Id DESC
LIMIT ? OFFSET ?
```

Toutes les valeurs sont paramétrées (aucune concaténation directe).

**Sécurité — whitelist de colonnes filtrées**

Les noms de colonnes ne peuvent pas être passés comme paramètres SQL `?`. Pour éviter toute injection de colonne, le modèle généré crée une allowlist explicite :

```python
_ALLOWED_FILTERS = {"statut": "Statut", "ville_id": "contact.VilleId"}

for key, val in (filters or {}).items():
    if val is not None and val != "":
        col = _ALLOWED_FILTERS.get(key)
        if col is None:
            raise ValueError(f"Filtre interdit : {key}")
        clauses.append(col + " = ?")
        params.append(val)
```

Une clé absente de `_ALLOWED_FILTERS` lève `ValueError` immédiatement. Le contrôleur généré ne passe que des clés correspondant aux champs déclarés dans le JSON d'entité ; une clé injectée manuellement depuis une URL GET ne peut jamais atteindre la concaténation SQL.

**Compatibilité HTMX et réinitialisation**

Le formulaire de filtres est un formulaire `GET` standard avec une amélioration HTMX progressive. Sans HTMX, le formulaire recharge la page complète. Avec HTMX, le formulaire remplace uniquement la zone `#crud-results` et pousse l'URL dans l'historique.

Un lien « Réinitialiser » est généré dans le formulaire. Il s'affiche dès que `pagination.q` est non vide **ou** que `pagination.filters` contient au moins un filtre actif. Le lien a un `href` classique (fallback sans JavaScript) et les attributs HTMX pour une navigation fluide.

```html
{% if pagination.q or pagination.filters %}
<a href="/contacts"
   hx-get="/contacts" hx-target="#crud-results" hx-swap="innerHTML" hx-push-url="true">
  Réinitialiser
</a>
{% endif %}
```

Aucun JavaScript personnalisé, aucune recherche live et aucun `debounce` ne sont générés.

**Limites des filtres CRUD**

Les filtres générés par `list.filter=true` sont des filtres d'égalité simples. Ne sont pas supportés dans cette version :

- opérateurs avancés : `>`, `<`, `BETWEEN`, `IN`, `NOT IN` ;
- filtres multi-valeurs (checkboxes multiples) ;
- plages de dates ou de nombres ;
- filtres relationnels profonds (jointures imbriquées) ;
- recherche live automatique à la saisie ;
- debounce ou auto-submit sur changement de valeur ;
- filtres sauvegardés en session ou en base ;
- API JSON CRUD avec filtres.

Ces extensions peuvent être ajoutées manuellement dans les fichiers générés.

### Listes CRUD générées : filtres relationnels `many_to_one`

Une relation `many_to_one` déclarée dans `mvc/entities/relations.json` peut aussi être utilisée comme filtre de liste. Aucune nouvelle métadonnée obligatoire n'est nécessaire : la présence de la relation suffit.

Exemple minimal :

```json
{
  "name": "hebergement_commune",
  "type": "many_to_one",
  "from_entity": "Hebergement",
  "to_entity": "Commune",
  "from_field": "commune_id",
  "to_field": "id",
  "foreign_key_name": "fk_hebergement_commune",
  "on_delete": "RESTRICT",
  "on_update": "CASCADE"
}
```

URL :

```text
/hebergements?commune_id=3
/hebergements?q=gite&commune_id=3&page=2
```

Le filtre relationnel est rendu sous forme de `<select>` :

```html
<select name="commune_id">
  <option value="">Tous les Commune</option>
  ...
</select>
```

Forge charge les options depuis l'entité liée avec une fonction modèle explicite. Le libellé est déduit du premier champ textuel disponible (`VARCHAR`, `CHAR`, `TEXT`) ; si l'entité liée n'a aucun champ textuel, Forge utilise la clé primaire comme libellé. Les options sont triées par ce libellé, ou par la clé primaire en fallback.

Le contrôleur généré ignore une valeur vide ou non numérique. La valeur valide est passée comme paramètre SQL, puis combinée avec `q`, les filtres simples, la pagination et le tri.

Le formulaire create/edit continue d'utiliser `RelationField`. Les fonctionnalités plus avancées comme l'autocomplete ou la recherche dans les options ne font pas partie de cette première version.

**Contexte de vue**

`pagination.filters` est toujours un dict (vide si aucun filtre actif) :

```python
pagination = {
    "page": 1, "nb_pages": 3, "total": 55,
    "has_prev": False, "has_next": True,
    "q": "roger", "sort": "", "direction": "desc",
    "filters": {"statut": "actif", "actif": "1"},
}
```

### Métadonnée `form.field`

Chaque champ peut porter une clé optionnelle `"form"` pour contrôler le type de champ généré par `make:crud`.

```json
{
  "name": "email",
  "sql_type": "VARCHAR(254)",
  "python_type": "str",
  "nullable": false,
  "constraints": { "max_length": 254 },
  "form": { "field": "email" }
}
```

| Valeur `form.field` | Champ généré | Import |
|---|---|---|
| `string` | `StringField` | StringField |
| `email` | `EmailField` | EmailField |
| `phone` | `PhoneField` | PhoneField |
| `url` | `UrlField` | UrlField |
| `textarea` | `TextAreaField` | TextAreaField |
| `slug` | `SlugField` | SlugField |
| `date` | `DateField` | DateField |
| `datetime` | `DateTimeField` | DateTimeField |

La validation vérifie aussi la cohérence avec `sql_type` :

| Valeur `form.field` | `sql_type` accepté |
|---|---|
| `string`, `email`, `phone`, `url`, `textarea`, `slug` | `CHAR`, `VARCHAR`, `TEXT`, `TINYTEXT`, `MEDIUMTEXT`, `LONGTEXT` |
| `date` | `DATE` |
| `datetime` | `DATETIME`, `TIMESTAMP` |

**Priorités** : `RelationField` (défini via `relations.json`) est toujours prioritaire sur `form.field`. En l'absence de `form.field`, `make:crud` déduit le champ depuis `python_type` (comportement par défaut inchangé).

**`file` et `image` dans `form.field`** : ces valeurs sont refusées à la validation de `fields[].form.field`. Les médias doivent être déclarés via la clé `"media"` à la racine de l'entité — voir la section *Métadonnée `media`* ci-dessous.

### Métadonnée `media` (déclaration des médias liés)

La clé optionnelle `"media"` au niveau racine d'un `entity.json` déclare les médias liés à une entité. Elle n'ajoute aucune colonne SQL et ne modifie pas `_base.py`. `make:crud` l'utilise pour générer les champs de formulaire et l'upload à la création.

Les médias sont stockés dans la table `media` distincte via `media.entity_name` / `media.entity_id`. La table métier ne contient aucun champ média.

```json
"media": [
  {
    "name": "cover",
    "field": "image",
    "role": "cover",
    "variants": true,
    "multiple": false,
    "required": false,
    "label": "Image principale"
  },
  {
    "name": "brochure",
    "field": "file",
    "role": "brochure",
    "label": "Brochure PDF"
  }
]
```

| Clé | Obligatoire | Valeurs | Défaut |
|---|---|---|---|
| `name` | oui | chaîne non vide, unique | — |
| `field` | oui | `"image"`, `"file"` | — |
| `role` | oui | chaîne non vide, unique | — |
| `variants` | non | `bool` | `false` |
| `multiple` | non | `bool` | `false` |
| `required` | non | `bool` | `false` |
| `label` | non | chaîne | — |

**Règles** : `variants=true` est autorisé uniquement avec `field="image"`. Les doublons `name` et `role` dans une même entité sont refusés à la validation. Voir [docs/media.md](../media.md) pour les détails et la convention de rôles.

### Génération CRUD media (`make:crud` + `media`)

Quand une entité déclare des médias, `make:crud` génère :

- **Formulaire** : un `ImageField` ou `FileField` par entrée `media`, avec label et `required` issus de la déclaration.
- **Vue formulaire** : `enctype="multipart/form-data"` sur le `<form>`, `<input type="file">` avec `accept="image/*"` pour les images.
- **Contrôleur `create`** :
  - Import de `save_upload` depuis `core.uploads` (primitive générique) et `attach_media_to_entity`, `delete_media`, `list_media_for_entity` depuis `forge_mvc_media` (helpers applicatifs).
  - Exclusion des clés média de `form.cleaned_data` avant l'insert SQL.
  - Capture de l'identifiant créé (`cursor.lastrowid`).
  - Pour chaque média soumis : `save_upload(file, category, variants=...)` puis `attach_media_to_entity(saved, entity_name=..., entity_id=created_id, role=..., position=0)`.
- **Contrôleur `update`** (pour `multiple=false`) :
  - Si un nouveau fichier est soumis : `list_media_for_entity` pour trouver l'ancien, `delete_media(..., delete_files=True)` pour le supprimer, puis `save_upload` + `attach_media_to_entity` pour attacher le nouveau.
  - Si `_delete_media_<name>` est coché (sans nouveau fichier) : `delete_media` uniquement, pas d'upload.
  - Sans action : média existant conservé.
  - Les clés média et `_delete_media_*` ne sont jamais écrites dans la table métier.
- **Contrôleurs `show` et `edit`** (pour `multiple=false`) :
  - `get_cover_media(entity_name, entity_id, role=...)` chargé pour chaque entrée, passé au contexte.
  - `show.html` : images affichées avec `thumbnail_url or url` ; fichiers avec un lien.
  - `form.html` : média existant affiché avant le champ upload avec un message de remplacement.

Les médias non soumis (champ vide) sont ignorés silencieusement. La case à cocher `_delete_media_<name>` permet la suppression explicite d'un média existant. `multiple=true` est validé et normalisé mais non exploité comme galerie CRUD (multi-upload, réorganisation).

### Protection RBAC des routes CRUD (`rbac.permissions`)

La clé optionnelle `"rbac"` dans `entity.json` déclare les permissions requises par action CRUD. `make:crud` injecte alors `@require_permission(...)` dans le contrôleur généré.

```json
"rbac": {
  "permissions": {
    "index":  "contacts.view",
    "show":   "contacts.view",
    "create": "contacts.create",
    "store":  "contacts.create",
    "edit":   "contacts.edit",
    "update": "contacts.edit",
    "delete": "contacts.delete"
  }
}
```

Actions acceptées : `index`, `show`, `create` (→ méthode `new`), `store` (→ méthode `create`), `edit`, `update`, `delete` (→ méthode `destroy`). Toute action inconnue déclenche une erreur à la génération. Sans clé `rbac`, le contrôleur est identique à celui généré sans RBAC.

Documentation complète : [RBAC — Contrôle d'accès](../rbac.md).

</details>

---

## Modules officiels (opt-in)

Forge sépare le **core minimal** des **modules officiels** distribués
séparément. Le core couvre les primitives générales (HTTP, routing, sessions,
mots de passe Argon2id, CSRF, uploads, SQL explicite). Les modules officiels
ajoutent des fonctionnalités spécialisées installables via les extras pip.

Chaque module est livré comme paquet PyPI distinct sous le namespace
`forge-mvc-*` et expose son API depuis le namespace Python `forge_mvc_*`.

| Module | Package PyPI | Extra pip | Documentation détaillée |
|---|---|---|---|
| MFA / TOTP | `forge-mvc-mfa` | `[mfa]` | [auth-mfa.md](auth-mfa.md) |
| RBAC | `forge-mvc-rbac` | `[rbac]` | [rbac.md](../rbac.md) |
| Workflow | `forge-mvc-workflow` | `[workflow]` | [workflow.md](workflow.md) |
| Statistiques | `forge-mvc-stats` | `[stats]` | [stats.md](stats.md) |
| Médias applicatifs | `forge-mvc-media` | — | [media.md](../media.md) |

### MFA — `forge-mvc-mfa`

TOTP RFC 6238, codes de récupération, challenge multi-facteur et revalidation.
Inclut l'anti-replay TOTP.

```bash
# Mode source-only en {{forge_version}} et non publié sur PyPI en 1.0
# Voir docs/installation.md#contrat-dinstallation-des-opt-ins
```

Référence détaillée : [auth-mfa.md](auth-mfa.md).

### RBAC — `forge-mvc-rbac`

Rôles, permissions, décorateur `@require_permission`, helpers Jinja
`has_permission()` et politique d'attribution.

> Installation PyPI prospective.
> Les opt-ins `rbac`, `workflow` et `stats` ne sont pas documentés comme installables tant que leur publication coordonnée n'est pas effective.
> La publication est prévue à partir de `1.0.0-beta.5` — voir [contrat d'installation](../installation.md#contrat-dinstallation-des-opt-ins).

Référence détaillée : [rbac.md](../rbac.md).

### Workflow — `forge-mvc-workflow`

États, transitions et helpers d'affichage. Déclaration déclarative de statuts,
fonctions de validation, helpers Jinja2. Aucun callback automatique.

> Installation PyPI prospective.
> Les opt-ins `rbac`, `workflow` et `stats` ne sont pas documentés comme installables tant que leur publication coordonnée n'est pas effective.
> La publication est prévue à partir de `1.0.0-beta.5` — voir [contrat d'installation](../installation.md#contrat-dinstallation-des-opt-ins).

Référence détaillée : [workflow.md](workflow.md).

### Statistiques — `forge-mvc-stats`

Collecte d'événements métier, schéma SQL associé, agrégats et indicateurs
calculés à la demande.

> Installation PyPI prospective.
> Les opt-ins `rbac`, `workflow` et `stats` ne sont pas documentés comme installables tant que leur publication coordonnée n'est pas effective.
> La publication est prévue à partir de `1.0.0-beta.5` — voir [contrat d'installation](../installation.md#contrat-dinstallation-des-opt-ins).

Référence détaillée : [stats.md](stats.md).

### Médias applicatifs — `forge-mvc-media`

Repository, galerie et helpers applicatifs liés à la table `media`.

> Source-only, non publié sur PyPI en `{{forge_version}}`.
> Installe depuis les sources : `pip install -e ./packages/forge-mvc-media/`
> Les générateurs `make:crud --media` et `make:public:list` importent depuis ce module.

Référence détaillée : [media.md](../media.md).

