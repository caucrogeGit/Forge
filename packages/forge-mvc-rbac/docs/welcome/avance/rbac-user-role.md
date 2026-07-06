# Associer un rôle à un utilisateur

Objectif : construire et valider l'association **utilisateur ↔ rôle**.

**Ce que vous allez apprendre :** `create_auth_user_role(user_id, role_id)` construit et valide une association `AuthUserRole` que l'application persiste ensuite dans `user_roles`.

Premier palier du **niveau avancé** de la progression RBAC.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-rbac` installé.
    La démo **ne persiste pas** l'association (pas de base).

## Ce que ce starter montre

- `create_auth_user_role(user_id, role_id)` → `AuthUserRole` validé ;
- la clé logique `user_id:role_id` ;
- la validation **sans** persistance (démo).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_rbac.create_auth_user_role` | Construire et valider une association user/role. | RBAC |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-user-role?user_id=1&role_id=2`.

## Le contrôleur

Créez le contrôleur `mvc/controllers/rbac_user_role_controller.py` :

```python
# mvc/controllers/rbac_user_role_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import create_auth_user_role


class RbacUserRoleController(BaseController):
    """Starter pédagogique : construire une association utilisateur ↔ rôle."""

    @staticmethod
    def index(request: Request) -> Response:
        try:
            user_id = int(request.query("user_id") or 1)
            role_id = int(request.query("role_id") or 2)
            association = create_auth_user_role(user_id, role_id)
            context = {
                "user_id": association.user_id,
                "role_id": association.role_id,
                "key": f"{association.user_id}:{association.role_id}",
            }
        except Exception as exc:
            context = {"error": str(exc)}
        return BaseController.render("rbac_user_role/index.html", context=context, request=request)
```

### Comprendre ce code

- `create_auth_user_role` **valide** le couple (entiers positifs) et renvoie un objet ; il **ne touche pas la base**.
- La **persistance est le job de l'application** : on insère le couple dans `user_roles`.
- Une même personne peut cumuler plusieurs associations (plusieurs rôles).

## La vue

Créez la vue `mvc/views/rbac_user_role/index.html` :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Associer un rôle à un utilisateur - Forge</title>
</head>
<body>
  <h1>Associer un rôle à un utilisateur</h1>

  <form method="get" action="/rbac-user-role">
    <label>user_id <input type="number" name="user_id" value="{{ user_id or 1 }}"></label>
    <label>role_id <input type="number" name="role_id" value="{{ role_id or 2 }}"></label>
    <button type="submit">Construire l'association</button>
  </form>

  {% if error %}
  <p data-level="error"><strong>{{ error }}</strong></p>
  {% else %}
  <p data-level="success">Association valide : <code>{{ key }}</code>
  (user_id={{ user_id }}, role_id={{ role_id }}).</p>
  {% endif %}

  <p>L'objet est validé mais <strong>pas persisté</strong> ici : en production, on
  l'enregistre dans <code>user_roles</code>.</p>
</body>
</html>
```

## La route

Ajoutez l'import et la route dans le groupe public de `mvc/routes.py` :

```python
# mvc/routes.py
from mvc.controllers.rbac_user_role_controller import RbacUserRoleController

with router.group("", public=True) as public:
    public.add("GET", "/rbac-user-role", RbacUserRoleController.index, name="rbac_user_role_index")
```

## À retenir

- L'association user ↔ rôle est un **objet validé**, persisté par l'application.
- La table cible est `user_roles`.
- Le package valide ; il ne décide pas du stockage.

## Après ce starter

La suite : résoudre les permissions effectives d'un utilisateur.

[Résoudre les permissions d'un utilisateur](rbac-resolve.md)
