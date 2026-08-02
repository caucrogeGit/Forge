# Protéger une route

Objectif : refuser l'accès à une route si les rôles n'accordent pas la permission requise.

**Ce que vous allez apprendre :** `require_contract_permission(result, roles, permission)` renvoie une réponse `403` si la permission manque, sinon `None` (la route continue).
Une ligne en tête de contrôleur suffit.

Deuxième palier du **niveau intermédiaire** de la progression RBAC.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-rbac` installé et livre un contrat de démonstration.

## Ce que ce starter montre

- `require_contract_permission` comme **garde** ;
- une réponse `403` si refusée, la ressource sinon ;
- la garde déclarative en tête de contrôleur.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_rbac.require_contract_permission` | Garde de route (403 si refusée, None sinon). | RBAC |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-guard?roles=reader` (403) puis `?roles=editor` (autorisé).

## Le contrôleur

Créez le contrôleur `mvc/controllers/rbac_guard_controller.py` :

```python
# mvc/controllers/rbac_guard_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import load_rbac_contract, require_contract_permission

_REQUIRED = "article.create"


class RbacGuardController(BaseController):
    """Starter pédagogique : protéger une route par une permission contractuelle."""

    @staticmethod
    def index(request: Request) -> Response:
        roles_raw = request.query("roles") or "reader"
        roles = [r.strip() for r in roles_raw.split(",") if r.strip()]
        result = load_rbac_contract(".")
        context = {"roles": roles_raw, "required": _REQUIRED}
        denied = require_contract_permission(result, roles, _REQUIRED)
        if denied is not None:
            context["denied"] = True
            return BaseController.render("rbac_guard/index.html", context=context, request=request, status=403)
        context["allowed"] = True
        return BaseController.render("rbac_guard/index.html", context=context, request=request)
```

### Comprendre ce code

- Le pattern est **explicite** : on appelle la garde, et si elle renvoie une réponse, on la retourne immédiatement (court-circuit `403`).
- En production, les **rôles viennent de l'utilisateur connecté**, pas de l'URL ; ici on les passe en paramètre pour la démonstration.
- La permission requise est déclarée **une fois**, en tête de l'action.

## Le contrat

Ce palier réutilise le contrat `mvc/security/rbac.json` introduit au palier « Welcome RBAC ».
Si vous démarrez ici, créez-le :

```json
{
  "schema_version": "1.0",
  "entities": {
    "Article": {
      "permissions": {
        "list": "article.list",
        "show": "article.show",
        "create": "article.create",
        "update": "article.update",
        "delete": "article.delete"
      }
    }
  },
  "roles": {
    "admin": ["article.list", "article.show", "article.create", "article.update", "article.delete"],
    "editor": ["article.list", "article.show", "article.create", "article.update"],
    "reader": ["article.list", "article.show"]
  }
}
```

## La vue

Créez la vue `mvc/views/rbac_guard/index.html` :

```html
{# mvc/views/rbac_guard/index.html #}
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Protéger une route - Forge</title>
</head>
<body>
  <h1>Protéger une route</h1>

  <p>Ressource protégée - permission requise : <code>{{ required }}</code></p>
  <p>Rôles présentés : <code>{{ roles }}</code></p>

  {% if allowed %}
  <p data-level="success">✓ Accès autorisé : la route continue.</p>
  {% endif %}
  {% if denied %}
  <p data-level="error">✗ 403 - permission refusée pour ces rôles.</p>
  {% endif %}

  <p>Essayez <code>?roles=reader</code> (403) puis <code>?roles=editor</code> (autorisé).
  En production, les rôles viennent de l'utilisateur connecté, pas de l'URL.</p>
</body>
</html>
```

## La route

Ajoutez l'import et la route dans le groupe public de `mvc/routes/__init__.py` :

```python
# mvc/routes/__init__.py
from mvc.controllers.rbac_guard_controller import RbacGuardController

with router.group("", public=True) as public:
    public.add("GET", "/rbac-guard", RbacGuardController.index, name="rbac_guard_index")
```

## À retenir

- `require_contract_permission` = garde de route, `403` ou passage.
- Court-circuit explicite : `if denied is not None: return denied`.
- Les rôles réels proviennent de la session/utilisateur.

## Après ce starter

La suite : adapter l'**interface** aux permissions.

[Permission dans un template](rbac-template.md)
