# L'application dans Forge

Ce document décrit l'objet `Application`, cœur de l'exécution d'un projet Forge.

Le fichier de code correspondant est `core/app/application.py`.

## 1. À quoi sert ce module ?

`Application` orchestre une requête de bout en bout : routage, middlewares et contrôle d'accès.
C'est l'objet que le serveur (dev ou WSGI) appelle pour traiter chaque requête.

## 2. L'objet

| Élément | Rôle |
|---|---|
| `Application` | orchestre le routeur, les middlewares et la résolution de route vers une réponse |

On construit rarement `Application` à la main : on passe par [la fabrique](app_factory.md) (`build_application`) qui assemble config, Jinja, routes et middlewares.

## 3. Contextes d'utilisation

- **Serveur dev** : `python app.py` / `forge run` construit et sert une `Application`.
- **Production** : le [callable WSGI](wsgi.md) enveloppe une `Application`.

## 4. Voir aussi

- [La fabrique d'application](app_factory.md) : `build_application`.
- [Les callables WSGI](wsgi.md) : servir l'application en production.
- [Le routeur (core/http)](../core-http/router.md).
