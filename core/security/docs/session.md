# La session dans Forge

Ce document décrit l'API de session côté serveur : créer, lire, authentifier et faire tourner une session.

Le fichier de code correspondant est `core/security/session.py`.

## 1. À quoi sert ce module ?

Une session garde une mémoire entre deux requêtes d'un même visiteur (connexion, messages flash…).
Ce module gère le cycle de vie d'une session côté serveur, identifiée par un `session_id` transporté dans un cookie.

## 2. Cycle de vie

```python
from core.security.session import create_session, authenticate_session, regenerate_session

sid = create_session()
sid = regenerate_session(sid)          # après login : ferme la fixation de session
authenticate_session(sid, user)        # marque la session comme authentifiée
```

## 3. L'API

| Fonction | Rôle |
|---|---|
| `create_session()` | crée une session, retourne son identifiant |
| `get_session(session_id)` | les données de la session, ou `None` si absente/expirée |
| `delete_session(session_id)` | supprime la session (logout) |
| `regenerate_session(old_session_id)` | nouvel identifiant en conservant les données (anti-fixation) |
| `authenticate_session(session_id, user)` | marque la session authentifiée et y stocke l'utilisateur |
| `get_session_id(request)` | extrait et valide l'identifiant depuis le cookie |
| `is_authenticated(request)` | `True` si la requête provient d'un utilisateur authentifié |
| `get_user(request)` | l'utilisateur courant, ou `None` |
| `user_has_role(request, role)` | `True` si l'utilisateur a le rôle (RBAC léger, déprécié) |
| `set_flash(session_id, message, level="success")` | stocke un message flash (affiché une fois) |
| `get_flash(session_id)` | retourne et supprime le message flash |

## 4. La sécurité

- **Anti-fixation** : régénérer l'identifiant juste après le login (`regenerate_session`), puis réémettre le cookie.
- L'identifiant est validé à la lecture (`get_session_id`) : un identifiant malformé est rejeté.
- Le stockage par défaut est en mémoire (mono-processus) ; les backends de session sont dans `core/sessions/`.

## 5. Contextes d'utilisation

- **Login** : `authenticate_session` puis `regenerate_session` + réémission du cookie.
- **Garde** : `is_authenticated(request)` / `get_user(request)`.
- **Flash** : `set_flash` / `get_flash` autour d'une redirection.

## 6. Voir aussi

- [Les cookies de session](cookies.md) : transport de l'identifiant.
- [Les décorateurs de sécurité](decorators.md) : `require_auth`.
- [Les middlewares](middleware.md) : `AuthMiddleware`.
