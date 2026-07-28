# Le SQL d'insertion

Objectif : **voir** le SQL d'insertion d'un événement avant de l'exécuter.

**Ce que vous allez apprendre :** `get_track_event_sql` retourne l'`INSERT` paramétré ; `prepare_track_event_values` retourne le tuple de valeurs d'un événement (métadonnées sérialisées en JSON).
SQL visible, requête paramétrée (anti-injection).

Premier palier du **niveau intermédiaire** de la progression stats.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-stats` installé.

## Ce que ce starter montre

- `get_track_event_sql()` → l'`INSERT` ;
- `prepare_track_event_values(event)` → le tuple de valeurs ;
- une transformation **pure** (on montre, on n'exécute pas).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_stats.get_track_event_sql` | L'`INSERT` paramétré. | Stats |
| `forge_mvc_stats.prepare_track_event_values` | Le tuple de valeurs d'un événement. | Stats |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/stats-track-sql` : l'`INSERT` et ses valeurs.

## Le contrôleur

```python
# mvc/controllers/stats_track_sql_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import get_track_event_sql, make_event, prepare_track_event_values


class StatsTrackSqlController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        event = make_event("page_view", "Vue de page", "navigation", {"path": "/"})
        return BaseController.render(
            "stats_track_sql/index.html",
            context={
                "sql": get_track_event_sql(),
                "values": list(prepare_track_event_values(event)),
            },
            request=request,
        )
```

### Comprendre ce code

- Le SQL est **paramétré** (`?`) : les valeurs ne sont jamais concaténées (anti-injection).
- Les **métadonnées** (dict) sont sérialisées en JSON pour tenir dans une colonne texte.
- Voir le SQL avant de l'exécuter rend le comportement transparent (SQL visible).

## La vue

```html
<!-- mvc/views/stats_track_sql/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Le SQL d'insertion - Forge</title>
</head>
<body>
  <h1>Le SQL d'insertion</h1>

  <p>Requête <code>INSERT</code> paramétrée (SQL visible) :</p>
  <pre><code>{{ sql }}</code></pre>

  <p>Valeurs pour l'événement de démo :</p>
  <ul>
    {% for value in values %}<li><code>{{ value }}</code></li>{% endfor %}
  </ul>

  <p>Les <code>?</code> sont des paramètres liés (anti-injection) ; les métadonnées
  sont sérialisées en JSON.</p>
</body>
</html>
```

## La route

Dans `mvc/routes/__init__.py`, ajoutez l'import en tête de fichier et la route dans le groupe public.

```python
# mvc/routes/__init__.py
from mvc.controllers.stats_track_sql_controller import StatsTrackSqlController

with router.group("", public=True) as public:
    public.add("GET", "/stats-track-sql", StatsTrackSqlController.index, name="stats_track_sql_index")
```

## À retenir

- `get_track_event_sql` + `prepare_track_event_values` = SQL + valeurs, sans exécuter.
- Requête paramétrée, métadonnées en JSON.
- Transparence : on lit ce qui sera écrit.

## Après ce starter

La suite : **exécuter** cet enregistrement.

[Enregistrer un événement](stats-track.md)
