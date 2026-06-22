# Les middlewares de sécurité dans Forge

Ce document décrit les middlewares d'authentification et de protection CSRF.

Le fichier de code correspondant est `core/security/middleware.py`.

## 1. À quoi sert ce module ?

Un middleware s'intercale dans le traitement de chaque requête.
Ce module fournit deux gardes transverses : exiger une session authentifiée, et vérifier le jeton CSRF des requêtes non sûres.

## 2. L'API

| Middleware | Rôle |
|---|---|
| `AuthMiddleware(login_url="/login")` | vérifie qu'une session authentifiée est présente, redirige sinon |
| `CsrfMiddleware(field_name="csrf_token", header_name="X-CSRF-Token")` | vérifie le jeton CSRF d'une requête non sûre déclarée protégée |

## 3. La protection CSRF

`CsrfMiddleware` est le cœur de la défense CSRF de Forge :

- il vérifie les requêtes **non sûres** (POST, PUT, PATCH, DELETE) déclarées protégées (`csrf=True` sur la route) ;
- le jeton est lu dans le champ de formulaire `csrf_token` ou l'en-tête `X-CSRF-Token`, et comparé à celui de la session ;
- en absence ou non-correspondance, la requête est refusée (`403`).

Le décorateur [`require_csrf`](decorators.md) couvre le cas par action ; le middleware couvre le cas transverse.

## 4. Contextes d'utilisation

- **Application** : enregistrer `AuthMiddleware` + `CsrfMiddleware` au câblage.
- **Routes publiques** : exemptées d'auth ; les routes `csrf=False` (API) ne passent pas par la vérification CSRF.

## 5. Voir aussi

- [La protection CSRF](csrf.md) : la vue d'ensemble du mécanisme.
- [Les décorateurs](decorators.md) : `require_auth`, `require_csrf`.
- [La session](session.md).
