# Les messages du serveur de dev dans Forge

Ce document décrit les messages de diagnostic et les gardes du serveur de développement.

Le fichier de code correspondant est `core/app/dev_server.py`.

## 1. À quoi sert ce module ?

Le serveur de développement affiche des messages au démarrage et **refuse** certaines configurations dangereuses (écoute publique en production).
Ce module construit ces messages et porte la logique de garde.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `format_startup_messages(...)` | lignes d'information affichées au démarrage |
| `scheme_for(ssl_flag)` | `https` ou `http` selon le drapeau SSL |
| `is_dangerous_public_host(host)` | `True` si l'hôte écoute sur toutes les interfaces |
| `should_block_prod_public_host(env, host)` | `True` si la combinaison doit déclencher le garde |
| `format_prod_host_guard_error(...)` | message quand `python app.py` refuse de démarrer (prod + hôte public) |
| `format_port_in_use_message(...)` | message lisible quand le bind échoue (`EADDRINUSE`) |

## 3. Le garde de production

Le serveur intégré est réservé au **développement**. En `APP_ENV=prod` sur un hôte public, il refuse de démarrer et oriente vers la stratégie WSGI (Gunicorn + reverse proxy).

## 4. Contextes d'utilisation

- **`python app.py` / `forge run`** : messages de démarrage et garde prod.

## 5. Voir aussi

- [Les callables WSGI](wsgi.md) : la voie de production.
- [Les avertissements de production](prod_warnings.md).
