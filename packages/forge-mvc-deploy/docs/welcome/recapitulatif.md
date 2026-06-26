# Aide-mémoire Deploy

Synthèse de l'outillage de `forge-mvc-deploy`, à garder sous la main.

## Les deux commandes

| Commande | Effet | Écrit ? |
|----------|-------|---------|
| `forge deploy:init` | Génère les fichiers de déploiement. | Oui, write-if-new |
| `forge deploy:check` | Vérifie l'environnement de production. | Non, lecture seule |

L'opt-in n'expose aucune API runtime : il n'ajoute que ces deux commandes CLI.

## Fichiers générés par deploy:init

| Fichier | Rôle |
|---------|------|
| `wsgi.py` | Point d'entrée WSGI, à la racine, lancé par Gunicorn. |
| `deploy/nginx/forge-app.conf` | Config Nginx en reverse proxy ; `client_max_body_size` calibré sur `UPLOAD_MAX_SIZE`. |
| `deploy/systemd/forge-app.service` | Unité systemd lançant Gunicorn. |
| `deploy/README_DEPLOY.md` | Marche à suivre pour la mise en production. |

Aucun fichier existant n'est écrasé (principe 9, pas d'écriture invisible).

## Ce que deploy:check contrôle

| Contrôle | Détail |
|----------|--------|
| Interpréteur | Python 3.12 ou supérieur. |
| Environnement | `.venv` présent, dossier `env/` présent. |
| Fichier de prod | `env/prod` et `DB_APP_HOST`, `DB_NAME`, `DB_APP_LOGIN`, `UPLOAD_ROOT`. |
| Cohérence TLS | HTTP/HTTPS Nginx en accord avec `APP_SSL_ENABLED`. |
| Modules | `mariadb`, `jinja2`, `gunicorn` importables. |
| Fichiers | `wsgi.py` et fichiers `deploy/` présents. |

Sortie en code 1 si une erreur bloquante existe.
Tags de résultat : `[OK]`, `[WARN]`, `[ERREUR]`.

## Checklist de mise en production

| Étape | Action |
|-------|--------|
| 1 | `forge deploy:init` puis adapter les gabarits. |
| 2 | Renseigner `env/prod` (DB, `UPLOAD_ROOT`, `APP_SSL_ENABLED=false`). |
| 3 | Régler systemd : `User`, `WorkingDirectory`, workers Gunicorn. |
| 4 | Régler Nginx : `server_name`, certificats TLS, `proxy_pass`. |
| 5 | `forge deploy:check` jusqu'à zéro `[ERREUR]`. |

## Rappel

Forge Core ne dépend pas du paquet.
L'opinion Nginx/systemd/Gunicorn est un raccourci recommandé : vous pouvez
déployer en conteneur ou autrement sans cet opt-in.
