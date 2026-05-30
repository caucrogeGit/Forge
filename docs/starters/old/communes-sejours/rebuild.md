# Reconstruction — Starter Communes & Séjours

## Prérequis

Un projet Forge existant créé avec `forge new`.

```bash
forge new MonProjet
cd MonProjet
source .venv/bin/activate
forge doctor
```

## Génération du starter

```bash
forge starter:build 5
```

Alias acceptés : `communes-sejours`, `communes`.

### Aperçu sans écriture

```bash
forge starter:build 5 --dry-run
```

### Forcer la réinstallation

```bash
forge starter:build 5 --force
```

## Démarrage immédiat

Le starter fonctionne **sans base de données** pour les pages publiques.

```bash
python app.py
```

Ouvrir : `http://localhost:8000/communes-sejours`

## Avec base de données (optionnel)

```bash
forge check:model
forge build:model
forge db:init
forge db:apply
```

## Fichiers générés

```
mvc/
  controllers/
    communes_sejours_controller.py
  entities/
    commune/commune.json
    proprietaire/proprietaire.json
    hebergement/hebergement.json
    demande_sejour/demande_sejour.json
    relations.json
  forms/
    demande_sejour_form.py
  mail/templates/communes_sejours/
    demande_visiteur_subject.txt
    demande_visiteur_text.txt
    demande_proprietaire_subject.txt
    demande_proprietaire_text.txt
  views/public/communes_sejours/
    home.html
    hebergements_index.html
    hebergements_show.html
seed/
  communes.json
  proprietaires.json
  hebergements.json
  demandes_sejour.json
translations/
  fr.json
routes.py               (snippet injecté)
```

## Routes

| Méthode | Route | Rôle |
|---|---|---|
| `GET` | `/communes-sejours` | Accueil |
| `GET` | `/communes-sejours/hebergements` | Liste des hébergements |
| `GET` | `/communes-sejours/hebergements/{slug}` | Fiche hébergement |
| `POST` | `/communes-sejours/hebergements/{slug}/demande` | Soumission formulaire |

## Ce que ce starter démontre

- pages publiques (`make:public-page`, `make:public-list`, `make:public-show`, `make:public-form`) ;
- formulaire avec validation serveur et protection CSRF ;
- notifications mail (visiteur + gestionnaire) ;
- internationalisation via `trans()` (préfixe `starter.cs.*`) ;
- seed JSON consultable ;
- entités et relations (`many_to_one`).

## Limites assumées

Ce starter est un **démonstrateur**, pas une application métier complète.

Non livré : réservation confirmée, paiement, calendrier, espace propriétaire, back-office, authentification spécifique.

Voir la [présentation complète](index.md) pour le détail des limites.
