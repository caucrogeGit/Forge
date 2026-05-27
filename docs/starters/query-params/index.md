# Paramètres d'URL

Objectif : lire une valeur passée dans l'URL avec `request.param(...)`.

Ce starter est identifié par `query-params` dans la CLI Forge
(aliases `query_params` / `params`). Il représente le **palier 2** de
la
[progression officielle des starters](../index.md#progression-recommandee),
juste après [Bonjour Forge](../welcome/index.md).

## Ce que ce starter installe

- une route `/query-params`
- une route `/query-params/hello`
- un contrôleur `QueryParamsController` avec deux méthodes
- aucune vue HTML
- aucune base de données

## Exemple

`/query-params/hello?name=Roger`

retourne :

`Bonjour Roger`

Sans paramètre, `/query-params/hello` retourne `Bonjour Forge` (valeur
par défaut).

## Les routes

```python
# mvc/routes.py
from mvc.controllers.query_params_controller import QueryParamsController

with router.group("", public=True) as pub:
    pub.add("GET", "/query-params",       QueryParamsController.index, name="query_params_index")
    pub.add("GET", "/query-params/hello", QueryParamsController.hello, name="query_params_hello")
```

## Le contrôleur

```python
# mvc/controllers/query_params_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class QueryParamsController(BaseController):
    """Starter pédagogique : lire des paramètres d'URL."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text(
            "Ajoutez ?name=Roger à l'URL, puis ouvrez /query-params/hello?name=Roger"
        )

    @staticmethod
    def hello(request: Request) -> Response:
        name = request.param("name", default="Forge")
        return Response.text(f"Bonjour {name}")
```

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `http://localhost:8000/query-params` | message d'aide |
| `http://localhost:8000/query-params/hello` | `Bonjour Forge` |
| `http://localhost:8000/query-params/hello?name=Roger` | `Bonjour Roger` |
| `http://localhost:8000/query-params/hello?name=Alice` | `Bonjour Alice` |

## À retenir

- `request.param(key, default=...)` lit une valeur de la *query string*
  (`?key=valeur`).
- Le second argument `default=...` est la valeur retournée si la clé
  est absente — pas d'exception, pas de `None` à manipuler.
- Le type retourné est toujours `str` (ou la valeur de `default`).
- Aucun template, aucun moteur de rendu : la réponse reste en
  `text/plain`.

## Après ce starter

Passez au palier suivant : **Première vue HTML**.

Vous y apprendrez à rendre une page HTML avec :

```python
BaseController.render(...)
```

[Continuer avec Première vue HTML](../first-html-view/index.md)
