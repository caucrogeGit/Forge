# La commande make:auth dans Forge

Cette page décrit `forge make:auth`, qui scaffolde le flux de connexion d'un projet Forge.

Le code correspondant est `cli/security/make_auth.py`, sous-paquet CLI sécurité regroupé par l'ADR-043.

Le cœur redirige les routes protégées vers `/login` (codé en dur) et fournit le backend d'authentification (`core.auth.session`), mais ne scaffolde ni route, ni contrôleur, ni vue de login.
`make:auth` comble ce trou.

## 1. Rôle

`make:auth` génère un contrôleur d'authentification et une vue de login, puis affiche les routes à ajouter dans `mvc/routes/__init__.py`.

Il se place après `auth:init` : `auth:init` crée les comptes et le SQL, `make:auth` crée l'UI et le flux.

## 2. Ce qu'il génère

Écriture en mode write-if-new (aucun fichier existant n'est écrasé) :

- `mvc/controllers/auth_controller.py` : `login_form` (GET), `login` (POST), `logout` (POST) ;
- `mvc/views/auth/login.html` : le formulaire de connexion.

Les routes ne sont pas écrites dans `mvc/routes/__init__.py` : elles sont **affichées**, à coller (charte principe 9, Forge n'écrit pas en silence un fichier utilisateur).

## 3. Le flux généré

Le contrôleur s'appuie sur le socle standard `users` (produit par `forge auth:init`) :

- `login` : `authenticate_user(email, password, load_user_by_email)` du cœur, puis `login_user`, puis régénération de session anti-fixation (`regenerate_session`) et réémission du cookie ;
- `logout` : `logout_user`, suppression du cookie, redirection vers `/login`.

## 4. Prérequis

- `forge auth:init` puis `forge db:apply` pour créer la table `users` ;
- un compte applicatif : `forge auth:user:create`.

## 5. Limites

- version 1 sans MFA, ni rate-limit, ni audit : le contrôleur de référence `tests/fixtures/app/mvc/controllers/auth_controller.py` montre comment les ajouter ;
- les routes sont affichées, jamais injectées dans `mvc/routes/__init__.py`.

## Voir aussi

- [Commandes auth:*](auth.md) : socle et comptes d'authentification.
