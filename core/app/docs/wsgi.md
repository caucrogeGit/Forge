# Les callables WSGI dans Forge

Ce document décrit les points d'entrée WSGI pour servir Forge en production.

Le fichier de code correspondant est `core/app/wsgi.py`.

## 1. À quoi sert ce module ?

En production, Forge se sert derrière un serveur WSGI (Gunicorn) et un reverse proxy.
Ce module fournit les callables WSGI qui enveloppent l'`Application`.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `create_wsgi_app(application)` | callable WSGI dispatchant via une `Application` donnée |
| `create_configured_wsgi_app()` | construit l'`Application` configurée et retourne son callable WSGI |

```python
# wsgi.py du projet
from core.app.wsgi import create_configured_wsgi_app
app = create_configured_wsgi_app()
```

## 3. Contextes d'utilisation

- **Production** : `gunicorn wsgi:app` pointant sur `create_configured_wsgi_app`.

## 4. Voir aussi

- [La fabrique d'application](app_factory.md) et [l'application](application.md).
- Guide [Déploiement WSGI](../deployment/wsgi-deployment.md).
