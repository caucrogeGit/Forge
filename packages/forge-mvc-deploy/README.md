# forge-mvc-deploy

Outillage de déploiement opt-in pour le framework Forge.

## Statut : Beta — opt-in officiel

`forge-mvc-deploy` est marqué `Development Status :: 4 - Beta`.
Le module a été extrait du cœur par l'ADR-053 (`DEPLOY-EXTRACT-001`).

C'est un **opt-in à CLI seule** : il ajoute les commandes `forge deploy:init`
et `forge deploy:check` une fois installé. Il n'expose **aucune API runtime** ;
une application ne l'importe jamais à l'exécution.

## Pourquoi un opt-in

Le déploiement est de l'outillage d'exploitation, pas du runtime de framework.
Ses gabarits (Nginx, systemd, Gunicorn) sont opinionés : les mettre en opt-in
rend cette opinion optionnelle, au lieu de l'imposer par le cœur (principe 8,
ADR-004). Une application déployée en Docker ou en Kubernetes n'a pas à
l'installer.

## Installation

```bash
pip install --pre forge-mvc-deploy
```

Pour développer le paquet en mode éditable depuis les sources du dépôt Forge :

```bash
pip install -r requirements-dev.txt  # installe forge-mvc-deploy depuis packages/
```

## Commandes

| Commande | Rôle |
|---|---|
| `forge deploy:init` | Génère `wsgi.py`, `deploy/nginx/forge-app.conf`, `deploy/systemd/forge-app.service` et `deploy/README_DEPLOY.md` dans le projet (écriture si nouveau, jamais d'écrasement). Ajoute `worker.py` et `deploy/systemd/forge-jobs-worker.service` quand `forge-mvc-jobs` est installé. |
| `forge deploy:check` | Vérifie l'environnement de production (Python, `.venv`, `env/prod`, variables DB, modules, `wsgi.py`, fichiers `deploy/`). Sort en code 1 si une erreur bloquante est détectée. |

`forge deploy:init` adapte `client_max_body_size` de la configuration Nginx à
`UPLOAD_MAX_SIZE` lu dans `config.py`. Les fichiers générés sont des modèles à
adapter à votre infrastructure.

## Déploiement

Le chemin de production officiel est Gunicorn derrière Nginx (HTTPS terminé par
le proxy, Forge en HTTP local). La documentation complète de mise en production
reste publiée dans la documentation Forge :
[forgemvc.com/docs/forge/deployment/](https://forgemvc.com/docs/forge/deployment/).

## Compatibilité

Disponible séparément depuis Forge 1.0.0-rc.1 (ADR-053, `DEPLOY-EXTRACT-001`).
Avant cette extraction, `deploy:init` et `deploy:check` faisaient partie du cœur
du CLI.
