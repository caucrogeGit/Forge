# La session Auth/User dans Forge

Ce document décrit l'authentification et la session de l'utilisateur applicatif.

Le fichier de code correspondant est `core/auth/session.py`.

## 1. À quoi sert ce module ?

C'est l'**API canonique** d'authentification des nouveaux projets : authentifier un couple email/mot de passe, ouvrir et fermer la session, protéger une route.

## 2. L'API

```python
from core.auth import authenticate_user, login_user, login_required

user = authenticate_user(email, password, load_user_by_email)
if user:
    login_user(request, user)
```

| Fonction | Rôle |
|---|---|
| `authenticate_user(email, password, loader)` | authentifie via un loader applicatif ; retourne l'utilisateur ou `None` |
| `login_user(request, user)` | stocke l'identifiant en session |
| `logout_user(request)` | retire l'identifiant de la session |
| `get_authenticated_user_id(request)` | l'identifiant en session, ou `None` |
| `current_user(request, loader)` | l'utilisateur courant via un loader |
| `is_authenticated(request)` | `True` si la session contient un utilisateur |
| `login_required(func)` | décorateur : protège une action par la session Auth/User |

## 3. La sécurité

`login_user` ne régénère pas l'identifiant de session : juste après, l'application régénère l'identifiant et réémet le cookie pour fermer la fixation de session (voir [core/security/session](../core-security/session.md)).

## 4. Contextes d'utilisation

- **Connexion** : `authenticate_user` puis `login_user`.
- **Route protégée** : `@login_required`.

## 5. Voir aussi

- [Le mot de passe](password.md), [le contrat utilisateur](user.md).
- [La session (core/security)](../core-security/session.md) : la régénération et le cookie.
