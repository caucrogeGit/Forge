# Forge — Référence API

Cette référence décrit l'API publique de Forge. Pour les procédures d'installation et les exemples complets, voir le [Guide de démarrage](guide.md).

---

## `core.forge`

Registre centralisé de configuration du noyau. Tous les modules `core/` lisent leurs paramètres via ce registre.

### `configure(**kwargs) -> None`

Configure le noyau Forge. À appeler une seule fois au démarrage.

**Raises :** `KeyError` si une clé est inconnue. Les chemins relatifs sont résolus depuis la racine du projet.

**Clés disponibles :**

| Clé | Défaut | Description |
|-----|--------|-------------|
| `app_name` | `"Forge"` | Nom de l'application |
| `app_env` | `"dev"` | Environnement |
| `views_dir` | `"{racine}/mvc/views"` | Dossier des templates |
| `sql_dir` | `"{racine}/mvc/models/sql"` | Dossier des requêtes SQL applicatives |
| `upload_root` | `"{racine}/storage/uploads"` | Racine des fichiers uploadés |
| `upload_max_size` | `5242880` | Taille maximale d'un fichier uploadé (octets) |
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

### `get(key: str) -> object`

Retourne une valeur de configuration. **Raises :** `KeyError` si la clé est inconnue.

---

## `core.http.request`

### Classe `Request`

Encapsule une requête HTTP entrante. Instanciée automatiquement par le serveur.

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
- `params` et `body` suivent le format `parse_qs` : les valeurs sont des listes. Utiliser `BaseController.body(request)` pour un dict plat.
- `json_body` est vide si le `Content-Type` n'est pas `application/json`.
- `GET`, `HEAD` et `OPTIONS` n'ont pas de body parsé.
- `POST` avec `_method=PUT`, `_method=PATCH` ou `_method=DELETE` est traité comme la méthode indiquée.

---

## `core.http.response`

### Classe `Response`

```python
Response(status=200, body=b"", content_type="text/html; charset=utf-8", headers=None)
```

| Attribut | Type | Description |
|----------|------|-------------|
| `status` | `int` | Code HTTP |
| `body` | `bytes` | Contenu (str auto-converti en UTF-8) |
| `content_type` | `str` | Type MIME |
| `headers` | `dict` | En-têtes supplémentaires |

---

## `core.http.helpers`

### `html(template, status=200, context=None, *, raw=False) -> Response`

Rend un template et retourne une `Response`.

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `template` | `str` | — | Chemin relatif depuis `views_dir` |
| `status` | `int` | `200` | Code HTTP |
| `context` | `dict \| None` | `None` | Variables injectées dans le template |
| `raw` | `bool` | `False` | Si `True`, retourne le fichier sans passer par Jinja2 |

`raw=True` n'injecte pas de contexte Jinja2. Utile pour les fichiers contenant des accolades (CSS, JS).

---

## `core.http.router`

### Classe `Router`

### `add(method, pattern, handler, *, name=None, public=False, csrf=True, api=False) -> Router`

Enregistre une route. **Raises :** `ValueError` si le nom est déjà utilisé.

### `group(prefix, *, public=False, csrf=True, api=False) -> RouteGroup`

Crée un groupe de routes partageant un préfixe. Les routes unsafe (`POST`, `PUT`, `PATCH`, `DELETE`) sont protégées par CSRF par défaut.

### `match(method, path) -> tuple | None`

Trouve la première route correspondante et retourne l'objet route avec ses paramètres.

```python
entry, params = router.match("POST", "/clients")
entry.pattern / entry.public / entry.csrf / entry.api
entry.requires_csrf("POST")
```

### `resolve(method, path) -> tuple | None`

Retourne `(handler, params)` ou `None`.

### `is_public(path, method=None) -> bool`

Retourne `True` si le chemin correspond à une route publique.

### `iter_routes() -> list[RouteEntry]`

Retourne les routes dans l'ordre de déclaration. Utilisé par `forge routes:list`.

### `url_for(name, **params) -> str`

