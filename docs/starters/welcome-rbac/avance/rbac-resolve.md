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

```python
# mvc/controllers/rbac_resolve_controller.py
from forge_mvc_rbac import get_user_permissions, user_has_permission

_DEMO_ROWS = [{"code": "article.list"}, {"code": "article.show"}, {"code": "article.create"}]


def _demo_fetch_all(sql, params=()):
    return _DEMO_ROWS   # au lieu d'interroger la base


class RbacResolveController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        perms = get_user_permissions(1, fetch_all=_demo_fetch_all)
        return Response.json({
            "permissions": list(perms),
            "can_create": user_has_permission(1, "article.create", fetch_all=_demo_fetch_all),
            "can_delete": user_has_permission(1, "article.delete", fetch_all=_demo_fetch_all),
        })
```

### Comprendre ce code

- L'injection de `fetch_all` rend la résolution **testable** sans base : on passe la
  vraie fonction d'accès en production, une fausse en démo/test.
- `user_has_permission` s'appuie sur `get_user_permissions` : un seul endroit de
  vérité.
- Par défaut (sans `fetch_all` ni accès), **aucune permission** : sécurisé par défaut.

## À retenir

- Les permissions effectives = rôles de l'utilisateur × permissions des rôles.
- `fetch_all` injectable = code RBAC **testable** sans base réelle.
- Sécurisé par défaut : aucun droit sans données.

## Après ce starter

Dernier palier : les rôles tels que vus au runtime, depuis la requête.

[Rôles de la requête](rbac-request-roles.md)
