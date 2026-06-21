# Le résolveur de permissions dans Forge RBAC

Ce document décrit la résolution d'un utilisateur vers ses permissions et rôles effectifs.

Le fichier de code correspondant est `forge_mvc_rbac/resolver.py`.

## 1. À quoi sert ce module ?

À partir d'un `user_id`, ce module calcule les **rôles** et les **permissions** effectifs de l'utilisateur, en lisant la base.
C'est la couche que [l'autorisation Auth/User](authorization.md) utilise sous le capot.

Par défaut, **aucun accès** : un utilisateur sans rôle n'a aucune permission.

## 2. L'API

| Fonction | Comportement |
|---|---|
| `get_user_permissions(user_id, *, fetch_all=None)` | les permissions effectives de `user_id`, sans doublon |
| `get_user_role_ids(user_id, *, fetch_all=None)` | les `role_id` associés à `user_id`, sans doublon |
| `user_has_permission(user_id, permission, *, fetch_all=None)` | `True` si `user_id` possède la permission |

`fetch_all` est injectable (tests) ; à défaut, la connexion du noyau est utilisée.

## 3. Usage typique

```python
from forge_mvc_rbac import get_user_permissions, user_has_permission

perms = get_user_permissions(user_id)
if user_has_permission(user_id, "article.publish"):
    ...
```

## 4. Les erreurs

`AuthUserRbacResolverError` signale une erreur explicite de résolution Auth/User vers RBAC.

## 5. Contextes d'utilisation

- **Décision serveur** : `user_has_permission(user_id, "...")`.
- **Affichage** : `get_user_permissions(user_id)` pour préparer un contexte.

## 6. Voir aussi

- [L'autorisation Auth/User](authorization.md) : la façade qui appelle ce résolveur.
- [Les liens utilisateur / rôle](user_rbac.md) : la donnée d'association résolue ici.
- [Vue d'ensemble RBAC](../reference.md).
