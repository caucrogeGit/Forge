# Avancé 2 — Valider et livrer

Objectif : garder le projet sain avant de livrer.

```bash
python -m pytest
forge doctor
ruff check .
```

Pour la mise en production, Forge documente une stratégie de déploiement
(serveur WSGI, service système, reverse proxy).

## Pour approfondir

Le guide de déploiement :
https://forgemvc.com/docs/forge/deployment/deployment/

## Étape suivante

[Bilan du niveau avancé](bilan.md)
