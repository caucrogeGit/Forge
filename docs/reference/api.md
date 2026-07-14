# API du cœur

L'API publique du cœur, regroupée par usage.
Chaque module a sa **page de référence dédiée** (rôle, schémas, signatures exactes, exemples) ; les liens ci-dessous y mènent.

!!! tip "Par où commencer"
    Une action de contrôleur type lit la requête avec [Request](../core-http/request.md), produit la réponse via [BaseController](../core-mvc/base_controller.md), et la renvoie sous forme de [Response](../core-http/response.md).

## Requête et réponse HTTP

La couche HTTP : recevoir une requête, router, produire une réponse.

- [Request](../core-http/request.md) : l'objet requête entrant (query, form, json, fichiers).
- [Response](../core-http/response.md) : l'objet réponse (texte, HTML, JSON, fichier).
- [Helpers de réponse](../core-http/helpers.md) : raccourcis de réponse.
- [Router](../core-http/router.md) : déclaration et résolution des routes.

## Contrôleurs et vues

Construire la réponse et rendre les gabarits.

- [BaseController](../core-mvc/base_controller.md) : la classe mère de tous les contrôleurs.
- [Templating](../core-templating/manager.md) : le rendu Jinja2 ([contrats](../core-templating/contracts.md)).
- [Pagination](../core-mvc/pagination.md) : listes paginées prêtes pour le gabarit.

## Formulaires et validation

Lire et valider les données entrantes.

- [Form](../core-forms/form.md) : formulaires applicatifs (`cleaned_data`, erreurs).
- [Champs](../core-forms/fields.md) : types de champs disponibles.
- [Validation d'upload](../core-forms/upload_validation.md) : extension, MIME, taille.
- [Décorateurs de validation](../core-validation/decorators.md) et [exceptions](../core-validation/exceptions.md).

## Base de données

Accès SQL explicite, sans ORM.

- [db](../core-database/db.md) : `fetch_one`, `fetch_all`, `execute`, `insert`.
- [Transaction](../core-database/transaction.md) : transactions explicites.
- [Chargeur SQL](../core-database/sql_loader.md) : charger les requêtes `.py`.
- [Connexion](../core-database/connection.md) : obtention de la connexion (backend).

## Sécurité

Les briques de sécurité par défaut.

- [Hachage de mots de passe](../core-security/hashing.md) (Argon2id) et [Auth API par jeton](../core-security/api_auth.md).
- [CSRF](../core-security/csrf.md), [CSP](../core-security/csp.md), [En-têtes de sécurité](../core-security/headers.md), [Cookies](../core-security/cookies.md).
- [Décorateurs](../core-security/decorators.md) et [middleware](../core-security/middleware.md).

## Sessions

Gestion des sessions et du store.

- [Gestionnaire de session](../core-sessions/manager.md) : API de session.
- [Contrat de store](../core-sessions/contract.md) : protocole `SessionStore`.
- [Clés de session](../core-sessions/keys.md) : conventions de clés.

## Authentification et utilisateurs

L'API officielle d'authentification (`core.auth`).

- [Utilisateur](../core-auth/user.md) : création, lecture, mot de passe.
- [Session d'authentification](../core-auth/session.md) : connexion et identité.
- [Mots de passe](../core-auth/password.md) : hachage et vérification.

## Configuration, application et modules

Le démarrage et l'assemblage du projet.

- [Registre de configuration `forge.py`](../core/forge_config.md) : `configure()` / `get()`.
- [Application](../core-app/application.md) et [fabrique d'application](../core-app/app_factory.md).
- [Système de modules](../core-modules/registry.md) : cycle de vie des modules.

## Erreurs runtime

- [Erreurs runtime](../core-errors/runtime_errors.md) : capture et format des erreurs.

## Voir aussi

- [CRUD explicite](../features/crud.md) : les fonctionnalités du CRUD généré (filtres, tri, export, HTMX).
- [Authentification](../features/auth.md) et [Relations entre entités](../features/relations.md).
- [Référence des commandes Forge](cli-commands.md) : le catalogue de la CLI.
- [Packages opt-in](../optins/index.md) : l'API au-delà du cœur.
