# Enregistrer un événement

Objectif : **enregistrer** un événement, via un exécuteur injectable.

**Ce que vous allez apprendre :** `track_event` prend un **exécuteur** (`execute`) plutôt que d'accéder directement à la base, ce qui le rend testable.
La démo injecte un exécuteur factice ; en production on passe `core.database.db.execute`.

Deuxième palier du **niveau intermédiaire** de la progression stats.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-stats` installé.
    **Aucune base réelle** : l'exécuteur de démo capture la requête.

## Ce que ce starter montre

- un exécuteur de démonstration injecté ;
- `track_event(execute, event)` ;
- la requête qui aurait été exécutée.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_stats.track_event` | Enregistrer un événement via un exécuteur. | Stats |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/stats-track` : la requête capturée par l'exécuteur de démo.

## Le contrôleur

```python
# mvc/controllers/stats_track_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

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
        return BaseController.render(
            "stats_track/index.html", context={"executed": captured[0]}, request=request
        )
```

### Comprendre ce code

- L'**injection** de l'exécuteur découple Forge Stats de la base : testable sans MariaDB, branché en une ligne en production.
- Le même motif que la résolution RBAC (`fetch_all` injecté) : le code métier reste pur.
- En production : `track_event(core.database.db.execute, event)`.

## La vue

```html
<!-- mvc/views/stats_track/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Enregistrer un événement - Forge</title>
</head>
<body>
  <h1>Enregistrer un événement</h1>

  <p data-level="success">Événement enregistré (via un exécuteur de démonstration).</p>

  <p>Requête exécutée :</p>
  <pre><code>{{ executed.sql }}</code></pre>
  <p>Paramètres :</p>
  <ul>
    {% for param in executed.params %}<li><code>{{ param }}</code></li>{% endfor %}
  </ul>

  <p>En production, on passe <code>core.database.db.execute</code> à
  <code>track_event</code> ; l'exécuteur injectable rend le code testable sans base.</p>
</body>
</html>
```

## La route

Dans `mvc/routes/__init__.py`, ajoutez l'import en tête de fichier et la route dans le groupe public.

```python
# mvc/routes/__init__.py
from mvc.controllers.stats_track_controller import StatsTrackController

with router.group("", public=True) as public:
    public.add("GET", "/stats-track", StatsTrackController.index, name="stats_track_index")
```

## À retenir

- `track_event(execute, event)` enregistre via un exécuteur injectable.
- Découplage de la base = code testable.
- En production, on passe l'exécuteur réel du core.

## Après ce starter

La suite : **valider** un événement avant de l'écrire.

[Valider un événement](stats-validate.md)
