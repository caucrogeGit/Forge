# Rôles de la requête

Objectif : inspecter les **rôles et permissions de la requête courante**, ce que
RBAC consomme au runtime.

**Ce que vous allez apprendre :** `get_request_roles(request)` retourne les rôles
déduits de l'utilisateur connecté (session) ; `get_request_permissions(request)` les
permissions qui en découlent. C'est ce que `can()` et les guards utilisent en interne.

Troisième palier du **niveau avancé** de la progression RBAC.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-rbac` installé. **Sans utilisateur connecté**, les
    deux listes sont vides.

## Ce que ce starter montre

- `get_request_roles(request)` → rôles de la requête ;
- `get_request_permissions(request)` → permissions de la requête ;
- le résultat en JSON (vide sans utilisateur).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_rbac.get_request_roles` | Rôles de la requête/session courante. | RBAC |
| `forge_mvc_rbac.get_request_permissions` | Permissions de la requête courante. | RBAC |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-request-roles` : sans utilisateur connecté,
`{"roles": [], "permissions": []}`.

## Le contrôleur

Créez le contrôleur `mvc/controllers/rbac_request_roles_controller.py` :

```python
# mvc/controllers/rbac_request_roles_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import get_request_permissions, get_request_roles


class RbacRequestRolesController(BaseController):
    """Starter pédagogique : inspecter rôles et permissions de la requête courante."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.json({
            "roles": get_request_roles(request),
            "permissions": sorted(get_request_permissions(request)),
        })
```

### Comprendre ce code

- Au runtime, RBAC part des **rôles de la requête** (issus de l'utilisateur connecté),
  pas de paramètres d'URL : c'est la version réelle des démos précédentes.
- `get_request_permissions` combine ces rôles avec le contrat pour donner les
  permissions effectives de la requête.
- Listes vides sans utilisateur : **aucun droit par défaut**.

## La route

Ce palier renvoie du JSON directement (`Response.json`), il n'a donc pas de vue.
Ajoutez l'import et la route dans le groupe public de `mvc/routes.py` :

```python
# mvc/routes.py
from mvc.controllers.rbac_request_roles_controller import RbacRequestRolesController

with router.group("", public=True) as public:
    public.add("GET", "/rbac-request-roles", RbacRequestRolesController.index, name="rbac_request_roles_index")
```

## À retenir

- `get_request_roles` / `get_request_permissions` = la vue runtime du RBAC.
- C'est la source que `can()` et les guards consomment.
- Sécurisé par défaut : pas d'utilisateur, pas de droits.

## Après ce starter

Vous avez parcouru toute la progression RBAC : déclarer, vérifier, appliquer, relier.

[Bilan du niveau avancé](bilan.md)
