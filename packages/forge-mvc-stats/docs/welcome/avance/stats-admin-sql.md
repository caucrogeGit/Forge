# Le SQL de consultation

Objectif : **voir** le SQL de lecture filtrable des événements.

**Ce que vous allez apprendre :** `get_stats_events_admin_sql` construit un `SELECT`
filtrable (nom, catégorie, limite) ; `prepare_stats_events_admin_params` fournit ses
paramètres liés. SQL visible, filtres paramétrés.

Premier palier du **niveau avancé** de la progression stats.

!!! note "Module opt-in"
    Ce starter suppose `forge-mvc-stats` installé (palier « Installation »).

## Ce que ce starter montre

- un filtre optionnel par catégorie ;
- `get_stats_events_admin_sql` → le `SELECT` ;
- `prepare_stats_events_admin_params` → ses paramètres.

## Classes Forge utilisées

| Classe / fonction | Rôle dans ce starter | Référence |
|-------------------|----------------------|-----------|
| `forge_mvc_stats.get_stats_events_admin_sql` | Le `SELECT` filtrable. | Stats |
| `forge_mvc_stats.prepare_stats_events_admin_params` | Les paramètres du `SELECT`. | Stats |

## Tester

```bash
forge run
```

Ouvrez `https://localhost:8000/stats-admin-sql?category=navigation` : le `SELECT` adapté.

## Le contrôleur

```python
# mvc/controllers/stats_admin_sql_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import get_stats_events_admin_sql, prepare_stats_events_admin_params


class StatsAdminSqlController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        category = request.query("category") or None
        return BaseController.render(
            "stats_admin_sql/index.html",
            context={
                "category": category or "(toutes)",
                "sql": get_stats_events_admin_sql(category=category, limit=20),
                "params": list(prepare_stats_events_admin_params(category=category, limit=20)),
            },
            request=request,
        )
```

### Comprendre ce code

- Le SQL **s'adapte aux filtres** fournis (nom, catégorie) tout en restant paramétré.
- Voir le `SELECT` avant de l'exécuter garde le comportement transparent (SQL visible).
- La **limite** protège contre les lectures non bornées.

## La vue

```html
<!-- mvc/views/stats_admin_sql/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Le SQL de consultation - Forge</title>
</head>
<body>
  <h1>Le SQL de consultation</h1>

  <form method="get" action="/stats-admin-sql">
    <label>Catégorie (optionnel) <input type="text" name="category"></label>
    <button type="submit">Construire le SELECT</button>
  </form>

  <p>Catégorie filtrée : <code>{{ category }}</code></p>

  <p>Requête <code>SELECT</code> (SQL visible) :</p>
  <pre><code>{{ sql }}</code></pre>
  <p>Paramètres :</p>
  <ul>{% for param in params %}<li><code>{{ param }}</code></li>{% endfor %}</ul>

  <p>Le SQL s'adapte aux filtres fournis, toujours en requête paramétrée.</p>
</body>
</html>
```

## La route

Dans `mvc/routes.py`, ajoutez l'import en tête de fichier et la route dans le groupe public.

```python
# mvc/routes.py
from mvc.controllers.stats_admin_sql_controller import StatsAdminSqlController

with router.group("", public=True) as public:
    public.add("GET", "/stats-admin-sql", StatsAdminSqlController.index, name="stats_admin_sql_index")
```

## À retenir

- `get_stats_events_admin_sql` + params = le `SELECT` filtrable, sans exécuter.
- Filtres paramétrés, limite par défaut.
- SQL visible aussi en lecture.

## Après ce starter

La suite : **exécuter** cette lecture et obtenir des événements.

[Lister les événements](stats-list.md)
