# Les commandes deploy:init et deploy:check

Ce document décrit les commandes `forge deploy:init` et `forge deploy:check`, fournies par l'opt-in `forge-mvc-deploy` (ADR-053).

Le fichier de code correspondant est `forge_mvc_deploy/cli/deploy.py`.

## 1. À quoi servent ces commandes ?

Elles préparent et contrôlent la configuration de déploiement d'un projet Forge.

`deploy:init` génère les gabarits de déploiement (Nginx, service systemd, point d'entrée WSGI, README de déploiement).
Quand `forge-mvc-jobs` est installé, il ajoute le point d'entrée du worker (`worker.py`) et son unité systemd.
Ces fichiers sont écrits en mode write-if-new : un fichier existant n'est jamais écrasé (principe 9).

`deploy:check` contrôle la cohérence de la configuration de déploiement sans rien modifier.
Elle restitue une liste de résultats tagués (`ok`, `warn`, `error`) et sort en code 1 si une erreur bloquante est détectée.

## 2. L'API

| Symbole | Rôle |
|---|---|
| `cmd_deploy_init(root=None)` | génère les gabarits de déploiement (write-if-new) |
| `cmd_deploy_check(root=None)` | contrôle la configuration de déploiement (lecture seule) |
| `main(args)` | point d'entrée dispatchant `deploy:init` / `deploy:check` |

La taille d'upload maximale est lue depuis `config.py` du projet pour calibrer `client_max_body_size` côté Nginx.

## 3. Contextes d'utilisation

- **Mise en production** : produire une base de configuration Nginx + systemd + WSGI à adapter.
- **Audit avant déploiement** : `deploy:check` signale une configuration incomplète ou incohérente.
- **Idempotence** : relancer `deploy:init` préserve les fichiers déjà personnalisés.

## 4. Opt-in à CLI seule

`forge-mvc-deploy` n'expose aucune API runtime.
Une application n'importe jamais `forge_mvc_deploy` à l'exécution : le paquet ne sert qu'à l'outillage de déploiement.
C'est le premier opt-in Forge de cette forme (voir aussi `forge-mvc-testing`, dev-only).

## 5. Voir aussi

- La documentation de mise en production complète (Gunicorn, Nginx, systemd, sécurité) reste publiée dans la documentation Forge, section Déploiement.
