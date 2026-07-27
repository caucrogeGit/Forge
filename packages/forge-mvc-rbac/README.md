# forge-mvc-rbac

Module RBAC officiel pour Forge : rôles, permissions, décorateurs et helpers Jinja.

## Installation

```bash
pip install forge-mvc-rbac
```

## Usage

### Modèles

```python
from forge_mvc_rbac import Role, Permission, normalize_role_slug, normalize_permission_code

slug = normalize_role_slug("Super Admin")  # "super-admin"
code = normalize_permission_code("Posts Edit")  # "posts.edit"

role = Role(id=None, name="Super Admin", slug=slug)
perm = Permission(id=None, code=code)
```

### Décorateurs serveur (session legacy)

```python
from forge_mvc_rbac import require_permission

@staticmethod
@require_permission("posts.edit")
def edit(request): ...
```

### Décorateurs serveur (Auth/User)

```python
from forge_mvc_rbac import require_user_permission

@staticmethod
@require_user_permission("posts.edit")
def edit(request): ...
```

### Helper Jinja

```python
from forge_mvc_rbac import make_auth_jinja_context

# Dans BaseController.render(), injecté automatiquement
ctx.update(make_auth_jinja_context(request))
```

Template :
```jinja
{% if can("posts.edit") %}<a href="...">Modifier</a>{% endif %}
{% if is_authenticated %}Bonjour {{ current_user.id }}{% endif %}
```

## SQL

- La table pivot `user_roles` (liaison `users` ↔ `roles`) est générée dans votre
  projet par la commande du core `forge auth:init`, puis appliquée avec
  `forge db:apply`. Elle est rendue pour le backend installé.
- Les tables `roles`, `permissions`, `role_permissions` sont générées par
  `forge rbac:init`, puis appliquées avec `forge migration:apply`. Elles sont
  rendues pour le backend installé, comme le reste du provisioning Forge.

Le fichier `sql/rbac.sql` du dépôt source n'est plus qu'une **référence
historique** : il n'est pas livré dans le wheel et n'est lu par aucun code.
La source de vérité est la déclaration `forge_mvc_rbac.tables`.

## Limites

- Pas de hiérarchie de rôles
- Pas de multi-tenant
- Toutes les permissions sont définies en base
