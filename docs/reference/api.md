# API du cœur

L'API publique du cœur est documentée **par module** : chaque module a sa page de référence dédiée (rôle, schémas UML, signatures exactes, exemples).
Ce catalogue y renvoie.

## Catalogue par module

| Domaine | Pages de référence détaillées |
|---|---|
| Configuration | [registre `forge.py`](../core/forge_config.md) |
| HTTP | [Request](../core-http/request.md), [Response](../core-http/response.md), [Helpers](../core-http/helpers.md), [Router](../core-http/router.md) |
| Sécurité | [Hashing](../core-security/hashing.md), [CSRF](../core-security/csrf.md), [Session](../core-security/session.md), [CSP](../core-security/csp.md), [Headers](../core-security/headers.md), [Cookies](../core-security/cookies.md), [Décorateurs](../core-security/decorators.md), [Auth API](../core-security/api_auth.md), [Middleware](../core-security/middleware.md) |
| Sessions | [Manager](../core-sessions/manager.md), [Contrat](../core-sessions/contract.md), [Clés](../core-sessions/keys.md) |
| Base de données | [db](../core-database/db.md), [Transaction](../core-database/transaction.md), [SQL loader](../core-database/sql_loader.md), [Connexion](../core-database/connection.md) |
| Formulaires | [Form](../core-forms/form.md), [Champs](../core-forms/fields.md), [Validation d'upload](../core-forms/upload_validation.md) |
| Validation | [Décorateurs](../core-validation/decorators.md), [Exceptions](../core-validation/exceptions.md) |
| Templating | [Manager](../core-templating/manager.md), [Contrats](../core-templating/contracts.md) |
| MVC | [BaseController](../core-mvc/base_controller.md), [Pagination](../core-mvc/pagination.md), [Validator](../core-mvc/validator.md) |
| Erreurs runtime | [Erreurs runtime](../core-errors/runtime_errors.md) |
| Application | [Application](../core-app/application.md), [Fabrique](../core-app/app_factory.md) |
| Modules | [Système de modules](../core-modules/registry.md) |
| Auth / User | [User](../core-auth/user.md), [Session auth](../core-auth/session.md), [Mots de passe](../core-auth/password.md) |

## Voir aussi

- [Le contrôleur de base (BaseController)](../core-mvc/base_controller.md) : la surface complète des contrôleurs.
- [CRUD explicite](../features/crud.md) : les fonctionnalités du CRUD généré (filtres, tri, export, HTMX).
- [Authentification](../features/auth.md) et [Relations entre entités](../features/relations.md).
- [Référence des commandes Forge](cli-commands.md) : le catalogue de la CLI.
