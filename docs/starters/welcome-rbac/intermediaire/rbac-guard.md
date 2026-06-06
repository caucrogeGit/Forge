# Protéger une route

Objectif : refuser l'accès à une route si les rôles n'accordent pas la permission
requise.

**Ce que vous allez apprendre :** `require_contract_permission(result, roles, permission)`
renvoie une réponse `403` si la permission manque, sinon `None` (la route continue).
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
| `forge_mvc_rbac.require_contract_permission` | Garde de route (403 si refusée, None sinon). | [RBAC](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-guard?roles=reader` (403) puis `?roles=editor`
(autorisé).

## Le contrôleur

```python
# mvc/controllers/rbac_guard_controller.py
from forge_mvc_rbac import load_rbac_contract, require_contract_permission

_REQUIRED = "article.create"


class RbacGuardController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        roles = [r.strip() for r in (request.param("roles") or "reader").split(",") if r.strip()]
        result = load_rbac_contract(".")
        denied = require_contract_permission(result, roles, _REQUIRED)
        if denied is not None:
            return denied  # réponse 403 prête à renvoyer
        # … la route continue (ressource protégée)
```

### Comprendre ce code

- Le pattern est **explicite** : on appelle la garde, et si elle renvoie une réponse,
  on la retourne immédiatement (court-circuit `403`).
- En production, les **rôles viennent de l'utilisateur connecté**, pas de l'URL —
  ici on les passe en paramètre pour la démonstration.
- La permission requise est déclarée **une fois**, en tête de l'action.

## À retenir

- `require_contract_permission` = garde de route, `403` ou passage.
- Court-circuit explicite : `if denied is not None: return denied`.
- Les rôles réels proviennent de la session/utilisateur.

## Après ce starter

La suite : adapter l'**interface** aux permissions.

[Permission dans un template](rbac-template.md)
