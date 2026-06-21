# Le contrat RBAC dans Forge

Ce document décrit le chargement et l'usage du contrat déclaratif `mvc/security/rbac.json`.

Le fichier de code correspondant est `forge_mvc_rbac/contract.py`.

## 1. À quoi sert ce module ?

Plutôt que de coder les permissions en dur, on les déclare dans un fichier `mvc/security/rbac.json` : quels rôles existent, et quelles permissions chaque rôle accorde.
Ce module **charge** et **valide** ce contrat, puis offre des vérifications fondées dessus.

## 2. Charger le contrat

```python
from forge_mvc_rbac import load_rbac_contract

result = load_rbac_contract(".")
result.valid          # bool
result.roles_count    # int
result.errors         # list[RbacContractError]
```

`load_rbac_contract(project_root=".")` retourne un `RbacContractResult` décrivant la validité, l'existence, le chemin, les compteurs et les erreurs éventuelles.

## 3. Vérifier une permission contractuelle

| Fonction | Comportement |
|---|---|
| `get_contract_permissions(result, roles)` | l'ensemble des permissions accordées à ces rôles |
| `has_contract_permission(result, roles, permission)` | `True` si un des rôles détient la permission |
| `get_request_roles(request)` | les rôles de la requête / session courante |
| `require_contract_permission(result, roles, permission)` | retourne une `Response` 403 si la permission manque, sinon `None` |
| `require_contract_permission_for_request(request, permission, project_root=".")` | idem, en partant directement de la requête |
| `contract_permission_required(permission, project_root=".")` | décorateur opt-in protégeant une action |

## 4. Usage typique

```python
from forge_mvc_rbac import contract_permission_required

@contract_permission_required("article.publish")
def publish(request):
    ...
```

## 5. Les erreurs

`RbacContractError` décrit une erreur de validation du contrat (chemin + message) ; elles sont rassemblées dans `RbacContractResult.errors`.

## 6. Contextes d'utilisation

- **Démarrage** : `load_rbac_contract()` une fois, vérifier `result.valid`.
- **Garde de route** : `@contract_permission_required("...")`.

## 7. Voir aussi

- [Le cœur RBAC](rbac.md) : modèles et vérifications de base.
- [Le contrat RBAC séparé](../contract.md) : la structure du fichier `rbac.json`.
- [Vue d'ensemble RBAC](../reference.md).
