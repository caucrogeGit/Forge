# Route dynamique

Objectif : capturer une partie variable du chemin de l'URL, par exemple un
identifiant d'article.

**Ce que vous allez apprendre :** déclarer une route avec un segment
dynamique `{id}` et lire ce segment avec `request.route("id", default=...)`.

## Là où nous en sommes

`WelcomeController` porte déjà `index`, `query_params`, `hello` et
`html` (paliers 1 à 3). Nous ajoutons une méthode et une route avec un
segment variable.

## L'ajout

Ajoutez cette méthode à la classe `WelcomeController` :

```python
    @staticmethod
    def article(request: Request) -> Response:
        article_id = request.route("id", default="inconnu")
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
    pub.add("GET", "/", HomeController.index, name="home-index")
    pub.add("GET",  "/welcome", WelcomeController.index, name="welcome-index")
    pub.add("GET",  "/welcome/query-params", WelcomeController.query_params, name="welcome-query_params")
    pub.add("GET",  "/welcome/hello", WelcomeController.hello, name="welcome-hello")
    pub.add("GET",  "/welcome/html", WelcomeController.html, name="welcome-html")
    pub.add("GET",  "/welcome/article/{id}", WelcomeController.article, name="welcome-article")
```

## Comprendre ce code

- `{id}` dans le chemin déclare un segment dynamique : il accepte n'importe
  quelle valeur à cet endroit de l'URL.
- `request.route("id", default="inconnu")` lit la valeur capturée par
  ce segment.
- C'est différent de `request.query(...)` du palier 2 : ici la valeur est
  dans le chemin lui-même, pas dans la chaîne de requête après le `?`.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/welcome/article/42` | `Article 42` |
| `https://localhost:8000/welcome/article/forge` | `Article forge` |

## À retenir

- Un segment `{nom}` dans le chemin capture une valeur variable.
- `request.route("nom", default=...)` lit cette valeur.
- Segment de chemin et chaîne de requête sont deux sources distinctes.

Au palier suivant, nous inspectons le contenu d'une requête pour le déboguer.

[Continuer avec Inspecter une requête](request-debug.md)