Génère l'URL d'une route nommée. **Raises :** `KeyError` si le nom ou un paramètre est inconnu.

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
app = Application(router)
app = Application(router, middlewares=[AuthMiddleware("/login")])
```

### `dispatch(request) -> Response`

Point d'entrée principal. Flux :
1. Résout la route et injecte `route_params`
2. Aucune route → `errors/404.html`
3. Route protégée → exécute les middlewares dans l'ordre
4. Route unsafe avec CSRF → vérifie le token
5. Appelle le handler
6. Exception non gérée → `errors/500.html`

### Interface middleware

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

`template_manager` est le singleton à utiliser. Ne pas instancier `TemplateManager` manuellement sauf en test.

### `register(renderer) -> None`

Enregistre le renderer actif. Remplace le renderer précédent.

### `render(template, context) -> str`

Rend un template et retourne le HTML. **Raises :** `RuntimeError` si aucun renderer n'a été enregistré.

---

## `integrations.jinja2.renderer`

### Classe `Jinja2Renderer`

```python
Jinja2Renderer(views_dir: str)
```

Renderer Jinja2 avec autoescape HTML activé sur les fichiers `.html`. Helper global `url_for()` branché sur le routeur actif.

| Cas | Syntaxe | Comportement |
|-----|---------|--------------|
| Valeur utilisateur | `{{ nom }}` | Échappée |
| HTML pré-rendu | `{{ flash \| safe }}` | Injecté tel quel |
| Bloc de layout | `{% block contenu %}{% endblock %}` | Héritage |

---

## `core.security.session`

| Fonction | Description |
|----------|-------------|
| `creer_session() -> str` | Crée une session anonyme. Retourne le `session_id`. |
| `get_session(session_id) -> dict \| None` | Retourne les données de la session ou `None`. |
| `supprimer_session(session_id) -> None` | Supprime immédiatement la session. |
| `authentifier_session(session_id, utilisateur) -> str \| None` | Marque la session comme authentifiée, rotation du `session_id`. |
| `get_session_id(request) -> str \| None` | Extrait le `session_id` depuis le cookie. |
| `est_authentifie(request) -> bool` | `True` si authentifié — repousse l'expiration. |
| `get_utilisateur(request) -> dict \| None` | Retourne le profil de l'utilisateur connecté. |
| `utilisateur_a_role(request, role) -> bool` | `True` si l'utilisateur possède le rôle. |
| `set_flash(session_id, message, level="success") -> None` | Stocke un message flash. |
| `get_flash(session_id) -> dict \| None` | Récupère puis supprime le message flash. |

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

| Fonction | Description |
|----------|-------------|
| `hacher_mot_de_passe(mot_de_passe) -> str` | Retourne un hash sécurisé au format `"sel:hash"`. |
| `verifier_mot_de_passe(mot_de_passe, hash_stocke) -> bool` | Compare un mot de passe avec son hash stocké. |
| `enregistrer_tentative(ip) -> None` | Enregistre une tentative de connexion échouée. |
| `est_limite(ip) -> bool` | `True` si l'IP a atteint la limite de tentatives. |

**Spécifications :** PBKDF2-HMAC-SHA256, 260 000 itérations, sel aléatoire de 16 octets, comparaison via `hmac.compare_digest()`, fenêtre de rate limiting de 60 secondes.

---

## `core.security.middleware`

### Classe `AuthMiddleware`

```python
middleware = AuthMiddleware(login_url="/login")
```

`check(request) -> Response | None` : redirection 302 vers `login_url` si non authentifié, `None` sinon.

### Classe `CsrfMiddleware`

Vérifie le token CSRF des requêtes unsafe déclarées comme protégées par le routeur. Utilisé automatiquement par `Application`.

`check(request) -> Response | None` : retourne `errors/403.html` si le token est absent ou invalide.

---

## `core.security.decorators`

### `@require_auth`

Redirige vers `/login` si non authentifié.

### `@require_csrf`

Retourne 403 si le token CSRF ne correspond pas à la session. Disponible pour du code hérité ; la protection officielle passe par les métadonnées de route et `Application`.

### `@require_role(role)`

Redirige vers `/login` si non authentifié. Retourne 403 si le rôle est absent.

---

## `core.forms`

Mécanique générique des formulaires Forge. Les formulaires applicatifs vivent dans `mvc/forms/`.

### Classe `Form`

```python
class ContactForm(Form):
    nom = StringField(label="Nom", required=True, max_length=80)
    age = IntegerField(label="Age", required=False, min_value=0)
