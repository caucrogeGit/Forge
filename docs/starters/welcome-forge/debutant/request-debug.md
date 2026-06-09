# Inspecter une requête

Objectif : visualiser le contenu d'une requête pour comprendre ce que Forge
reçoit.

**Ce que vous allez apprendre :** afficher les données de la requête avec
`Response.debug(request.data)`, une aide pédagogique disponible en
environnement de développement.

## Là où nous en sommes

`WelcomeController` porte déjà les méthodes des paliers 1 à 4, et
`mvc/routes.py` déclare les routes correspondantes jusqu'à
`/welcome/article/{id}`. Nous ajoutons une méthode et une route.

## L'ajout

Ajoutez cette méthode à la classe `WelcomeController` :

```python
    @staticmethod
    def debug(request: Request) -> Response:
        return Response.debug(request.data)
```

Puis ajoutez la route dans le groupe public de `mvc/routes.py`.

## Votre mvc/routes.py à ce stade

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.welcome_controller import WelcomeController

router = Router()

with router.group("", public=True) as public:
    public.add("GET", "/", HomeController.index, name="home-index")
    public.add("GET",  "/welcome", WelcomeController.index, name="welcome-index")
    public.add("GET",  "/welcome/hello", WelcomeController.hello, name="welcome-hello")
    public.add("GET",  "/welcome/html", WelcomeController.html, name="welcome-html")
    public.add("GET",  "/welcome/article/{id}", WelcomeController.article, name="welcome-article")
    public.add("GET",  "/welcome/debug", WelcomeController.debug, name="welcome-debug")
```

## Comprendre ce code

- `request.data` rassemble les données utiles de la requête courante.
- `Response.debug(...)` les présente sous forme de page HTML lisible, pensée
  pour l'inspection pendant le développement.
- Cette aide n'est active qu'en environnement de développement
  (`APP_ENV=dev`) ; en production elle répond `404`, pour ne jamais exposer
  les données d'une requête.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/welcome/debug` | la page de débogage (en `APP_ENV=dev`) |
| `https://localhost:8000/welcome/debug?x=1&y=2` | la même page, avec les paramètres affichés |

## À retenir

- `Response.debug(request.data)` est un outil d'inspection pédagogique.
- Il n'est disponible qu'en développement ; il répond `404` en production.
- À n'utiliser que pour comprendre, jamais comme réponse définitive.

Au palier suivant, nous renvoyons des données structurées au format JSON.

[Continuer avec Réponse JSON](json-response.md)
