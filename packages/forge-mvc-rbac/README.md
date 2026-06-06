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
  `forge db:apply`.
- Les tables `roles`, `permissions`, `role_permissions` : voir la DDL dans la
  documentation des fonctionnalités RBAC (`docs/features/rbac.md`).

Les fichiers `sql/` du dépôt source (`rbac.sql`, `user_roles.sql`) en sont la
référence ; ils ne sont pas livrés dans le wheel.

## Limites

- Pas de hiérarchie de rôles
- Pas de multi-tenant
- Toutes les permissions sont définies en base
