# Les commandes deploy:init et deploy:check dans Forge

Ce document décrit les commandes `forge deploy:init` et `forge deploy:check`.

Le fichier de code correspondant est `cli/deploy/deploy.py`.

## 1. À quoi servent ces commandes ?

Elles préparent et contrôlent la configuration de déploiement d'un projet Forge.

`deploy:init` génère les gabarits de déploiement (Nginx, service systemd, point d'entrée WSGI, README de déploiement).
Ces fichiers sont écrits en mode write-if-new : un fichier existant n'est jamais écrasé (principe 9).

`deploy:check` contrôle la cohérence de la configuration de déploiement sans rien modifier.
Elle restitue une liste de résultats tagués (`ok`, `warn`, `error`).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `cmd_deploy_init(root=None)` | génère les gabarits de déploiement (write-if-new) |
| `cmd_deploy_check(root=None)` | contrôle la configuration de déploiement (lecture seule) |
| `main(args)` | point d'entrée dispatchant `deploy:init` / `deploy:check` |

La taille d'upload maximale est lue depuis l'environnement du projet pour calibrer `client_max_body_size` côté Nginx.

## 3. Contextes d'utilisation

- **Mise en production** : produire une base de configuration Nginx + systemd + WSGI à adapter.
- **Audit avant déploiement** : `deploy:check` signale une configuration incomplète ou incohérente.
- **Idempotence** : relancer `deploy:init` préserve les fichiers déjà personnalisés.

## 4. Voir aussi

- [Les commandes module:*](modules.md) : gestion des modules Forge locaux.
