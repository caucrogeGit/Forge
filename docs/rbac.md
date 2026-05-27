# RBAC — Contrôle d'accès par rôles et permissions

## Vue d'ensemble

Le RBAC Forge est **générique** et **sans ORM**. Il fournit les briques
nécessaires pour protéger les routes HTTP et afficher conditionnellement des
éléments de template, sans imposer de modèle utilisateur ni de structure de
base particulière.

| Brique | Fichier | Rôle |
|---|---|---|
| Modèles | `forge_mvc_rbac` | `Role`, `Permission`, normalisation, validation |
| Décorateur serveur | `forge_mvc_rbac` | `@require_permission` |
| Helper Jinja | `forge_mvc_rbac` | `make_can` / `can(...)` |
| Résolution | `forge_mvc_rbac` | `get_request_permissions`, `has_permission` |
| Tables SQL | `mvc/models/sql/rbac.sql` | Schéma `roles`, `permissions`, `role_permissions` |
| CRUD déclaratif | `forge_cli/entities/make_crud.py` | Injection de `@require_permission` à la génération |

**Principe fondamental** : Forge fournit le mécanisme d'autorisation.
L'application fournit l'identité de l'utilisateur et la liste de ses
permissions, après authentification.

---

## RBAC léger core ou RBAC complet opt-in ?

Forge distingue deux niveaux d'autorisation :

**RBAC léger core** — primitives dans `core/security/` (dépréciées depuis Forge 2.x) :

- `user_has_role(request, role)` — vérifie qu'un rôle est présent dans le champ `roles` de la session Auth/User. Ne consulte pas les tables SQL RBAC.
- `require_role(role)` — décorateur : redirige vers `/login` si non authentifié, retourne 403 si le rôle est absent de la session.

Ces deux fonctions conviennent aux cas les plus simples (protéger une route par un rôle déjà dans la session). Elles ne connaissent pas les permissions fines et ne remplacent pas `forge-mvc-rbac`. Les nouveaux projets utilisent `forge_mvc_rbac.require_user_permission`.

**RBAC complet opt-in** — module `forge-mvc-rbac` :

- Modèles `Role`, `Permission` (normalisation, validation)
- Décorateur `@require_permission(...)` — résolution via tables SQL `roles`, `permissions`, `role_permissions`
- Helper Jinja `make_can` / `can(...)` — affichage conditionnel dans les templates
- Résolution backend `get_user_permissions`, `user_has_permission`
- Pont Auth/User vers RBAC via la table `user_roles`
- Administration CLI des associations utilisateurs/rôles

### Quand utiliser quoi ?

| Besoin | Choix recommandé |
|---|---|
| Vérifier simplement qu'un utilisateur a un rôle (session) | `user_has_role` — core léger (déprécié) |
| Protéger une route pour les nouveaux projets | `forge-mvc-rbac` — `require_user_permission` |
| Permissions fines (`contacts.edit`, `posts.delete`) | `forge-mvc-rbac` — `require_permission` |
| Administrer rôles et permissions | `forge-mvc-rbac` |
| Affichage conditionnel dans les templates Jinja | `forge-mvc-rbac` — `can(...)` |
| Relations utilisateurs/rôles complexes | `forge-mvc-rbac` |

### Frontière d'import

`core/` ne doit pas importer `forge_mvc_rbac`. La dépendance va dans un seul sens : `forge-mvc-rbac` → `core`. `core/auth/audit.py` peut nommer des événements d'audit RBAC génériques — ce vocabulaire est assumé dans le core (ADR-011), il ne représente pas une dépendance fonctionnelle vers le module opt-in.

---

## RBAC et Auth/User

Le RBAC repond a la question : **qu'a le droit de faire l'utilisateur ?**
La brique Auth/User repond a la question : **qui est connecte ?**

Pour comprendre comment Auth/User fournit l'identité utilisateur (login, MFA, OIDC,
sessions, cookies, administration CLI), voir la [documentation Auth/User](auth.md).

Auth/User fournit l'identite locale et RBAC fournit les roles et permissions.
La table optionnelle `user_roles`, ajoutee par AUTH-USER-RBAC-001, sert de pont
entre les deux mondes : elle associe un `user_id` a un `role_id`, sans stocker
de permissions dans `users` et sans deplacer la logique RBAC dans Auth/User.