```

### `Form.from_request(request, **options) -> Form`

Construit un formulaire depuis `request.body`. Les `options` servent à fournir des listes de validation explicites.

### `is_valid() -> bool`

Nettoie les données, remplit `cleaned_data` et expose les erreurs.

### Helpers de rendu

| Méthode | Description |
|---------|-------------|
| `form.value("champ")` | Retourne la valeur saisie (pour réaffichage) |
| `form.error("champ")` | Retourne le message d'erreur |
| `form.has_error("champ")` | `True` si le champ a une erreur |

### Attributs

| Attribut | Description |
|----------|-------------|
| `data` | Données d'origine aplaties |
| `cleaned_data` | Données converties et validées |
| `errors` | Erreurs par champ |
| `non_field_errors` | Erreurs globales |
| `context` | Dict prêt à injecter dans un template |

### Champs disponibles

| Champ | Rôle |
|-------|------|
| `StringField` | Chaîne avec `min_length`, `max_length`, `pattern` |
| `IntegerField` | Entier avec `min_value`, `max_value` |
| `DecimalField` | Nombre décimal |
| `BooleanField` | Booléen de formulaire |
| `ChoiceField` | Choix explicite fourni au champ ou au formulaire |
| `RelatedIdsField` | Liste d'identifiants liés pour pivot explicite |

Un formulaire Forge ne fait pas de SQL et ne décide pas d'une redirection.

### `ChoiceField`

Valide une valeur parmi une liste de choix fournie explicitement. Le champ ne charge jamais les choix depuis la base.

```python
ville_id = ChoiceField(required=False, choices_key="allowed_ville_ids")

form = ContactForm.from_request(request, allowed_ville_ids=VilleModel.allowed_ids())
```

### `RelatedIdsField`

Lit une liste d'identifiants, convertit en entiers, supprime les doublons, valide contre une liste autorisée fournie explicitement.

```python
groupe_ids = RelatedIdsField(required=False, allowed_ids_key="allowed_group_ids")

form = ContactForm.from_request(request, allowed_group_ids=GroupeModel.allowed_ids())
```

Ne charge jamais les identifiants autorisés depuis la base. Ne connaît pas la table pivot et ne persiste rien.

---

## `core.mvc.controller.base_controller`

### Classe `BaseController`

| Méthode | Description |
|---------|-------------|
| `render(template, status=200, context=None, *, request=None, raw=False)` | Génère une réponse HTML. Injecte `csrf_token` si `request` est fourni. |
| `redirect(location, *, request=None, flash=None, level="success")` | Redirection 302. |
| `redirect_with_flash(request, location, message, level="success")` | Flux POST-Redirect-GET avec message flash. |
| `redirect_to_route(name, *, request=None, flash=None, level="success", **params)` | Redirige vers une route nommée. |
| `not_found()` | Retourne `errors/404.html` (404). |
| `bad_request()` | 400 |
| `forbidden()` | 403 |
| `validation_error(template, context, request)` | 422 — affiche le formulaire avec erreurs. |
| `server_error()` | 500 |
| `json(data, status=200)` | Retourne une réponse JSON. |
| `body(request) -> dict` | Dict plat depuis `request.body`. |
| `json_body(request) -> dict` | Corps JSON parsé. |
| `csrf_token(request) -> str` | Token CSRF de la session courante. |
| `current_user(request) -> dict \| None` | Profil de l'utilisateur connecté. |
| `set_flash(request, message, level="success")` | Stocke un message flash. |
| `include(partial, context=None) -> str` | Rend un partial Jinja2 et retourne son HTML. |
| `render_form(template, request, data, status=200, erreurs="")` | Raccourci `render()` + `form_context()`. |
| `form_context(request, data, erreurs="") -> dict` | Construit le contexte commun à un formulaire. |

**Note `form_context` :** les données sont injectées brutes. Utiliser `{{ erreurs | safe }}` dans le template uniquement pour cette sortie HTML contrôlée.

---

## `core.mvc.model.validator`

### Classe `Validator`

```python
class ClientValidator(Validator):
    def __init__(self, data):
        super().__init__()
        self.required(data.get("nom", ""), "Nom")
        self.max_length(data.get("nom", ""), 60, "Nom")
