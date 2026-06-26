# Indépendance du cœur

Objectif : comprendre pourquoi le cœur ne dépend pas de l'outillage de
déploiement.

**Ce que vous allez apprendre :** Forge Core ne dépend pas de
`forge-mvc-deploy`.
La dépendance va de l'opt-in vers le cœur, jamais l'inverse.
Vous pouvez déployer autrement, par exemple en conteneur, sans installer cet
opt-in : l'opinion Nginx/systemd/Gunicorn reste un choix, pas une obligation.

Deuxième palier du **niveau avancé** de la progression Deploy.

## Ce que ce starter montre

- la règle de dépendance de l'opt-in ;
- déployer sans cet opt-in (Docker, Kubernetes, autre) ;
- pourquoi l'opinion Nginx/systemd/Gunicorn est optionnelle.

## 1. La règle de dépendance

```text
Forge Core ne sait rien du déploiement.
forge-mvc-deploy fournit deploy:init et deploy:check.
L'application choisit comment et où elle est déployée.
```

- Aucun fichier du cœur n'importe `forge_mvc_deploy` : l'outillage reste à l'extérieur.
- L'opt-in dépend du cœur (il lit `config.py`, l'environnement) : c'est le sens autorisé.
- Retirer le paquet ne casse pas le cœur : il n'en a jamais dépendu.

## 2. Déployer autrement

```text
Conteneur Docker : votre propre image lance Gunicorn, sans deploy:init.
Kubernetes : vos manifestes décrivent le service et l'ingress.
Autre reverse proxy : Caddy, Traefik, Apache, à votre convenance.
```

### Comprendre ce code

- Les fichiers générés sont une commodité, pas un passage obligé.
- Une application conteneurisée fournit elle-même son point d'entrée et son reverse proxy.
- Le cœur de Forge tourne sous WSGI : tout serveur d'application WSGI convient.

## 3. Une opinion optionnelle

- Le chemin Gunicorn derrière Nginx est l'opinion officielle de Forge, documentée et testée.
- Cette opinion accélère la mise en production courante, sans l'imposer.
- Choisir un autre déploiement reste pleinement supporté : Forge n'enferme pas l'application.

## À retenir

- L'opt-in dépend du cœur, le cœur ignore l'opt-in.
- On peut déployer Forge en conteneur ou autrement, sans `forge-mvc-deploy`.
- L'opinion Nginx/systemd/Gunicorn est un raccourci recommandé, jamais une contrainte.

## Après ce starter

Vous avez fait le tour de l'outillage de déploiement.
Place au bilan du niveau avancé.

[Bilan avancé](bilan.md)
