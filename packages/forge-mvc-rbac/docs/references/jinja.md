# Les helpers Jinja dans Forge RBAC

Ce document décrit l'utilisateur public et le helper `can()` exposés aux gabarits.

Le fichier de code correspondant est `forge_mvc_rbac/jinja.py`.

## 1. À quoi sert ce module ?

Les gabarits ont besoin de deux choses : savoir **qui** est connecté, et **ce qu'il peut faire**.
Ce module expose un utilisateur public **sans secret** (ni hash de mot de passe) et un helper `can(permission)` pour l'affichage conditionnel.

## 2. L'utilisateur public (`AuthJinjaUser`)

```python
@dataclass
class AuthJinjaUser:
    id: int
    email: str | None = None
    is_active: bool | None = None
```

C'est une représentation **minimale** : jamais de mot de passe ni de secret côté gabarit.

## 3. L'API

| Fonction | Comportement |
|---|---|
| `get_jinja_current_user(request, *, user_loader=None)` | l'utilisateur public courant, ou `None` |
| `sanitize_jinja_user(user)` | réduit un utilisateur à sa représentation publique |
| `make_auth_jinja_can(request, ...)` | construit le helper `can(permission)` exposé aux gabarits |
| `make_auth_jinja_context(request, *, user_loader=None, ...)` | le contexte Auth/User standard pour Jinja |
| `make_auth_jinja_context_with_can(request)` | variante sans argument pour le registre du noyau |
| `make_contract_jinja_context(request, *, project_root=".", user_loader=None)` | contexte du modèle contrat (rbac.json) |

Avec un `user_loader` (ADR-080), `current_user` et `is_authenticated` reflètent l'**existence** du sujet : une session orpheline (un `user_id` sans compte, après réassignation d'identifiants par exemple) est vue non authentifiée, cohérent avec `AuthMiddleware`. Sans loader, valeur id-based (rétrocompatible). Le provider Jinja est la **source autoritaire** de `is_authenticated` dans le rendu : `BaseController.render` pose une valeur par défaut que le provider remplace.

## 4. Usage dans un gabarit

```jinja
{% if current_user %}
  Bonjour {{ current_user.email }}
  {% if can("article.publish") %}
    <a href="/article/publish">Publier</a>
  {% endif %}
{% endif %}
```

## 5. Contextes d'utilisation

- **Injection** : `make_auth_jinja_context(request)` au rendu d'une vue.
- **Affichage conditionnel** : `can("...")` dans le gabarit.

## 6. Voir aussi

- [Le cœur RBAC](rbac.md) : `make_can` sous-jacent à `can()`.
- [L'autorisation Auth/User](authorization.md).
- [Vue d'ensemble RBAC](../reference.md) : la section sur la chaîne de confiance.
