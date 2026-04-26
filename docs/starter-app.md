# Forge — Starter Apps

Cette page regroupe les parcours applicatifs Forge v1.0. Les starters sont progressifs et restent alignés avec la doctrine du framework : modèle canonique JSON visible, SQL explicite, contrôleurs et routes lisibles, aucune couche ORM implicite.

## Vue D'ensemble

| Niveau | Starter | Objectif | Concepts |
|---|---|---|---|
| 1 | [Contact simple](starter-app-01-contacts.md) | Créer un CRUD complet sur une seule entité | `make:entity`, `make:crud`, formulaires, flash |
| 2 | [Utilisateurs/auth](starter-app-02-utilisateurs-auth.md) | Comprendre login, logout, sessions et routes protégées | sessions, CSRF, routes publiques/protégées |
| 3 | [Carnet relationnel](starter-app-03-carnet-contacts.md) | Lire un modèle relationnel explicite | `many_to_one`, pivot explicite, `JOIN` SQL |
| 4 | [Suivi élèves](starter-app-04-suivi-comportement-eleves.md) | Construire une application métier plus dense | formulaires, cases à cocher, vues de synthèse |

## Préparer Un Projet

```bash
git clone --branch main --depth=1 https://github.com/caucrogeGit/Forge.git NomDuProjet
cd NomDuProjet
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp env/example env/dev
forge doctor
forge db:init
```

Adaptez `env/dev` avant `forge db:init` si vos identifiants MariaDB ou mots de passe diffèrent.

## Règles Communes

- Les entités vivent dans `mvc/entities/<entite>/<entite>.json`.
- `forge build:model` régénère les projections SQL et `*_base.py`.
- Les fichiers manuels existants ne sont jamais écrasés.
- `forge make:crud` génère un squelette modifiable, pas une administration automatique.
- Les routes affichées par `make:crud` sont à copier manuellement dans `mvc/routes.py`.
- Les relations directes supportées en V1 sont `many_to_one`.
- Le many-to-many passe par une entité pivot explicite.

## Fichiers De Reconstruction

Chaque starter dispose aussi d'un dossier de référence minimal :

| Starter | README | Reconstruction |
|---|---|---|
| Contact simple | [README](starters/01-contact-simple/README.md) | [rebuild.md](starters/01-contact-simple/rebuild.md) |
| Utilisateurs/auth | [README](starters/02-utilisateurs-auth/README.md) | [rebuild.md](starters/02-utilisateurs-auth/rebuild.md) |
| Carnet relationnel | [README](starters/03-carnet-contacts/README.md) | [rebuild.md](starters/03-carnet-contacts/rebuild.md) |
| Suivi élèves | [README](starters/04-suivi-comportement-eleves/README.md) | [rebuild.md](starters/04-suivi-comportement-eleves/rebuild.md) |
