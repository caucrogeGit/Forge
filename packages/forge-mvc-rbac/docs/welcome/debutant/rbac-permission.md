# Code de permission

Objectif : comprendre ce qu'est un **code de permission** et comment Forge le
normalise et le valide.

**Ce que vous allez apprendre :** une permission est un code en **notation pointée**
(`entité.action`, ex. `article.create`). `normalize_permission_code` le met en forme ;
`validate_permission` refuse les codes invalides.

Deuxième palier du **niveau débutant** de la progression RBAC.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-rbac` installé (palier « Installation »).

## Ce que ce starter montre

- `normalize_permission_code(code)` → forme canonique ;
- `validate_permission(code)` → validité (ou `RbacValidationError`) ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_rbac.normalize_permission_code` | Normaliser un code de permission. | RBAC |
| `forge_mvc_rbac.validate_permission` | Refuser un code invalide. | RBAC |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-permission?code=Article.Create` :
`article.create`, valide.

## Le contrôleur

Créez le contrôleur `mvc/controllers/rbac_permission_controller.py` :

```python
# mvc/controllers/rbac_permission_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import RbacValidationError, normalize_permission_code, validate_permission

_DEMO_CODE = "Article.Create"


def _permission_view(code: str) -> dict:
    normalized = normalize_permission_code(code)
    try:
        validate_permission(normalized)
        return {"input": code, "normalized": normalized, "valid": True, "error": None}
    except RbacValidationError as exc:
        return {"input": code, "normalized": normalized, "valid": False, "error": str(exc)}


class RbacPermissionController(BaseController):
    """Starter pédagogique : normaliser et valider un code de permission."""

    @staticmethod
    def index(request: Request) -> Response:
        code = request.query("code") or _DEMO_CODE
        return BaseController.render(
            "rbac_permission/index.html", context=_permission_view(code), request=request
        )
```

### Comprendre ce code

- La **notation pointée** `entité.action` rend les permissions lisibles et
  cohérentes à travers l'application.
- Normaliser **avant** de comparer évite les faux négatifs (`Article.Create` vs
  `article.create`).
- `validate_permission` lève `RbacValidationError` sur un code vide ou mal formé.

## La vue

Créez la vue `mvc/views/rbac_permission/index.html` :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Code de permission - Forge</title>
</head>
<body>
  <h1>Code de permission</h1>

  <form method="get" action="/rbac-permission">
    <input type="text" name="code" value="{{ input }}" size="40">
    <button type="submit">Normaliser & valider</button>
  </form>

  <ul>
    <li>Entrée : <code>{{ input }}</code></li>
    <li>Normalisé : <code>{{ normalized }}</code></li>
    <li>Valide : <strong>{% if valid %}oui{% else %}non{% endif %}</strong>{% if error %} - {{ error }}{% endif %}</li>
  </ul>

  <p>La notation pointée <code>entité.action</code> (ex. <code>article.create</code>)
  rend les permissions lisibles et cohérentes.</p>
</body>
</html>
```

## La route

Ajoutez l'import et la route dans le groupe public de `mvc/routes.py` :

```python
# mvc/routes.py
from mvc.controllers.rbac_permission_controller import RbacPermissionController

with router.group("", public=True) as public:
    public.add("GET", "/rbac-permission", RbacPermissionController.index, name="rbac_permission_index")
```

## À retenir

- Une permission est un **code pointé** normalisé.
- Normaliser puis valider est le réflexe avant toute comparaison.
- Des codes cohérents = un contrat RBAC fiable.

## Après ce starter

La suite : la brique « rôle ».

[Rôle et slug](rbac-role.md)
