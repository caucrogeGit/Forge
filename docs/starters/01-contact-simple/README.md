# Starter 1 — Contact Simple

**Application démo :** carnet de contacts minimaliste sur une seule entité.

## Objectif

Apprendre le cycle complet d'un CRUD Forge : définition JSON, génération SQL, contrôleur et vues Jinja2, validation de formulaire, messages flash.

## Fonctionnalités principales

- Lister, créer, afficher, modifier et supprimer un contact
- Formulaire avec validation (nom obligatoire, email optionnel)
- Messages flash après chaque action
- Routes RESTful protégées par CSRF
- Vues générées par `forge make:crud`, modifiables librement

## Installation locale

```bash
forge new ContactApp
cd ContactApp
source .venv/bin/activate
forge doctor
forge db:init
forge make:entity Contact --no-input
# Éditer mvc/entities/contact/contact.json — ajouter nom, email, telephone
forge build:model
forge db:apply
forge make:crud Contact
# Ajouter le bloc de routes dans mvc/routes.py
```

## Lancement

```bash
python app.py
# https://localhost:8000
```

## Démo en ligne

> *(lien à renseigner lors du déploiement)*

## Documentation complète

- [Guide complet du starter](../../starter-app-01-contacts.md)
- [Reconstruction pas à pas](rebuild.md)
