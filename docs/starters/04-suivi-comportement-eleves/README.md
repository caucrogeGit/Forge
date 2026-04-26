# Starter 4 — Suivi pédagogique

**Vitrine Forge complète :** authentification, routes protégées, plusieurs entités, relations SQL, dashboard et seed de démonstration.

## Ce que ce starter démontre

- Login / logout avec session et CSRF actif
- Routes protégées par défaut — comportement standard Forge
- Trois entités générées depuis leurs JSON canoniques (`Eleve`, `Cours`, `ObservationCours`)
- Deux relations `many_to_one` déclarées dans `relations.json`, SQL visible dans `relations.sql`
- Dashboard protégé (`/suivi`) point d'entrée après connexion
- Seed de démonstration (`scripts/seed_suivi.py`) pour tester immédiatement

## Lancement rapide

```bash
forge starter:build 4   # disponible dans une prochaine version
```

En attendant, suivre le [guide complet](../../starter-app-04-suivi-comportement-eleves.md) ou le fichier [rebuild.md](rebuild.md) pour la reconstruction manuelle.

```bash
python app.py
# https://localhost:8000/suivi
```

## Documentation complète

- [Guide du starter 4](../../starter-app-04-suivi-comportement-eleves.md)
- [Reconstruction manuelle pas à pas](rebuild.md)
