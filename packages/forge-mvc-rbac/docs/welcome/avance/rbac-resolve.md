# Résoudre les permissions d'un utilisateur

Objectif : calculer les permissions **effectives** d'un utilisateur (ses rôles ×
leurs permissions) depuis la base.

**Ce que vous allez apprendre :** `get_user_permissions` et `user_has_permission`
font ce calcul via un `fetch_all` **injectable** — testables sans vraie base. On
injecte ici un `fetch_all` de démonstration.

Deuxième palier du **niveau avancé** de la progression RBAC.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-rbac` installé. La démo injecte un `fetch_all`
    fixe : **aucune base réelle requise**.

## Ce que ce starter montre

- `get_user_permissions(user_id, fetch_all=...)` → permissions effectives ;
- `user_has_permission(user_id, permission, fetch_all=...)` → booléen ;
- l'injection d'un `fetch_all` de démonstration.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_rbac.get_user_permissions` | Permissions effectives d'un utilisateur (via `fetch_all`). | [RBAC](../../../reference/api.md) |
| `forge_mvc_rbac.user_has_permission` | Test d'une permission pour un utilisateur. | [RBAC](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-resolve` : permissions de l'utilisateur démo +
deux vérifications, en JSON.

## Le contrôleur

Créez le contrôleur `mvc/controllers/rbac_resolve_controller.py` :

```python
# mvc/controllers/rbac_resolve_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import get_user_permissions, user_has_permission

_DEMO_USER_ID = 1
# Lignes que renverrait la base pour les permissions de l'utilisateur démo.
_DEMO_ROWS = [{"code": "article.list"}, {"code": "article.show"}, {"code": "article.create"}]


def _demo_fetch_all(sql, params=()):
    """fetch_all de démonstration : renvoie des permissions fixes (au lieu de la base)."""
    return _DEMO_ROWS


class RbacResolveController(BaseController):
    """Starter pédagogique : résoudre les permissions effectives d'un utilisateur."""

    @staticmethod
    def index(request: Request) -> Response:
        perms = get_user_permissions(_DEMO_USER_ID, fetch_all=_demo_fetch_all)
        return Response.json({
            "user_id": _DEMO_USER_ID,
            "permissions": list(perms),
            "can_create": user_has_permission(_DEMO_USER_ID, "article.create", fetch_all=_demo_fetch_all),
            "can_delete": user_has_permission(_DEMO_USER_ID, "article.delete", fetch_all=_demo_fetch_all),
        })
```

### Comprendre ce code

- L'injection de `fetch_all` rend la résolution **testable** sans base : on passe la
  vraie fonction d'accès en production, une fausse en démo/test.
- `user_has_permission` s'appuie sur `get_user_permissions` : un seul endroit de
  vérité.
- Par défaut (sans `fetch_all` ni accès), **aucune permission** : sécurisé par défaut.

## La route

Ce palier renvoie du JSON directement (`Response.json`), il n'a donc pas de vue.
Ajoutez l'import et la route dans le groupe public de `mvc/routes.py` :

```python
# mvc/routes.py
from mvc.controllers.rbac_resolve_controller import RbacResolveController

with router.group("", public=True) as public:
    public.add("GET", "/rbac-resolve", RbacResolveController.index, name="rbac_resolve_index")
```

## À retenir

- Les permissions effectives = rôles de l'utilisateur × permissions des rôles.
- `fetch_all` injectable = code RBAC **testable** sans base réelle.
- Sécurisé par défaut : aucun droit sans données.

## Après ce starter

Dernier palier : les rôles tels que vus au runtime, depuis la requête.

[Rôles de la requête](rbac-request-roles.md)
