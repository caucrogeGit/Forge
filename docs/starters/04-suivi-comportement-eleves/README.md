# Starter 4 — Suivi Comportement Élèves

**Application démo :** outil d'observation pour enseignants — saisie par séance, synthèse par élève.

## Objectif

Construire une application métier plus dense : formulaires de saisie avec cases à cocher, upsert SQL (`ON DUPLICATE KEY UPDATE`), et tableau récapitulatif à double entrée élèves × séances.

## Fonctionnalités principales

- Gestion des élèves (`Eleve`) et des séances de cours (`Seance`)
- Saisie d'observations par séance : participation, attention, comportement, commentaire
- Upsert automatique — la même saisie peut être corrigée
- Tableau récapitulatif croisant élèves et séances (`CROSS JOIN` + accès dict)
- Cases à cocher générées pour chaque critère booléen
- Vue de synthèse en fin de séance

## Installation locale

```bash
forge new SuiviApp
cd SuiviApp
source .venv/bin/activate
forge doctor
forge db:init
# Créer les entités : Eleve, Seance, Observation
forge build:model
forge db:apply
forge make:crud Eleve
forge make:crud Seance
# Créer manuellement ObservationController et RecapController
# Voir le guide du starter pour la structure complète
```

## Lancement

```bash
python app.py
# https://localhost:8000
```

## Démo en ligne

> *(lien à renseigner lors du déploiement)*

## Documentation complète

- [Guide complet du starter](../../starter-app-04-suivi-comportement-eleves.md)
- [Reconstruction pas à pas](rebuild.md)
