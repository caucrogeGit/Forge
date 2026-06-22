# Les en-têtes de sécurité dans Forge

Ce document décrit le helper qui pose les en-têtes HTTP de sécurité par défaut.

Le fichier de code correspondant est `core/security/headers.py`.

## 1. À quoi sert ce module ?

Forge applique des en-têtes HTTP de sécurité sur toutes les réponses (clickjacking, MIME sniffing, HSTS, CSP…).
Ce module centralise leur application en un seul point.

## 2. L'API

```python
from core.security.headers import apply_security_headers

apply_security_headers(headers, include_hsts=True, csp=build_csp_header())
```

| Fonction | Rôle |
|---|---|
| `apply_security_headers(headers, *, include_hsts, csp=None)` | pose les en-têtes de sécurité Forge par défaut sur le dict `headers` |

## 3. Les en-têtes posés

`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`, et `Content-Security-Policy` (si `csp` fourni).
`Strict-Transport-Security` (HSTS) n'est posé que si `include_hsts=True`.

Ces en-têtes sont des **garde-fous par défaut** : ils ne remplacent pas une configuration de déploiement complète ni une revue des gabarits.

## 4. Contextes d'utilisation

- **Réponses HTTP** : appelé en un point pour toutes les réponses (et le déploiement WSGI partage le même helper).

## 5. Voir aussi

- [Le nonce CSP](csp.md) : `build_csp_header` qui alimente l'en-tête CSP.
