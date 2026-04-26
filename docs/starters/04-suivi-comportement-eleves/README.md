# Starter 4 — Suivi Comportement Élèves

**Application démo :** outil d'observation pour enseignants — saisie par cours, synthèse par élève.

## Objectif

Construire une application métier plus dense : formulaires de saisie avec cases à cocher, upsert SQL (`ON DUPLICATE KEY UPDATE`), et tableau récapitulatif à double entrée élèves × cours.

## Fonctionnalités principales

- Gestion des élèves (`Eleve`) et des cours (`Cours`)
- Saisie d'observations par cours avec `ObservationCours`
- Upsert automatique — la même saisie peut être corrigée
- Tableau récapitulatif croisant élèves et cours (`CROSS JOIN` + accès dict)
- Cases à cocher générées pour chaque critère booléen
- Vue de synthèse en fin de cours

## Installation locale

```bash
forge new SuiviApp
cd SuiviApp
source .venv/bin/activate
forge doctor
forge db:init
# Créer les entités : Eleve, Cours, ObservationCours
forge build:model
forge db:apply
forge make:crud Eleve
forge make:crud Cours
# Créer manuellement ObservationCoursController et les vues métier
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
