# Vérifier une permission

Objectif : répondre « ces **rôles** accordent-ils cette **permission** ? » selon le
contrat.

**Ce que vous allez apprendre :** `has_contract_permission(result, roles, permission)`
agrège les permissions des rôles via le contrat et répond oui/non. Pur, sans base.

Premier palier du **niveau intermédiaire** de la progression RBAC.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-rbac` installé et livre un contrat de démonstration.

## Ce que ce starter montre

- un formulaire (rôles + permission) ;
- `has_contract_permission` → accordée / refusée ;
- une vérification **pure** sur le contrat.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_rbac.has_contract_permission` | Vérifier une permission pour des rôles selon le contrat. | RBAC |
| `forge_mvc_rbac.load_rbac_contract` | Charger le contrat. | RBAC |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-check?roles=reader&permission=article.create`
(refusée), puis `roles=editor` (accordée).

## Le contrôleur

Créez le contrôleur `mvc/controllers/rbac_check_controller.py` :

```python
# mvc/controllers/rbac_check_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import has_contract_permission, load_rbac_contract


class RbacCheckController(BaseController):
    """Starter pédagogique : vérifier une permission contractuelle pour des rôles."""

    @staticmethod
    def index(request: Request) -> Response:
        roles_raw = request.query("roles") or "reader"
        permission = request.query("permission") or "article.create"
        roles = [r.strip() for r in roles_raw.split(",") if r.strip()]
        result = load_rbac_contract(".")
        granted = has_contract_permission(result, roles, permission)
        return BaseController.render(
            "rbac_check/index.html",
            context={"roles": roles_raw, "permission": permission, "granted": granted},
            request=request,
        )
```

### Comprendre ce code

- La vérification est **pure** : rôles + permission + contrat → booléen. Aucune base,
  aucune session.
- Un utilisateur peut cumuler plusieurs rôles : `has_contract_permission` agrège.
- C'est la brique que `require_contract_permission` (guard) et `can()` (template)
  utilisent.

## Le contrat

Ce palier s'appuie sur le contrat `mvc/security/rbac.json` introduit au palier
« Welcome RBAC ». Si vous démarrez ici, créez-le :

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

Créez la vue `mvc/views/rbac_check/index.html` :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Vérifier une permission - Forge</title>
</head>
<body>
  <h1>Vérifier une permission</h1>

  <form method="get" action="/rbac-check">
    <label>Rôles (séparés par des virgules)
      <input type="text" name="roles" value="{{ roles }}">
    </label>
    <label>Permission
      <input type="text" name="permission" value="{{ permission }}">
    </label>
    <button type="submit">Vérifier</button>
  </form>

  <p>
    Rôles <code>{{ roles }}</code> + permission <code>{{ permission }}</code> →
    <strong>{% if granted %}accordée{% else %}refusée{% endif %}</strong>
  </p>

  <p>Essayez <code>reader</code> puis <code>editor</code> avec
  <code>article.create</code> : seul <code>editor</code> l'accorde.</p>
</body>
</html>
```

## La route

Ajoutez l'import et la route dans le groupe public de `mvc/routes.py` :

```python
# mvc/routes.py
from mvc.controllers.rbac_check_controller import RbacCheckController

with router.group("", public=True) as public:
    public.add("GET", "/rbac-check", RbacCheckController.index, name="rbac_check_index")
```

## À retenir

- `has_contract_permission` répond à « ces rôles ont-ils ce droit ? ».
- Le contrat est la **source de vérité** unique.
- Cette brique alimente guards et templates.

## Après ce starter

La suite : transformer cette vérification en **garde de route**.

[Protéger une route](rbac-guard.md)