AUTH-USER-RBAC-002 ajoute ensuite la resolution backend des permissions depuis
l'utilisateur connecte, sans ajouter de logique Jinja ni d'interface admin.

Il existe donc deux modes de protection serveur, volontairement distincts :

| Mode | API | Source des permissions |
|---|---|---|
| RBAC historique | `@require_permission(...)` | `request.permissions` ou session RBAC historique |
| Auth/User + RBAC | `require_user_permission(...)` | session Auth/User puis `user_roles -> roles -> permissions` |

`@require_permission(...)` ne lit pas automatiquement `user_roles`.
`require_user_permission(...)` ne lit pas `request.permissions` ni
`session["permissions"]`. Cette separation permet aux applications existantes
de conserver leur RBAC historique tout en donnant un chemin clair aux projets
qui utilisent Auth/User.

---

## Tables RBAC

Les trois tables sont déclarées dans `mvc/models/sql/rbac.sql` :

```sql
-- Rôles : admin, moderateur, lecteur…
CREATE TABLE IF NOT EXISTS roles (
    id          INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    slug        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT         NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Permissions atomiques : posts.edit, users.delete, dashboard.view…
CREATE TABLE IF NOT EXISTS permissions (
    id          INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    code        VARCHAR(150) NOT NULL UNIQUE,
    label       VARCHAR(255) NULL,
    description TEXT         NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Liaison rôle ↔ permission (clé primaire composite)
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id       INT NOT NULL,
    permission_id INT NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    CONSTRAINT fk_rp_role
        FOREIGN KEY (role_id)       REFERENCES roles(id)       ON DELETE CASCADE,
    CONSTRAINT fk_rp_permission
        FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    INDEX idx_rp_permission (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

Pour créer les tables dans votre base :

```bash
mysql -u user -p ma_base < mvc/models/sql/rbac.sql
```

La table optionnelle `user_roles` est fournie par la brique Auth/User avancee
pour relier les utilisateurs locaux aux roles RBAC existants :

```sql
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    INDEX idx_user_roles_user_id (user_id),
    INDEX idx_user_roles_role_id (role_id),
    CONSTRAINT fk_user_roles_user_id
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_role_id
        FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

Cette table reste optionnelle. RBAC reste responsable des roles et permissions ;
Auth/User ne devient pas un systeme d'autorisation.

### Resolution Auth/User vers permissions

Le flux de lecture backend est maintenant explicite :

```text
user_id -> user_roles -> roles -> role_permissions -> permissions
```

API cote Auth/User :

