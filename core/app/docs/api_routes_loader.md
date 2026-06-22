# Le chargeur de routes d'API dans Forge

Ce document décrit le chargement optionnel des routes d'API du projet.

Le fichier de code correspondant est `core/app/api_routes_loader.py`.

## 1. À quoi sert ce module ?

Un projet peut exposer des routes d'API séparées dans `mvc/api_routes.py`.
Ce module charge ce fichier **s'il existe** et y branche les routes, sans le rendre obligatoire.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `load_api_routes(...)` | charge `mvc/api_routes.py` si présent et appelle `register_api_routes` |

## 3. Contextes d'utilisation

- **Démarrage** : appelé par la fabrique d'application pour brancher les routes d'API du projet si elles existent.

## 4. Voir aussi

- [La fabrique d'application](app_factory.md).
- [Le routeur (core/http)](../core-http/router.md).