```

| Méthode | Description |
|---------|-------------|
| `required(value, label)` | Erreur si vide, `None`, ou espaces seulement. |
| `max_length(value, max_len, label)` | Erreur si `len(str(value)) > max_len`. Sans effet si vide. |
| `add_error(message)` | Ajoute un message d'erreur. |
| `is_valid() -> bool` | `True` si aucune erreur. |
| `errors() -> list[str]` | Liste des erreurs. |

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
pagination = Pagination(request, count_clients(), par_page=10)
items = get_clients_page(limit=pagination.limit, offset=pagination.offset)
```

### Attributs

| Attribut | Type | Description |
|----------|------|-------------|
| `page` | `int` | Page courante |
| `nb_pages` | `int` | Nombre total de pages |
| `total` | `int` | Nombre total d'éléments |
| `par_page` | `int` | Taille de page |
| `limit` | `int` | Limite SQL recommandée |
| `offset` | `int` | Décalage SQL recommandé |
| `has_previous` | `bool` | Page précédente disponible |
| `has_next` | `bool` | Page suivante disponible |
| `previous_page` | `int \| None` | Numéro de page précédente |
| `next_page` | `int \| None` | Numéro de page suivante |

### `context -> dict`

Retourne le dict prêt à injecter dans le template. Clés : `page`, `nb_pages`, `prev_page`, `next_page`, `has_prev`, `has_next`, `limit`, `offset`, `pagination`. Les classes CSS proviennent de `forge.get("css_visible")` / `forge.get("css_hidden")`.

### `to_dict() -> dict`

Bloc standard sans classes CSS, utile pour les APIs internes.

---

## `core.database.db`

Helper SQL léger. N'exécute que du SQL fourni explicitement par le développeur.

| Méthode | Description |
|---------|-------------|
| `fetch_one(sql, params=(), *, tx=None)` | Retourne une ligne (`cursor(dictionary=True)`). |
| `fetch_all(sql, params=(), *, tx=None)` | Retourne toutes les lignes. |
| `execute(sql, params=(), *, tx=None)` | Exécute et retourne `rowcount`. |
| `insert(sql, params=(), *, tx=None)` | Exécute une insertion et retourne `lastrowid`. |

Hors transaction : ouvre, exécute, commit, ferme. Dans une transaction : réutilise `tx` sans commit.

---

## `core.database.transaction`

### `transaction()`

```python
from core.database.transaction import transaction

with transaction() as tx:
    contact_id = ContactModel.create(data, tx=tx)
    ContactGroupeModel.replace_for_contact(contact_id, groupe_ids, tx=tx)
```

---

## `core.database.connection`

### `get_connection() -> mariadb.Connection`

Emprunte une connexion depuis le pool. **Raises :** `mariadb.PoolError` si épuisé.

### `close_connection(connection) -> None`

Restitue la connexion au pool. Sans effet si `connection` est `None`.

Pool initialisé au premier appel. Configuration lue depuis `forge.get()`.

---

## `core.database.sql_loader`

### `charger_queries(nom_fichier) -> module`

Charge un module de requêtes SQL depuis `{sql_dir}/{app_env}/`.

```python
q = charger_queries("client_queries.py")
cursor.execute(q.COUNT_CLIENTS)
```

**Raises :** `FileNotFoundError` si le fichier n'existe pas.

---

## `core.uploads`

Service minimal d'upload local. Valide, génère un nom sûr, évite l'écrasement, stocke sous `storage/uploads/<category>/`.

### `save_upload(file, category="documents") -> SavedUpload`

Lève `UploadStorageError("Aucun fichier reçu.")` si `file` est `None`.

**Comportement MIME :**

