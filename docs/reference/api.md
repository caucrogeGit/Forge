# Index API

L'API publique du cœur est documentée **par module**, chacun ayant sa page de référence dédiée (rôle, schémas UML, signatures exactes, exemples).
Cette page est l'index : le catalogue ci-dessous renvoie vers chaque module ; suivent deux références transverses (le contrôleur de base et le CRUD généré).

## Catalogue par module

| Domaine | Pages de référence détaillées |
|---|---|
| Configuration | [registre `forge.py`](../core/forge_config.md) |
| HTTP | [Request](../core-http/request.md), [Response](../core-http/response.md), [Helpers](../core-http/helpers.md), [Router](../core-http/router.md) |
| Sécurité | [Hashing](../core-security/hashing.md), [CSRF](../core-security/csrf.md), [Session](../core-security/session.md), [CSP](../core-security/csp.md), [Headers](../core-security/headers.md), [Cookies](../core-security/cookies.md), [Décorateurs](../core-security/decorators.md), [Auth API](../core-security/api_auth.md), [Middleware](../core-security/middleware.md) |
| Sessions | [Manager](../core-sessions/manager.md), [Contrat](../core-sessions/contract.md), [Clés](../core-sessions/keys.md) |
| Base de données | [db](../core-database/db.md), [Transaction](../core-database/transaction.md), [SQL loader](../core-database/sql_loader.md), [Connexion](../core-database/connection.md) |
| Formulaires | [Form](../core-forms/form.md), [Champs](../core-forms/fields.md), [Validation d'upload](../core-forms/upload_validation.md) |
| Validation | [Décorateurs](../core-validation/decorators.md), [Exceptions](../core-validation/exceptions.md) |
| Templating | [Manager](../core-templating/manager.md), [Contrats](../core-templating/contracts.md) |
| MVC | [BaseController](#coremvccontroller), [Pagination](../core-mvc/pagination.md), [Validator](../core-mvc/validator.md) |
| Erreurs runtime | [Erreurs runtime](../core-errors/runtime_errors.md) |
| Application | [Application](../core-app/application.md), [Fabrique](../core-app/app_factory.md) |
| Modules | [Système de modules](../core-modules/registry.md) |
| Auth / User | [User](../core-auth/user.md), [Session auth](../core-auth/session.md), [Mots de passe](../core-auth/password.md) |

## Frontières et conventions

- **Authentification** : `core.auth` est l'API officielle (sessions, mots de passe Argon2id, jetons). `core.security` (hachage, session) est conservé comme couche legacy ; les nouveaux projets utilisent `core.auth`. Commandes d'administration des comptes : `auth:user:create`, `auth:user:list`, `auth:user:disable`, `auth:user:enable`, `auth:user:password`, `auth:user:role:add`, `auth:user:role:remove`, `auth:user:roles` (voir [Authentification CLI](../cli-security/auth.md)).
- **Relations** : les relations `many_to_one` et `many_to_many` sont supportées (voir [Relations entre entités](../features/relations.md)).

## BaseController

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

### Méthode legacy : à ne pas utiliser

| Méthode | Signature | Statut |
|---|---|---|
| `current_user` | `current_user(request)` | **LEGACY**, appelle `core.security.session.get_user()` qui émet un `DeprecationWarning`. Absente de tous les starters post-9.1. |

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
        return self.redirect_with_flash(request, "/contact", "Contact créé.")

    def api_index(self, request):
        return self.json({"contacts": fetch_all("SELECT * FROM Contact")})
```

</details>

## CRUD généré : récapitulatif des fonctionnalités

Le CRUD produit par `forge make:crud` couvre nativement le filtrage, le tri, les actions groupées et l'export, sans JavaScript lourd.
Détail et exemples : [CRUD explicite](../features/crud.md) et la page de la commande [make:crud](../cli-entities/make_crud.md).

| Fonctionnalité | Points clés |
|---|---|
| Filtrage | recherche et `filter` par colonne, contrôles conservés dans `pagination.filters` |
| Recherche live (HTMX) | rafraîchit la cible `#crud-results` via HTMX, sans rechargement de page |
| Tri | colonnes triables bornées par la liste blanche `_ALLOWED_SORT` |
| Suppression groupée | actions `bulk` (suppression groupée) avec confirmation et jeton CSRF |
| Export CSV | route `export.csv`, plafond `_EXPORT_LIMIT` (1000 lignes), échappement `_csv_escape` (anti-injection CSV) |
| En-têtes | `Cache-Control` adapté aux réponses partielles et à l'export |
| Accès | compatible RBAC (`require_permission`) ; toutes les mutations protégées par CSRF |
