# Forge — Starter Apps

<div style="border:1px solid #FED7AA;background:linear-gradient(135deg,#FFF7ED 0%,#FFFFFF 58%,#F8FAFC 100%);border-radius:18px;padding:1.5rem 1.6rem;margin:1rem 0 1.5rem 0;">
  <p style="margin:0 0 .35rem 0;font-size:.85rem;font-weight:700;color:#EA580C;text-transform:uppercase;letter-spacing:.08em;">Forge · Parcours applicatifs</p>
  <h2 style="margin:.1rem 0 .45rem 0;font-size:2rem;line-height:1.15;color:#0F172A;">Starter apps</h2>
  <p style="margin:0;color:#334155;font-size:1.05rem;max-width:880px;">Des parcours progressifs pour apprendre Forge avec JSON canonique, SQL visible, contrôleurs explicites et routes ajoutées manuellement.</p>
</div>

Les starters sont d'abord des parcours pédagogiques. La génération automatique par `forge starter:build` est disponible pour les quatre starters.

## Vue D'ensemble

| Niveau | Starter | Objectif | Concepts |
|---|---|---|---|
| 1 | [Contacts](starter-app-01-contacts.md) | Créer un CRUD complet sur une seule entité | `make:entity`, `make:crud`, formulaires, flash |
| 2 | [Utilisateurs / authentification](starter-app-02-utilisateurs-auth.md) | Comprendre login, logout, sessions et routes protégées | sessions, CSRF, routes publiques/protégées |
| 3 | [Carnet de contacts](starter-app-03-carnet-contacts.md) | Lire un modèle relationnel explicite | `many_to_one`, `relations.json`, `JOIN` SQL |
| 4 | [Suivi pédagogique](starter-app-04-suivi-comportement-eleves.md) | Vitrine Forge complète avec auth, relations et dashboard | auth, routes protégées, `many_to_one`, seed de démo |

## Génération Automatique

```bash
forge starter:list
forge starter:build 1
forge starter:build contacts
forge starter:build contact-simple
forge starter:build 2
forge starter:build auth
forge starter:build utilisateurs-auth
forge starter:build 3
forge starter:build carnet
forge starter:build carnet-contacts
forge starter:build 4
forge starter:build suivi
forge starter:build suivi-comportement-eleves
```

Les alias `1`, `contacts` et `contact-simple` ciblent le même starter Contacts.
Les alias `2`, `auth`, `utilisateurs` et `utilisateurs-auth` ciblent le starter Utilisateurs / authentification.
Les alias `3`, `carnet` et `carnet-contacts` ciblent le starter Carnet de contacts.
Les alias `4`, `suivi` et `suivi-comportement-eleves` ciblent le starter Suivi pédagogique.

<div class="grid cards" markdown>

-   **Parcours**

    ---

    Les pages `starter-app-XX.md` expliquent les choix, le modèle et les étapes.

-   **Reconstruction**

    ---

    Les fichiers `rebuild.md` servent à reconstruire vite, sans répéter toute la pédagogie.

-   **Génération**

    ---

    La commande `forge starter:build` automatise les quatre starters. Utilisez `forge starter:list` pour voir les alias disponibles.

</div>

## Préparer Un Projet

```bash
git clone --branch v1.0.1 --depth=1 https://github.com/caucrogeGit/Forge.git NomDuProjet
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
| Contacts | [README](starters/01-contact-simple/README.md) | [rebuild.md](starters/01-contact-simple/rebuild.md) |
| Utilisateurs / authentification | [README](starters/02-utilisateurs-auth/README.md) | [rebuild.md](starters/02-utilisateurs-auth/rebuild.md) |
| Carnet de contacts | [README](starters/03-carnet-contacts/README.md) | [rebuild.md](starters/03-carnet-contacts/rebuild.md) |
| Suivi pédagogique | [README](starters/04-suivi-comportement-eleves/README.md) | [rebuild.md](starters/04-suivi-comportement-eleves/rebuild.md) |
