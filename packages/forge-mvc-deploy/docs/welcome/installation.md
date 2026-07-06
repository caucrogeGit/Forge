# Installation de forge-mvc-deploy

Objectif : installer l'opt-in Deploy et préparer l'outillage de déploiement.

Le parcours qui suit montre, en trois niveaux, comment générer les fichiers de déploiement avec `forge deploy:init`, vérifier l'environnement de production avec `forge deploy:check`, adapter les gabarits Nginx et systemd, puis comprendre pourquoi cet outillage reste un opt-in indépendant du cœur.

## Installer le paquet

```bash
pip install --pre forge-mvc-deploy
```

En développement depuis les sources du dépôt, l'opt-in est inclus dans les dépendances de développement :

```bash
pip install -r requirements-dev.txt
```

Le paquet dépend du cœur `forge-mvc`.
Il n'ajoute aucune dépendance runtime : c'est un outillage en ligne de commande, jamais importé par l'application à l'exécution.

## Ce que l'opt-in ajoute

Une fois installé, `forge-mvc-deploy` ajoute deux commandes à la CLI `forge` :

```bash
forge deploy:init
forge deploy:check
```

`deploy:init` génère les fichiers de déploiement (point d'entrée WSGI, config Nginx, unité systemd, README).
`deploy:check` contrôle l'environnement de production sans rien modifier.

## Vérifier l'installation

```bash
forge deploy:check
```

Si la commande s'exécute et affiche des lignes taguées `[OK]`, `[WARN]` ou `[ERREUR]`, l'opt-in est bien en place.

## Après cette étape

Place au niveau débutant : générer vos premiers fichiers de déploiement.

[Niveau débutant : Premier déploiement](debutant/deploy-welcome.md)
