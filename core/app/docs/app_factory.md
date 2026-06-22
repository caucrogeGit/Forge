# La fabrique d'application dans Forge

Ce document décrit la construction de l'`Application` Forge.

Le fichier de code correspondant est `core/app/app_factory.py`.

## 1. À quoi sert ce module ?

Assembler une application demande plusieurs étapes : appliquer la configuration, brancher Jinja, charger les routes et les middlewares.
Ce module les regroupe dans une fabrique unique.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `apply_forge_config()` | applique la configuration Forge depuis `config.py` (idempotent) |
| `build_application()` | construit l'`Application` complète : config + Jinja + routes + middlewares |

```python
from core.app.app_factory import build_application

app = build_application()
```

## 3. Contextes d'utilisation

- **Démarrage** : `build_application()` au lancement (dev ou WSGI).
- **Tests** : `apply_forge_config()` pour initialiser la config sans serveur.

## 4. Voir aussi

- [L'application](application.md) : l'objet construit.
- [Les callables WSGI](wsgi.md) : qui appellent cette fabrique.
