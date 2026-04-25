# Starter 3 — Carnet de Contacts Relationnel

**Application démo :** carnet de contacts avec villes et groupes d'appartenance.

## Objectif

Lire et écrire un modèle relationnel Forge sans magie : `many_to_one` explicite, entité pivot `ContactGroupe` pour le many-to-many, et requêtes SQL avec `JOIN` visibles dans les modèles applicatifs.

## Fonctionnalités principales

- CRUD complet sur `Contact`
- Rattachement optionnel d'un contact à une `Ville` (`many_to_one`)
- Appartenance à des `Groupe`s via pivot `ContactGroupe` (many-to-many explicite)
- Listes de villes et groupes avec pages dédiées
- Sélecteur de ville dans le formulaire contact
- Requêtes SQL visibles dans les modèles (`JOIN`, `WHERE`, `IN`)

## Installation locale

```bash
forge new CarnetApp
cd CarnetApp
source .venv/bin/activate
forge doctor
forge db:init
# Créer les entités JSON : Contact, Ville, Groupe, ContactGroupe
forge build:model
forge db:apply
# Générer les CRUD : forge make:crud Contact, forge make:crud Ville, forge make:crud Groupe
# Câbler les routes dans mvc/routes.py
```

## Lancement

```bash
python app.py
# https://localhost:8000
```

## Démo en ligne

> *(lien à renseigner lors du déploiement)*

## Documentation complète

- [Guide complet du starter](../../starter-app-03-carnet-contacts.md)
- [Reconstruction pas à pas](rebuild.md)
