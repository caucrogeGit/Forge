# Enregistrer un événement

Objectif : **enregistrer** un événement, via un exécuteur injectable.

**Ce que vous allez apprendre :** `track_event` prend un **exécuteur** (`execute`)
plutôt que d'accéder directement à la base — ce qui le rend testable. La démo injecte
un exécuteur factice ; en production on passe `core.database.db.execute`.

Deuxième palier du **niveau intermédiaire** de la progression stats.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-stats` installé. **Aucune base réelle** : l'exécuteur
    de démo capture la requête.

## Ce que ce starter montre

- un exécuteur de démonstration injecté ;
- `track_event(execute, event)` ;
- la requête qui aurait été exécutée.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_stats.track_event` | Enregistrer un événement via un exécuteur. | [Stats](../../../reference/api.md) |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/stats-track` : la requête capturée par l'exécuteur de démo.

## Le contrôleur

```python
# mvc/controllers/stats_track_controller.py
from forge_mvc_stats import make_event, track_event


class StatsTrackController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        captured = []
        def _demo_execute(sql, params):
            captured.append({"sql": sql, "params": list(params)})
            return 1
        event = make_event("page_view", "Vue de page", "navigation", {"path": "/"})
        track_event(_demo_execute, event)
        # en production : track_event(core.database.db.execute, event)
```

### Comprendre ce code

- L'**injection** de l'exécuteur découple Forge Stats de la base : testable sans
  MariaDB, branché en une ligne en production.
- Le même motif que la résolution RBAC (`fetch_all` injecté) : le code métier reste pur.
- En production : `track_event(core.database.db.execute, event)`.

## À retenir

- `track_event(execute, event)` enregistre via un exécuteur injectable.
- Découplage de la base = code testable.
- En production, on passe l'exécuteur réel du core.

## Après ce starter

La suite : **valider** un événement avant de l'écrire.

[Valider un événement](stats-validate.md)
