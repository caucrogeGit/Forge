# Les cookies de session dans Forge

Ce document décrit la pose et l'invalidation du cookie de session.

Le fichier de code correspondant est `core/security/cookies.py`.

## 1. À quoi sert ce module ?

L'identifiant de session voyage entre le navigateur et le serveur dans un cookie.
Ce module pose ce cookie de façon **durcie** par défaut et l'invalide au logout.

## 2. L'API

```python
from core.security.cookies import set_session_cookie, clear_session_cookie

set_session_cookie(response, session_id)   # à la connexion / régénération
clear_session_cookie(response)             # au logout
```

| Fonction | Rôle |
|---|---|
| `set_session_cookie(response, session_id, *, secure=True, same_site="Strict", path="/", max_age=None, cookie_name="__Host-session_id")` | écrit l'en-tête `Set-Cookie` de session |
| `clear_session_cookie(response, *, secure=True, same_site="Strict", path="/", cookie_name="__Host-session_id")` | invalide le cookie de session |

## 3. Le durcissement par défaut

Le cookie est posé avec des réglages sûrs par défaut :

- préfixe **`__Host-`** : exige `Secure`, `path=/`, pas de `Domain` (cookie lié à l'hôte exact) ;
- **`HttpOnly`** : inaccessible au JavaScript ;
- **`SameSite=Strict`** : non envoyé en cross-site ;
- **`Secure`** : HTTPS uniquement.

## 4. Contextes d'utilisation

- **Connexion** : `set_session_cookie(response, sid)` après `regenerate_session`.
- **Déconnexion** : `clear_session_cookie(response)`.

## 5. Voir aussi

- [La session](session.md) : l'identifiant transporté par ce cookie.
- [Les en-têtes de sécurité](headers.md).
