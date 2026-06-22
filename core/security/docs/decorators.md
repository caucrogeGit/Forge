# Les décorateurs de sécurité dans Forge

Ce document décrit les décorateurs qui protègent une action de contrôleur.

Le fichier de code correspondant est `core/security/decorators.py`.

## 1. À quoi sert ce module ?

Plutôt que de répéter les vérifications de sécurité dans chaque action, on les pose en **décorateurs**.
Ce module fournit les gardes d'authentification, de CSRF et de rôle.

## 2. L'API

| Décorateur | Rôle |
|---|---|
| `require_auth(func)` | redirige vers `/login` si l'utilisateur n'est pas authentifié |
| `require_csrf(func)` | retourne `403` si le jeton CSRF du formulaire ne correspond pas à la session |
| `require_role(role)` | redirige vers `/login` si non authentifié, `403` si le rôle est absent |

```python
from core.security.decorators import require_auth, require_csrf

@require_auth
@require_csrf
def update(request):
    ...
```

## 3. Notes

- `require_role` est le **RBAC léger** historique (lit le champ `roles` de la session) ; il est déprécié au profit du module de contrôle d'accès optionnel pour les permissions fines.
- `require_csrf` vérifie le jeton posé dans le formulaire contre celui de la session.

## 4. Contextes d'utilisation

- **Route protégée** : `@require_auth`.
- **POST sensible** : `@require_csrf`.

## 5. Voir aussi

- [La protection CSRF](csrf.md) : le mécanisme complet.
- [Les middlewares](middleware.md) : `AuthMiddleware`, `CsrfMiddleware`.
- [La session](session.md).
