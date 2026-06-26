# forge-mvc-deploy

Outillage de déploiement opt-in du framework Forge.

`forge-mvc-deploy` ajoute les commandes `forge deploy:init` et
`forge deploy:check` une fois installé. C'est un opt-in **à CLI seule** :
il n'expose aucune API runtime, une application ne l'importe jamais à
l'exécution.

## Pourquoi un opt-in

Le déploiement est de l'outillage d'exploitation, pas du runtime de framework.
Ses gabarits (Nginx, systemd, Gunicorn) sont opinionés.
Les mettre en opt-in rend cette opinion optionnelle, au lieu de l'imposer par
le cœur (principe 8, ADR-004).
Une application déployée autrement (Docker, Kubernetes, autre proxy) n'a pas à
l'installer.

Cette extraction est décidée par l'ADR-053 (`DEPLOY-EXTRACT-001`).

## Installation

```bash
pip install --pre forge-mvc-deploy
```

## Commandes

| Commande | Rôle |
|---|---|
| `forge deploy:init` | Génère `wsgi.py`, la configuration Nginx, l'unité systemd et un README de déploiement (write-if-new). |
| `forge deploy:check` | Vérifie l'environnement de production sans rien modifier. |

Voir la [référence des commandes](references/cli.md) et la progression
guidée (menu Progression Deploy).

## Mise en production

Le chemin de production officiel est Gunicorn derrière Nginx (HTTPS terminé par
le proxy, Forge en HTTP local).
La documentation complète de mise en production reste publiée dans la
documentation Forge, section Déploiement.
