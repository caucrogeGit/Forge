# Starter 2 — Utilisateurs / authentification

**Application démo :** accueil public, connexion sécurisée, dashboard protégé, déconnexion.

## Objectif

Comprendre les mécanismes de sécurité Forge : sessions, hachage de mot de passe, routes publiques vs protégées, protection CSRF, et logout propre.

## Fonctionnalités principales

- Page d'accueil publique
- Formulaire de connexion avec login et mot de passe haché en PBKDF2-HMAC-SHA256
- Dashboard accessible uniquement après authentification
- Page profil utilisateur (lecture seule)
- Déconnexion et invalidation de session
- Routes publiques déclarées explicitement (`public=True`)
- CSRF actif sur tous les formulaires POST

## Installation locale

```bash
forge new AuthApp
cd AuthApp
source .venv/bin/activate
forge doctor
forge db:init
forge starter:build 2
python scripts/create_auth_user.py
```

Alias disponibles : `auth`, `utilisateurs`, `utilisateurs-auth`.
Ce starter ne génère pas un CRUD utilisateur ; il installe un flux applicatif login/dashboard/profil.

## Lancement

```bash
python app.py
# https://localhost:8000
```

## Démo en ligne

> *(lien à renseigner lors du déploiement)*

## Documentation complète

- [Guide complet du starter](../../starter-app-02-utilisateurs-auth.md)
- [Reconstruction pas à pas](rebuild.md)
