# Starter 4 — Suivi pédagogique

[Accueil](../../index.html){ .md-button }

**Vitrine Forge complète :** authentification, routes protégées, plusieurs entités, relations SQL, dashboard et seed de démonstration.

## Ce que ce starter démontre

- Login / logout avec session et CSRF actif
- Routes protégées par défaut — comportement standard Forge
- Trois entités générées depuis leurs JSON canoniques (`Eleve`, `Cours`, `ObservationCours`)
- Deux relations `many_to_one` déclarées dans `relations.json`, SQL visible dans `relations.sql`
- Dashboard protégé (`/suivi`) point d'entrée après connexion
- Seed de démonstration (`scripts/seed_suivi.py`) pour tester immédiatement

## Installation locale

```bash
forge new SuiviApp
cd SuiviApp
source .venv/bin/activate
forge doctor
forge starter:build 4 --init-db
python scripts/create_auth_user.py
python scripts/seed_suivi.py
python app.py
# https://localhost:8000/suivi
```

Alias disponibles : `suivi`, `suivi-comportement-eleves`.

## Documentation complète

- [Guide du starter 4](../../starter-app-04-suivi-comportement-eleves.md)
- [Reconstruction manuelle pas à pas](rebuild.md)
