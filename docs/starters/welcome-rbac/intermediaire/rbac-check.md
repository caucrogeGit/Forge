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
| `forge_mvc_rbac.has_contract_permission` | Vérifier une permission pour des rôles selon le contrat. | [RBAC](../../../reference/api.md) |
| `forge_mvc_rbac.load_rbac_contract` | Charger le contrat. | [RBAC](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-check?roles=reader&permission=article.create`
(refusée), puis `roles=editor` (accordée).

## Le contrôleur

```python
# mvc/controllers/rbac_check_controller.py
from forge_mvc_rbac import has_contract_permission, load_rbac_contract


class RbacCheckController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        roles = [r.strip() for r in (request.query("roles") or "reader").split(",") if r.strip()]
        permission = request.query("permission") or "article.create"
        result = load_rbac_contract(".")
        granted = has_contract_permission(result, roles, permission)
        return BaseController.render("rbac_check/index.html",
            context={"roles": ",".join(roles), "permission": permission, "granted": granted}, request=request)
```

### Comprendre ce code

- La vérification est **pure** : rôles + permission + contrat → booléen. Aucune base,
  aucune session.
- Un utilisateur peut cumuler plusieurs rôles : `has_contract_permission` agrège.
- C'est la brique que `require_contract_permission` (guard) et `can()` (template)
  utilisent.

## À retenir

- `has_contract_permission` répond à « ces rôles ont-ils ce droit ? ».
- Le contrat est la **source de vérité** unique.
- Cette brique alimente guards et templates.

## Après ce starter

La suite : transformer cette vérification en **garde de route**.

[Protéger une route](rbac-guard.md)