> ℹ️ Les fonctions ci-dessous sont fournies par le module optionnel
> `forge-mvc-rbac` (opt-in officiel publié sur PyPI depuis `1.0.0-beta.9` — voir
> [contrat d'installation](install/index.md#contrat-dinstallation-des-opt-ins)).

```python
from forge_mvc_rbac import get_user_permissions, get_user_role_ids, user_has_permission

role_ids = get_user_role_ids(user_id)
permissions = get_user_permissions(user_id)
ok = user_has_permission(user_id, "articles.edit")
```

Les permissions restent des permissions RBAC. Auth/User ne les definit pas et
ne les stocke pas dans `users`.

---

## Modèles Python

```python
from forge_mvc_rbac import Role, Permission

# Créer depuis une ligne SQL
role = Role.from_row({"id": 1, "name": "Administrateur", "slug": "admin"})
perm = Permission.from_row({"id": 1, "code": "posts.edit", "label": "Modifier articles"})

# Sérialiser
role.to_dict()  # {"id": 1, "name": "Administrateur", "slug": "admin", "description": None}
perm.to_dict()  # {"id": 1, "code": "posts.edit", "label": "Modifier articles", "description": None}
```

### Normalisation

```python
from forge_mvc_rbac import normalize_role_slug, normalize_permission_code

normalize_role_slug("Super Admin")   # → "super-admin"
normalize_role_slug("GESTIONNAIRE")  # → "gestionnaire"

normalize_permission_code("Posts.Edit")  # → "posts.edit"
normalize_permission_code("posts edit")  # → "posts.edit"
```

### Validation

```python
from forge_mvc_rbac import validate_role, validate_permission, RbacValidationError

validate_role("Admin", "admin")          # OK
validate_role("", "admin")               # → RbacValidationError
validate_role("Admin", "super admin")    # → RbacValidationError (espace dans slug)

validate_permission("posts.edit")        # OK
validate_permission("")                  # → RbacValidationError
validate_permission("postsedit")         # → RbacValidationError (pas de point)
```

---

## Résolution des permissions

```python
from forge_mvc_rbac import get_request_permissions, has_permission

perms = get_request_permissions(request)  # → set[str]
ok    = has_permission(request, "posts.edit")  # → bool
```

Ordre de résolution :

1. `request.permissions` — injection directe (pratique pour les tests)
2. `session["user"]["permissions"]` — depuis la session authentifiée
3. Ensemble vide si aucune source disponible

Ces deux sources sont **contrôlées côté serveur**. Forge ne lit jamais les
permissions depuis les paramètres GET, le corps POST, les headers HTTP ni les
cookies bruts. Voir [Chaîne de confiance](#chaine-de-confiance).

---

## `@require_permission` — décorateur serveur

### Usage

```python
from forge_mvc_rbac import require_permission
from core.security.decorators import require_auth

class PostController:

    @staticmethod
    @require_auth
    @require_permission("posts.edit")
    def edit(request):
        ...

    @staticmethod
    @require_auth
    @require_permission("posts.delete")
    def delete(request, post_id):
        ...
```

### Comportement

- **Valide le code à la décoration** — `require_permission("postsedit")` lève
  `RbacValidationError` immédiatement, sans attendre une requête.
- **Normalise** le code (`"Posts.Edit"` → `"posts.edit"`) avant la vérification.
- **Retourne 403** si la permission est absente ; laisse passer si elle est présente.
- **Préserve la signature** via `functools.wraps`.

### Ajouter les permissions à la session

```python
utilisateur = {
    "UtilisateurId": row["id"],
    "Login": row["login"],
    "roles": ["admin"],
    "permissions": ["posts.edit", "posts.delete", "users.view"],
}
nouveau_id = authentifier_session(session_id, utilisateur)
```

La clé `"permissions"` est lue par `get_request_permissions` depuis la session.

### Injection dans les tests

```python
def test_edit_requiert_permission():
    req = FakeRequest("POST", "/posts/1/edit")
    req.permissions = ["posts.edit"]
    response = PostController.edit(req)
    assert response.status == 200

def test_edit_refuse_sans_permission():
    req = FakeRequest("POST", "/posts/1/edit")
    response = PostController.edit(req)
    assert response.status == 403
```

---

## Protection serveur avec Auth/User

Forge fournit aussi une strategie serveur explicite pour les projets qui
utilisent Auth/User et la table optionnelle `user_roles` :

> ℹ️ Cette section utilise des symboles fournis par le module
> optionnel `forge-mvc-rbac` (opt-in officiel publié sur PyPI depuis `1.0.0-beta.9` — voir
> [contrat d'installation](install/index.md#contrat-dinstallation-des-opt-ins)).

```python
from forge_mvc_rbac import require_user_permission

@require_user_permission("posts.edit")
def edit(request, post_id):
    ...
```

`require_user_permission(...)` lit l'utilisateur connecte avec
`get_authenticated_user_id(request)`, puis verifie ses permissions effectives
via le flux :

```text
user_id -> user_roles -> roles -> role_permissions -> permissions
```

Comportement :

- `401 Unauthorized` si aucun utilisateur Auth/User n'est connecte ;
- `403 Forbidden` si l'utilisateur est connecte mais ne possede pas la
  permission ;
- passage au controleur si `user_has_permission(user_id, permission)` retourne
  `True`.

Le RBAC historique reste disponible. `@require_permission(...)` n'est pas
supprime et continue de lire uniquement les permissions deja presentes dans
`request.permissions` ou dans la session RBAC historique. `make_can(request)`
conserve aussi son comportement existant pour ce mode.

### Attribution CLI des roles utilisateur

La CLI Auth/User peut manipuler la table optionnelle `user_roles` :

```bash
forge auth:user:role:add --email user@example.com --role admin
forge auth:user:role:remove --email user@example.com --role admin
forge auth:user:roles --email user@example.com
```

Ces commandes ne creent ni role, ni permission, ni utilisateur. Elles associent
ou dissocient seulement un utilisateur local existant et un role RBAC existant.
La definition des roles et permissions reste dans les tables RBAC historiques
`roles`, `permissions` et `role_permissions`.

---

## `can(...)` — helper d'affichage Jinja

### Usage dans les templates

```jinja2
{% if can("admin.users.manage") %}
  <a href="/admin/users">Utilisateurs</a>
{% endif %}

{% if can("posts.edit") %}
  <a href="/posts/{{ post.id }}/edit">Modifier</a>
{% endif %}
```

`can(...)` est injecté automatiquement dans les templates rendus via
`BaseController.render(..., request=request)`. Si une session Auth/User contient
un utilisateur local et que le contexte Auth/User est disponible, le helper peut
passer par la resolution backend :

```text
user_id -> user_roles -> roles -> role_permissions -> permissions
```

Sans session Auth/User, Forge preserve le comportement historique base sur les
permissions deja presentes dans la requete ou la session.

`can(...)` reste un helper d'affichage. Il peut masquer un bouton ou un lien,
mais ne protege jamais une route a lui seul.

### `make_can` — injection manuelle

```python
from forge_mvc_rbac import make_can
from tests.fake_request import FakeRequest

def test_menu_admin_visible():
    req = FakeRequest()
    req.permissions = ["admin.users.manage"]
    ctx = {"can": make_can(req)}
    html = renderer.render("layouts/nav.html", ctx)
    assert "Utilisateurs" in html
```

### Comportement

- Retourne `True` si la permission est présente, `False` sinon.
- Normalise automatiquement le code : `can("POSTS.EDIT")` équivaut à `can("posts.edit")`.
- Retourne `False` si aucune permission n'est disponible.
- Retourne `False` si aucun utilisateur n'est connecte dans le mode Auth/User.
- Retourne `False` si les tables optionnelles `user_roles` ou RBAC sont absentes.
- Ne lève jamais d'exception visible dans le template.
- Ne cree aucune permission et ne modifie aucune table.

### Différence entre `@require_permission` et `can`

| | `@require_permission` | `can(...)` |
|---|---|---|
| Où | Décorateur Python côté serveur | Template Jinja2 côté HTML |
| Rôle | **Protège** une action HTTP | **Affiche ou masque** un élément |
| Retour | 403 si permission absente | `True` / `False` |
| Obligatoire pour la sécurité | **Oui** | Non |

> **Avertissement** — Masquer un bouton dans le HTML n'est pas une sécurité
> suffisante. La route appelée doit aussi être protégée côté serveur avec
> `@require_permission(...)` ou `require_user_permission(...)`. Un utilisateur
> peut appeler la route directement sans passer par le bouton.

---

## `rbac.permissions` dans `make:crud`

### Déclarer les permissions dans l'entité JSON

```json
{
  "entity": "Contact",
  "table": "contacts",
  "fields": ["..."],
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
}
```

Le bloc `rbac` est **optionnel**. Sans lui, le CRUD généré est identique à avant.

### Actions supportées

| Clé JSON | Méthode générée | Route |
|---|---|---|
| `index` | `index` | `GET /contacts` |
| `show` | `show` | `GET /contacts/{id}` |
| `create` | `new` | `GET /contacts/new` |
| `store` | `create` | `POST /contacts` |
| `edit` | `edit` | `GET /contacts/{id}/edit` |
| `update` | `update` | `POST /contacts/{id}` |
| `delete` | `destroy` | `POST /contacts/{id}/delete` |

Seules les actions déclarées dans `rbac.permissions` reçoivent un décorateur.

### Code généré

Pour une entité `Contact` avec les permissions ci-dessus, `make:crud` génère :

```python
from forge_mvc_rbac import require_permission
from core.mvc.controller import BaseController
...

class ContactController(BaseController):

    @staticmethod
    @require_permission("contacts.view")
    def index(request):
        ...

    @staticmethod
    @require_permission("contacts.edit")
    def edit(request):
        ...

    @staticmethod
    @require_permission("contacts.delete")
    def destroy(request):
        ...
```

L'import `from forge_mvc_rbac import require_permission` n'est ajouté que
si au moins une permission est déclarée.

### Règles de validation

- Le code doit utiliser la notation pointée : `"contacts.view"` ✓, `"contactsview"` ✗
- La valeur doit être une chaîne non vide
- Les actions inconnues (ex. `"publish"`) produisent une erreur lors de `make:crud`
- Les codes sont normalisés automatiquement : `"Contacts.View"` → `"contacts.view"`

### Guards `{% if can() %}` dans les templates générés

Quand `rbac.permissions` est déclaré, `make:crud` entoure automatiquement les
boutons d'action des vues avec des guards Jinja :

| Vue | Élément protégé | Permission utilisée |
|---|---|---|
| `index.html` | Bouton « Nouveau » | `create` |
| `_table.html` | Lien « Modifier » | `edit` |
| `_table.html` | Formulaire « Supprimer » | `delete` |
| `show.html` | Bouton « Modifier » | `edit` |
| `show.html` | Formulaire « Supprimer » | `delete` |

Le lien « Afficher » (show) n'est jamais conditionné : la consultation reste
visible, c'est la route serveur qui décide.

```jinja2
{% if can('contacts.create') %}
{% with href='/contacts/new', variant='primary', label='Nouveau contact' %}
{% include "components/button.html" %}
{% endwith %}
{% endif %}
```

Sans `rbac` dans la définition, aucun guard n'est injecté (comportement
inchangé, compatibilité arrière).

!!! warning "Guard UI ≠ protection serveur"
    `{% if can() %}` masque le bouton dans l'interface, mais ne bloque pas
    l'appel HTTP direct. Les décorateurs `@require_permission` générés côté
    contrôleur restent la seule protection réelle.

---

## Chaîne de confiance {#chaine-de-confiance}

### Rôles respectifs

| Acteur | Responsabilité |
|---|---|
| **Forge** | Fournit le mécanisme d'autorisation (`require_permission`, `has_permission`, `can`) |
| **L'application** | Fournit l'identité utilisateur après authentification |
| **L'application** | Fournit la source fiable des permissions (depuis la base, l'annuaire, etc.) |

### Sources de permissions acceptées

Forge lit les permissions depuis deux sources, dans cet ordre :

1. **`request.permissions`** — injection directe par l'application après authentification
2. **`session["user"]["permissions"]`** — champ de la session serveur

### Sources refusées

| Source client | Statut |
|---|---|
| Paramètres GET (`?permissions=...`) | **Refusé** — jamais lu |
| Corps POST / formulaire | **Refusé** — jamais lu |
| Body JSON (`{"permissions": [...]}`) | **Refusé** — jamais lu |
| Headers HTTP (`X-Permissions: ...`) | **Refusé** — jamais lu |
| Cookies bruts (hors `session_id`) | **Refusé** — jamais lu |

### Injecter les permissions correctement

```python
# ✅ Correct — injection serveur après résolution applicative
def before_action(request, user):
    request.permissions = load_permissions_for_user(user.id)

# ✅ Correct — via la session lors de l'authentification
utilisateur = {
    "UtilisateurId": user.id,
    "Login": user.login,
    "roles": ["editor"],
    "permissions": ["posts.edit", "posts.view"],
}
nouveau_id = authentifier_session(session_id, utilisateur)
```

```python
# ❌ Interdit — permissions lues depuis le client
request.permissions = request.params.get("permissions")
request.permissions = request.body.get("permissions")
request.permissions = request.headers.get("X-Permissions")
request.permissions = request.cookies.get("permissions")
```

---

## Ce que Forge ne fait pas encore

- L'injection Jinja Auth/User existe pour l'affichage, mais elle ne protege pas
  les routes a elle seule.
- `user_roles` formalise le lien optionnel `user ↔ rôle` ; la resolution
  backend des permissions passe ensuite par les tables RBAC.
- Les routes manuelles (hors `make:crud`) doivent être protégées manuellement
  avec `@require_permission(...)`.
- Pas d'administration des rôles et permissions via une interface Forge.
- Pas de hiérarchie de rôles automatique.

---

## Exemple complet minimal

### 1. Entité JSON avec permissions

```json
{
  "format_version": 1,
  "entity": "Article",
  "table": "articles",
  "fields": [
    {"name": "id",    "column": "Id",    "python_type": "int", "sql_type": "INT",
     "primary_key": true, "auto_increment": true, "nullable": false, "constraints": {}},
    {"name": "titre", "column": "Titre", "python_type": "str", "sql_type": "VARCHAR(200)",
     "primary_key": false, "auto_increment": false, "nullable": false, "constraints": {}}
  ],
  "rbac": {
    "permissions": {
      "index":  "articles.view",
      "show":   "articles.view",
      "create": "articles.create",
      "store":  "articles.create",
      "edit":   "articles.edit",
      "update": "articles.edit",
      "delete": "articles.delete"
    }
  }
}
```

### 2. Générer le CRUD

```bash
forge make:crud Article
```

### 3. Template avec `can`

```jinja2
{% if can("articles.edit") %}
  <a href="/articles/{{ article.Id }}/edit">Modifier</a>
{% endif %}
```

### 4. Authentification avec permissions

```python
utilisateur = {
    "UtilisateurId": row["id"],
    "Login": row["login"],
    "roles": ["redacteur"],
    "permissions": ["articles.view", "articles.edit"],
}
nouveau_id = authentifier_session(session_id, utilisateur)
```

### 5. Test

```python
from tests.fake_request import FakeRequest
from mvc.controllers.article_controller import ArticleController

def test_edit_avec_permission():
    req = FakeRequest()
    req.permissions = ["articles.edit"]
    req.route_params = {"id": "1"}
    # La méthode edit n'est appelée que si la permission est présente
    # (nécessite une BDD pour aller plus loin — ici on vérifie le gardien)

def test_edit_sans_permission():
    req = FakeRequest()
    response = ArticleController.edit(req)
    assert response.status == 403
```

---

## Erreurs fréquentes

| Symptôme | Cause probable | Solution |
|---|---|---|
| `RbacValidationError` à l'import | Code sans point (`"postsedit"`) | Utiliser la notation pointée : `"posts.edit"` |
| `RbacValidationError` à l'import | Code vide (`""`) | Fournir un code non vide |
| 403 inattendu | `request.permissions` non injecté | Injecter après authentification ou via la session |
| `can(...)` toujours `False` | Template rendu sans `request=request` | Passer `request=request` à `BaseController.render(...)` |
| `can(...)` toujours `False` | Permissions absentes de la session historique | Ajouter la clé `"permissions"` lors de `authentifier_session` |
| `can(...)` toujours `False` | Utilisateur Auth/User sans rôle ou tables RBAC absentes | Initialiser les SQL optionnels et associer l'utilisateur via `user_roles` |
| Code normalisé dans le JSON | `"Contacts.View"` au lieu de `"contacts.view"` | Aucun problème — la normalisation est automatique |
| `EntityDefinitionError` à la génération | Action inconnue dans `rbac.permissions` (`"publish"`) | Utiliser uniquement : `index`, `show`, `create`, `store`, `edit`, `update`, `delete` |

---

## Limites restantes

- **Jinja n'est pas une protection serveur** — `can(...)` masque ou affiche des
  elements d'interface, mais une route sensible doit toujours etre protegee cote
  backend avec `@require_permission(...)` ou une verification equivalente.
- **Pas de `deny by default` automatique** — une route sans `@require_permission`
  est accessible. La politique de refus par défaut dépend du groupe de routes
  (`router.group(...)`).
- **Pas d'ORM** — les tables SQL sont lisibles et exécutables directement. Les
  `JOIN` `user ↔ role ↔ permission` restent explicites dans le resolver
  Auth/User -> RBAC.
- **Deux strategies coexistent** — le RBAC historique et Auth/User + RBAC sont
  separes. Aucun decorateur ne bascule implicitement vers l'autre mode.
- **Pas de cache distribué** — les permissions peuvent etre resolues depuis les
  tables optionnelles RBAC a chaque rendu concerne.
- **Pas de hiérarchie de rôles** — un rôle `admin` n'hérite pas automatiquement
  des permissions d'un rôle `editeur`.
