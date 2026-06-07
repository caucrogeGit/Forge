# Associer un rôle à un utilisateur

Objectif : construire et valider l'association **utilisateur ↔ rôle**.

**Ce que vous allez apprendre :** `create_auth_user_role(user_id, role_id)` construit
et valide une association `AuthUserRole` que l'application persiste ensuite dans
`user_roles`.

Premier palier du **niveau avancé** de la progression RBAC.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-rbac` installé. La démo **ne persiste pas**
    l'association (pas de base).

## Ce que ce starter montre

- `create_auth_user_role(user_id, role_id)` → `AuthUserRole` validé ;
- la clé logique `user_id:role_id` ;
- la validation **sans** persistance (démo).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_rbac.create_auth_user_role` | Construire et valider une association user/role. | [RBAC](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/rbac-user-role?user_id=1&role_id=2`.

## Le contrôleur

```python
# mvc/controllers/rbac_user_role_controller.py
from forge_mvc_rbac import create_auth_user_role


class RbacUserRoleController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        user_id = int(request.query("user_id") or 1)
        role_id = int(request.query("role_id") or 2)
        association = create_auth_user_role(user_id, role_id)
        # association.user_id, association.role_id — à persister dans user_roles
```

### Comprendre ce code

- `create_auth_user_role` **valide** le couple (entiers positifs) et renvoie un objet
  ; il **ne touche pas la base**.
- La **persistance est le job de l'application** : on insère le couple dans
  `user_roles`.
- Une même personne peut cumuler plusieurs associations (plusieurs rôles).

## À retenir

- L'association user ↔ rôle est un **objet validé**, persisté par l'application.
- La table cible est `user_roles`.
- Le package valide ; il ne décide pas du stockage.

## Après ce starter

La suite : résoudre les permissions effectives d'un utilisateur.

[Résoudre les permissions d'un utilisateur](rbac-resolve.md)
