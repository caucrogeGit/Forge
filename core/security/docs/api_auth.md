# L'authentification d'API par jeton dans Forge

Ce document décrit la protection minimale d'une route d'API par jeton Bearer.

Le fichier de code correspondant est `core/security/api_auth.py`.

## 1. À quoi sert ce module ?

Pour exposer une route d'API à des clients non navigateur, on la protège par un **jeton Bearer** statique plutôt que par une session.
Ce module fournit l'extraction, la vérification et un décorateur de garde.

## 2. L'API

| Élément | Rôle |
|---|---|
| `get_api_token_from_request(request)` | extrait le jeton Bearer de l'en-tête `Authorization`, ou `None` |
| `is_valid_api_token(request)` | `True` si le jeton correspond à `API_TOKEN` |
| `require_api_token(func)` | décorateur : protège une route d'API par jeton Bearer |

```python
from core.security.api_auth import require_api_token

@require_api_token
def api_index(request):
    ...
```

## 3. Notes

C'est une protection **minimale** (jeton statique). Une API exposée largement demande une gestion de jetons plus riche, à la charge de l'application.

## 4. Contextes d'utilisation

- **Route d'API interne** : `@require_api_token` derrière un jeton de configuration.

## 5. Voir aussi

- [Les décorateurs de sécurité](decorators.md) : les gardes de session.
- [Les helpers de réponse (core/http)](../core-http/helpers.md) : `api_success` / `api_error`.
