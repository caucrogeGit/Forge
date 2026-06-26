# Rôle et slug

Objectif : comprendre la brique **rôle**, son nom lisible et son slug stable.

**Ce que vous allez apprendre :** un rôle a un **nom** (« Éditeur en chef ») et un
**slug** identifiant (`editeur-en-chef`). `normalize_role_slug` dérive le slug ;
`validate_role` refuse un rôle invalide.

Troisième palier du **niveau débutant** de la progression RBAC.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-rbac` installé (palier « Installation »).

## Ce que ce starter montre

- `normalize_role_slug(name)` → slug stable ;
- `validate_role(name, slug)` → validité ;
- une transformation **pure**.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_rbac.normalize_role_slug` | Dériver un slug depuis un nom de rôle. | RBAC |
| `forge_mvc_rbac.validate_role` | Refuser un rôle invalide. | RBAC |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-role?name=Éditeur en chef` → slug
`editeur-en-chef`.

## Le contrôleur

Créez le contrôleur `mvc/controllers/rbac_role_controller.py` :

```python
# mvc/controllers/rbac_role_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import RbacValidationError, normalize_role_slug, validate_role

_DEMO_NAME = "Éditeur en chef"


def _role_view(name: str) -> dict:
    slug = normalize_role_slug(name)
    try:
        validate_role(name, slug)
        return {"name": name, "slug": slug, "valid": True, "error": None}
    except RbacValidationError as exc:
        return {"name": name, "slug": slug, "valid": False, "error": str(exc)}


class RbacRoleController(BaseController):
    """Starter pédagogique : dériver et valider un rôle (nom + slug)."""

    @staticmethod
    def index(request: Request) -> Response:
        name = request.query("name") or _DEMO_NAME
        return BaseController.render(
            "rbac_role/index.html", context=_role_view(name), request=request
        )
```

### Comprendre ce code

- Le **slug** est l'identifiant stable du rôle ; il ne change pas même si le nom
  d'affichage évolue.
- Séparer nom et slug évite de coder en dur des libellés dans les comparaisons.
- `validate_role` garantit un couple nom/slug cohérent.

## La vue

Créez la vue `mvc/views/rbac_role/index.html` :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Rôle et slug - Forge</title>
</head>
<body>
  <h1>Rôle et slug</h1>

  <form method="get" action="/rbac-role">
    <input type="text" name="name" value="{{ name }}" size="40">
    <button type="submit">Dériver le slug</button>
  </form>

  <ul>
    <li>Nom : <code>{{ name }}</code></li>
    <li>Slug : <code>{{ slug }}</code></li>
    <li>Valide : <strong>{% if valid %}oui{% else %}non{% endif %}</strong>{% if error %} - {{ error }}{% endif %}</li>
  </ul>

  <p>Le <strong>slug</strong> est l'identifiant stable du rôle ; le <strong>nom</strong>
  est l'affichage. Un rôle accorde des permissions via le contrat RBAC.</p>
</body>
</html>
```

## La route

Ajoutez l'import et la route dans le groupe public de `mvc/routes.py` :

```python
# mvc/routes.py
from mvc.controllers.rbac_role_controller import RbacRoleController

with router.group("", public=True) as public:
    public.add("GET", "/rbac-role", RbacRoleController.index, name="rbac_role_index")
```

## À retenir

- Un rôle = un **nom** (affichage) + un **slug** (identité stable).
- Le slug est ce qui apparaît dans le contrat et les associations.
- Nom et slug se valident ensemble.

## Après ce starter

Vous avez les briques (permission, rôle). La suite (intermédiaire) : les confronter.

[Bilan du niveau débutant](bilan.md)
