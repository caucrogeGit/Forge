# Lister les événements

Objectif : **lire** les événements via un `fetch_all` injectable et obtenir des dicts propres.

**Ce que vous allez apprendre :** `list_stats_events` lit via un `fetch_all` **injectable** et retourne des dicts **normalisés** (métadonnées désérialisées).
La démo injecte un `fetch_all` factice.

Deuxième palier du **niveau avancé** de la progression stats.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-stats` installé.
    **Aucune base réelle** : le `fetch_all` de démo renvoie des lignes fixes.

## Ce que ce starter montre

- un `fetch_all` de démonstration injecté ;
- `list_stats_events(fetch_all, limit=...)` ;
- des événements normalisés en JSON.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_stats.list_stats_events` | Lire les événements via `fetch_all`, normalisés. | Stats |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/stats-list` : les événements de démo en JSON.

## Le contrôleur

```python
# mvc/controllers/stats_list_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import list_stats_events

# Lignes que renverrait la base (metadata est une chaîne JSON, comme en SQL).
_DEMO_ROWS = [
    {"id": 1, "name": "page_view", "label": "Vue de page", "category": "navigation",
     "metadata": '{"path": "/"}', "created_at": "2026-01-01T10:00:00"},
    {"id": 2, "name": "user_signup", "label": "Inscription", "category": "auth",
     "metadata": "{}", "created_at": "2026-01-01T11:00:00"},
]


def _demo_fetch_all(sql, params):
    return _DEMO_ROWS


class StatsListController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        events = list_stats_events(_demo_fetch_all, limit=20)
        return Response.json({"events": events})
```

### Comprendre ce code

- L'injection de `fetch_all` rend la lecture **testable** : vraie fonction en production, fausse en démo/test.
- Les **métadonnées** reviennent en **dict** (désérialisées du JSON stocké), prêtes à l'usage, sans retraitement côté appelant.
- En production : `list_stats_events(core.database.db.fetch_all, ...)`.

## La route

Dans `mvc/routes/__init__.py`, ajoutez l'import en tête de fichier et la route dans le groupe public.

```python
# mvc/routes/__init__.py
from mvc.controllers.stats_list_controller import StatsListController

with router.group("", public=True) as public:
    public.add("GET", "/stats-list", StatsListController.index, name="stats_list_index")
```

## À retenir

- `list_stats_events` lit via `fetch_all` injecté et normalise les lignes.
- Métadonnées désérialisées automatiquement.
- Testable sans base réelle.

## Après ce starter

Dernier palier : la normalisation d'une ligne brute, isolée.

[Normaliser une ligne](stats-normalize.md)
