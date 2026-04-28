# Starter 3 — Carnet de contacts

[Accueil](../../index.html){ .md-button }

**Application démo :** carnet de contacts avec villes.

## Objectif

Lire et écrire un modèle relationnel Forge sans magie : deux JSON canoniques, une relation globale `many_to_one`, un `relations.sql` visible et des requêtes applicatives avec `LEFT JOIN`.

## Fonctionnalités principales

- Entités `Ville` et `Contact`
- Relation `Contact.VilleId -> Ville.VilleId`
- CRUD Contact avec sélection de ville
- Liste simple des villes
- Script `scripts/seed_villes.py`
- SQL visible dans `mvc/models/contact_model.py`

## Installation locale

```bash
forge new CarnetApp
cd CarnetApp
source .venv/bin/activate
forge doctor
forge starter:build 3 --init-db
python scripts/seed_villes.py
python app.py
```

Alias disponibles : `carnet`, `carnet-contacts`.

## Notes

Les routes de ce starter sont publiques et sans protection CSRF. C'est un choix pédagogique pour rester centré sur les relations entre entités — pas une pratique recommandée pour la production. Dans une application réelle, les routes d'écriture devront être protégées.

Cette génération automatique ne crée pas encore `Groupe` ni `ContactGroupe`. Le pivot many-to-many explicite reste une évolution pédagogique possible.

## Documentation complète

- [Guide complet du starter](../../starter-app-03-carnet-contacts.md)
- [Reconstruction rapide](rebuild.md)