| `allowed_mime_types` | MIME reçu | Résultat |
|----------------------|-----------|---------|
| vide `[]` | peu importe | pas de validation MIME |
| non vide | présent et autorisé | accepté |
| non vide | présent et non autorisé | `UploadInvalidMimeTypeError` |
| non vide | absent (`None`) | `UploadInvalidMimeTypeError` |

**`SavedUpload` :**

| Attribut | Description |
|----------|-------------|
| `filename` | Nom sûr généré |
| `original_name` | Nom reçu depuis le navigateur |
| `path` | Chemin complet du fichier enregistré |
| `category` | Sous-dossier utilisé |
| `size` | Taille en octets |
| `mime_type` | Type MIME reçu si disponible |

### `delete_upload(path) -> bool`

Supprime un fichier sous `upload_root`. Retourne `False` si absent. Refuse les chemins hors du dossier d'upload.

### `get_upload_path(filename, category="documents") -> Path`

Retourne le chemin attendu pour un fichier d'une catégorie.

### Exceptions

- `UploadError`
- `UploadTooLargeError`
- `UploadInvalidExtensionError`
- `UploadInvalidMimeTypeError`
- `UploadStorageError`

---

## `mvc.helpers.flash`

### `render_flash_html(request) -> str`

Récupère puis supprime le message flash de la session et retourne son HTML pré-rendu. Retourne `""` si aucun flash.

Dans le template : `{{ flash | safe }}`.

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

Convertit une liste d'erreurs en bloc HTML. Retourne `""` si vide. Les messages sont échappés via `html.escape()`.

Dans le template : `{{ erreurs | safe }}`.

---

## `forge` CLI

### Tableau des commandes

| Commande | Rôle | Écrit des fichiers |
|----------|------|--------------------|
| `forge new NomProjet` | Crée un nouveau projet depuis le squelette officiel | Oui, dans le nouveau projet |
| `forge doctor` | Diagnostique l'environnement du projet courant | Non |
| `forge make:entity Entity` | Crée une entité JSON canonique (interactif ou `--no-input`) | Oui |
| `forge make:crud Entity [--dry-run]` | Génère le squelette CRUD MVC d'une entité | Oui |
| `forge make:relation` | Ajoute une relation globale via assistant interactif | Oui |
| `forge sync:entity Entity` | Régénère SQL et base Python d'une entité | Oui |
| `forge sync:relations` | Régénère `mvc/entities/relations.sql` | Oui |
| `forge sync:landing [--check]` | Copie la landing canonique vers `docs/index.html` | Oui / Non |
| `forge upload:init` | Initialise les dossiers de stockage upload | Oui |
| `forge build:model [--dry-run]` | Valide et régénère tout le modèle | Oui |
| `forge check:model` | Valide le modèle sans écrire | Non |
| `forge db:init` | Prépare la base MariaDB et l'utilisateur applicatif | Oui, côté base |
| `forge db:apply` | Applique les SQL générés en base | Oui, côté base |
| `forge routes:list` | Liste les routes déclarées | Non |
| `forge deploy:init` | Génère Nginx, systemd et README de déploiement dans `deploy/` | Oui |
| `forge deploy:check` | Diagnostique l'environnement de production local | Non |
| `forge starter:list` | Liste les starter apps disponibles | Non |
| `forge starter:build <id> [--dry-run] [--init-db] [--force] [--public]` | Construit automatiquement un starter applicatif | Oui |
| `forge help` | Affiche l'aide CLI intégrée | Non |

### `forge new <NomProjet>`

Clone par défaut la référence stable `v1.0.1` du dépôt Forge, configure `env/dev`, crée le virtualenv Python, génère les certificats HTTPS locaux, réinitialise le dépôt Git. Pour travailler explicitement depuis la branche de développement, utilisez `forge new <NomProjet> --ref main`.

**Prérequis :** `git`, `openssl`, Python 3.11+. Node.js / npm est optionnel.

### `forge make:entity <Entity>`

```bash
forge make:entity Contact           # mode interactif
forge make:entity Contact --no-input  # squelette minimal, utile en CI
```

### `forge make:crud <Entity> [--dry-run]`

