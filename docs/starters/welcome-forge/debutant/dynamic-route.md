# Route dynamique

Objectif : capturer une partie variable du chemin de l'URL, par exemple un
identifiant d'article.

**Ce que vous allez apprendre :** déclarer une route avec un segment
dynamique `{id}` et lire ce segment avec `request.route_param("id", default=...)`.

## Là où nous en sommes

`WelcomeController` porte déjà `index`, `query_params_index`, `hello` et
`html_view` (paliers 1 à 3). Nous ajoutons une méthode et une route avec un
segment variable.

## L'ajout

Ajoutez cette méthode à la classe `WelcomeController` :

```python
    @staticmethod
    def show_article(request: Request) -> Response:
        article_id = request.route_param("id", default="inconnu")
        return Response.text(f"Article {article_id}")
```

Puis ajoutez la route avec son segment `{id}` dans le groupe public de
`mvc/routes.py`.

## Votre mvc/routes.py à ce stade

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.welcome_controller import WelcomeController

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET", "/", HomeController.index, name="home_index")
    pub.add("GET",  "/welcome", WelcomeController.index, name="welcome_index")
    pub.add("GET",  "/query-params", WelcomeController.query_params_index, name="query_params_index")
    pub.add("GET",  "/query-params/hello", WelcomeController.hello, name="query_params_hello")
    pub.add("GET",  "/first-html-view", WelcomeController.html_view, name="first_html_view_index")
    pub.add("GET",  "/dynamic-route/articles/{id}", WelcomeController.show_article, name="dynamic_route_article_show")
```

## Comprendre ce code

- `{id}` dans le chemin déclare un segment dynamique : il accepte n'importe
  quelle valeur à cet endroit de l'URL.
- `request.route_param("id", default="inconnu")` lit la valeur capturée par
  ce segment.
- C'est différent de `request.param(...)` du palier 2 : ici la valeur est
  dans le chemin lui-même, pas dans la chaîne de requête après le `?`.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/dynamic-route/articles/42` | `Article 42` |
| `https://localhost:8000/dynamic-route/articles/forge` | `Article forge` |

## À retenir

- Un segment `{nom}` dans le chemin capture une valeur variable.
- `request.route_param("nom", default=...)` lit cette valeur.
- Segment de chemin et chaîne de requête sont deux sources distinctes.

Au palier suivant, nous inspectons le contenu d'une requête pour le déboguer.

[Continuer avec Inspecter une requête](request-debug.md)
