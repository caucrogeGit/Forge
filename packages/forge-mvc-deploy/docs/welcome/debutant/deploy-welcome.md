# Premier déploiement

Objectif : premier contact avec le module **opt-in** `forge-mvc-deploy`.

**Ce que vous allez apprendre :** déployer une application Forge demande quelques fichiers de configuration toujours semblables (point d'entrée WSGI, reverse proxy Nginx, service systemd).
L'opt-in Deploy les génère pour vous, à adapter, puis vérifie l'environnement de production avant la mise en ligne.

Premier palier du **niveau débutant** de la progression Deploy.

!!! note "Module opt-in"
    Si `forge-mvc-deploy` n'est pas installé, les commandes `deploy:*` sont absentes.
    Le cœur de Forge, lui, ne dépend jamais de ce paquet.

## Pourquoi un opt-in de déploiement

Le chemin de production officiel de Forge est Gunicorn derrière Nginx.
Nginx termine HTTPS côté public, Forge écoute en HTTP local (`APP_SSL_ENABLED=false`).

Mettre cela en place à la main signifie écrire toujours les mêmes fichiers : un `wsgi.py`, une config Nginx, une unité systemd.
L'opt-in Deploy capture cette recette et la rend reproductible, sans rien écrire dans votre code applicatif.

## Ce que ce niveau montre

- générer les fichiers de déploiement avec `forge deploy:init` ;
- comprendre le mode write-if-new : aucun fichier existant n'est écrasé.

## Les deux commandes

| Commande | Rôle | Écrit ? |
|----------|------|---------|
| `forge deploy:init` | Génère les fichiers de déploiement. | Oui, write-if-new |
| `forge deploy:check` | Vérifie l'environnement de production. | Non, lecture seule |

## À retenir

- Déployer Forge suit une recette stable : Gunicorn derrière Nginx, service systemd.
- L'opt-in Deploy fournit deux commandes : `deploy:init` et `deploy:check`.
- Il n'écrit jamais dans votre code applicatif, seulement des fichiers de déploiement.

## Après ce starter

Vous savez à quoi sert l'opt-in.
Générons les fichiers de déploiement.

[Générer les fichiers](deploy-init.md)
