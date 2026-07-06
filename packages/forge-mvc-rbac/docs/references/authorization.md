# L'autorisation Auth/User dans Forge RBAC

Ce document décrit les vérifications de permission liées à l'utilisateur connecté.

Le fichier de code correspondant est `forge_mvc_rbac/authorization.py`.

## 1. À quoi sert ce module ?

C'est le pont entre l'utilisateur authentifié (Auth/User) et le RBAC : il répond à la question « l'utilisateur **connecté** a-t-il cette permission ?
».

## 2. L'API

| Fonction | Comportement |
|---|---|
| `auth_user_can(request, permission, *, fetch_all=None, permission_checker=None)` | `True` si l'utilisateur Auth/User connecté possède la permission |
| `require_user_permission(permission, *, fetch_all=None, permission_checker=None)` | décorateur protégeant une route avec les permissions de l'utilisateur connecté |

Les paramètres `fetch_all` et `permission_checker` sont **injectables** : utiles pour les tests, à défaut le résolveur standard est utilisé.

## 3. Usage typique

```python
from forge_mvc_rbac import auth_user_can, require_user_permission

@require_user_permission("article.publish")
def publish(request):
    ...

if auth_user_can(request, "article.delete"):
    ...
```

## 4. Contextes d'utilisation

- **Garde de route** : `@require_user_permission("...")` sur une action.
- **Logique fine** : `auth_user_can(request, "...")` pour une décision dans le code.

## 5. Voir aussi

- [Le résolveur de permissions](resolver.md) : la résolution `user_id` vers permissions sous-jacente.
- [Le cœur RBAC](rbac.md) : les vérifications fondées sur la requête.
- [Vue d'ensemble RBAC](../reference.md).
