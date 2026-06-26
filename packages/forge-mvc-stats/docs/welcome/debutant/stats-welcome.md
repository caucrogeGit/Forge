# Bonjour Forge Stats

Objectif : premier contact avec le module **opt-in** `forge-mvc-stats`.

**Ce que vous allez apprendre :** Forge Stats enregistre des **événements génériques**
(un nom, un libellé, une catégorie, des métadonnées) dans une table SQL.
`make_event` crée un événement ; `STATS_EVENTS_TABLE` / `STATS_EVENTS_COLUMNS`
décrivent le stockage.

Premier palier du **niveau débutant** de la progression stats
(vue d'ensemble des starters).

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-stats` installé (palier « Installation »). Module à
    **SQL visible** : aucun ORM.

## Ce que ce starter montre

- une route texte de **premier contact** (`GET /stats-welcome`) ;
- la table, les colonnes et un événement de démo (`GET /stats-welcome/inspect`).

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_stats.make_event` | Créer un événement (nom, libellé, catégorie, métadonnées). | Stats |
| `forge_mvc_stats.STATS_EVENTS_TABLE` / `STATS_EVENTS_COLUMNS` | Table et colonnes du stockage. | Stats |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/stats-welcome` puis `/stats-welcome/inspect`.

## Le contrôleur

```python
# mvc/controllers/stats_welcome_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import STATS_EVENTS_COLUMNS, STATS_EVENTS_TABLE, make_event


class StatsWelcomeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge Stats")

    @staticmethod
    def inspect(request: Request) -> Response:
        event = make_event("page_view", "Vue de page", "navigation", {"path": "/"})
        return Response.json({
            "table": STATS_EVENTS_TABLE,
            "columns": list(STATS_EVENTS_COLUMNS),
            "demo_event": {
                "name": event.name,
                "label": event.label,
                "category": event.category,
                "metadata": event.metadata,
            },
        })
```

### Comprendre ce code

- Un événement est **générique** : un nom, un libellé, une catégorie, et des
  métadonnées libres (un dict), pas de table par type d'événement.
- Le stockage est explicite (`STATS_EVENTS_TABLE`, colonnes) : Forge Stats est à
  **SQL visible**, sans ORM.
- `make_event` valide à la construction (le nom doit être valide).

## La route

Dans `mvc/routes.py`, ajoutez l'import en tête de fichier et les routes dans le groupe public.

```python
# mvc/routes.py
from mvc.controllers.stats_welcome_controller import StatsWelcomeController

with router.group("", public=True) as public:
    public.add("GET", "/stats-welcome", StatsWelcomeController.index, name="stats_welcome_index")
    public.add("GET", "/stats-welcome/inspect", StatsWelcomeController.inspect, name="stats_welcome_inspect")
```

## À retenir

- Forge Stats trace des **événements génériques** dans une table.
- Nom + libellé + catégorie + métadonnées (dict).
- SQL visible, aucun ORM.

## Après ce starter

Premier contact établi. La suite : la brique « nom d'événement ».

[Nom d'événement](stats-event.md)