Génère contrôleur, modèle, formulaire et vues depuis l'entité JSON canonique. Les fichiers existants sont marqués `[PRÉSERVÉ]`. Affiche le bloc de routes à copier dans `mvc/routes.py`.

Tags de sortie : `[CRÉÉ]` nouveau fichier, `[PRÉSERVÉ]` fichier existant non touché.

### `forge sync:entity <Entity>`

Régénère `<entity>.sql` et `<entity>_base.py`. Ne touche jamais les fichiers manuels (`<entity>.py`, `__init__.py`).

### `forge build:model [--dry-run]`

Régénère tout le modèle. Tags de sortie :

| Tag | Signification |
|-----|---------------|
| `[ÉCRIT]` | Fichier généré ou régénéré |
| `[CRÉÉ]` | Fichier manuel squelette créé car absent |
| `[PRÉSERVÉ]` | Fichier manuel existant — non touché |

### `forge db:init`

Crée la base `DB_NAME`, l'utilisateur `DB_APP_LOGIN` et applique les privilèges. Utilise `DB_ADMIN_*`.

En Forge 1.0.1, le compte `DB_APP_LOGIN` reste volontairement compatible avec `forge db:apply` dans un contexte pédagogique : il reçoit les droits de lecture/écriture et les droits de migration sur `DB_NAME.*`. En production, utilisez un compte de migration séparé et un compte applicatif runtime limité à `SELECT`, `INSERT`, `UPDATE`, `DELETE`.

### `forge db:apply`

Applique les SQL générés avec `DB_APP_*`, dans l'ordre : entités puis relations.

### `forge routes:list`

Affiche méthode, chemin, nom, statut public/protégé, CSRF requis, marqueur API, handler Python.

### `forge deploy:init`

Génère `deploy/nginx/forge-app.conf`, `deploy/systemd/forge-app.service`, `deploy/README_DEPLOY.md`. Idempotent : `[PRÉSERVÉ]` si un fichier existe.

### `forge deploy:check`

Vérifie : Python ≥ 3.11, `.venv`, `env/prod`, variables `DB_APP_*`, `UPLOAD_ROOT`, `storage/`, modules `mariadb` et `jinja2`, fichiers `deploy/`. Quitte avec le code `1` si au moins une erreur bloquante.

### `forge starter:list`

| Niveau | Starter | Génération automatique |
|---:|---|---|
| 1 | Contacts | Disponible |
| 2 | Utilisateurs / authentification | Disponible |
| 3 | Carnet de contacts | Disponible |
| 4 | Suivi comportement élèves | À venir |

### `forge starter:build <identifiant>`

Construit un starter depuis un projet Forge vierge ou préparé.

| Option | Effet |
|--------|-------|
| `--dry-run` | Prévisualise sans écrire |
| `--init-db` | Lance `forge db:init` avant la construction |
| `--force` | Nettoie et reconstruit (prudence) |
| `--public` | Routes publiques de test (starter 1 uniquement) |

Identifiants équivalents : `1`, `contacts`, `contact-simple` — `2`, `auth`, `utilisateurs`, `utilisateurs-auth` — `3`, `carnet`, `carnet-contacts`.

### `forge doctor`

Diagnostique l'environnement et produit un rapport lisible.

| Statut | Signification |
|--------|---------------|
| `OK`   | Check passé |
| `WARN` | Anomalie non bloquante |
| `FAIL` | Problème bloquant — à corriger |
| `SKIP` | Check ignoré faute de contexte |

| Check | FAIL si | WARN si | SKIP si |
|-------|---------|---------|---------|
| Python | < 3.11 | — | — |
| Environnement | `env/example` absent ou clé requise manquante | `env/dev` absent | — |
| Structure MVC | dossiers obligatoires absents | — | — |
| Entités | modèle invalide | aucune entité | `mvc/entities/` absent |
| Certificats SSL | — | fichiers absents | `config.py` non chargeable |
| Node.js / npm | — | npm absent | — |
| Base de données | — | driver absent ou connexion refusée | `env/dev` absent |

**Code de sortie :** `0` si aucun `FAIL`, `1` sinon.

### `forge help`

```bash
forge help
forge --help
forge -h
```
