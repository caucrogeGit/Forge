# Les liens utilisateur / rôle dans Forge RBAC

Ce document décrit l'association entre un utilisateur local et un rôle RBAC.

Le fichier de code correspondant est `forge_mvc_rbac/user_rbac.py`.

## 1. À quoi sert ce module ?

Un rôle ne sert à rien tant qu'il n'est rattaché à personne.
Ce module modélise le **lien** entre un utilisateur local et un rôle (`AuthUserRole`), et fournit la validation et la normalisation de ce lien.

## 2. Le modèle (`AuthUserRole`)

```python
@dataclass
class AuthUserRole:
    user_id: int
    role_id: int
    created_at: Any | None = None
```

C'est un lien **stockable** entre un utilisateur et un rôle RBAC.

## 3. Créer et valider

| Fonction | Comportement |
|---|---|
| `create_auth_user_role(user_id, role_id, *, created_at=None)` | construit une association valide |
| `normalize_auth_user_role(data)` | valide et normalise un dict brut ou un `AuthUserRole` |
| `is_valid_auth_user_role(association)` | `True` si l'association est valide |
| `validate_auth_user_role_contract(data)` | valide le contrat minimal |
| `validate_user_role_user_id(user_id)` | valide un identifiant utilisateur |
| `validate_user_role_role_id(role_id)` | valide un identifiant de rôle |

## 4. Comparer et indexer

| Fonction | Comportement |
|---|---|
| `user_role_key(user_id, role_id)` | la clé stable `user_id:role_id` |
| `auth_user_role_key(association)` | la clé d'une association normalisable |
| `auth_user_roles_match(left, right)` | compare deux associations par leur couple `(user_id, role_id)` |

## 5. Contextes d'utilisation

- **Attribution** : `create_auth_user_role(user_id, role_id)` puis persistance applicative.
- **Déduplication** : `user_role_key(...)` comme clé d'un ensemble.

## 6. Voir aussi

- [Le résolveur de permissions](resolver.md) : exploite ces liens pour calculer les permissions.
- [Le cœur RBAC](rbac.md) : les `Role` et `Permission` reliés.
- [Vue d'ensemble RBAC](../reference.md).
