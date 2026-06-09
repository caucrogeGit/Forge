# Paramètres d'URL

Objectif : lire une valeur passée dans l'adresse, par exemple `?name=Roger`.

**Ce que vous allez apprendre :** récupérer une valeur de la chaîne de
requête avec `request.query("name", default=...)`, avec une valeur de repli
quand le paramètre est absent.

## Là où nous en sommes

Votre `WelcomeController` possède déjà la méthode `index` (palier 1), et
`mvc/routes.py` déclare la route `/welcome`. Nous y ajoutons une méthode
et une route.

## L'ajout

Ajoutez cette méthode à la classe `WelcomeController` :

```python
    # Ajoutez ?name=Roger à l'URL, puis ouvrez /welcome/hello?name=Roger
    @staticmethod
    def hello(request: Request) -> Response:
        name = request.query("name", default="Forge")
        return Response.text(f"Bonjour {name}")
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
```

## Comprendre ce code

- La chaîne de requête est la partie après le `?` : `?name=Roger` porte la
  valeur `name=Roger`.
- `request.query("name", default="Forge")` lit cette valeur ; le second
  argument évite tout cas particulier « clé absente ».
- La valeur retournée est toujours de type `str` ; une conversion (entier,
  date) reste à votre charge dans le contrôleur.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/welcome/hello` | `Bonjour Forge` |
| `https://localhost:8000/welcome/hello?name=Roger` | `Bonjour Roger` |
| `https://localhost:8000/welcome/hello?name=Alice` | `Bonjour Alice` |

## À retenir

- `request.query(cle, default=...)` lit une valeur de la chaîne de requête.
- `default=...` est renvoyé si la clé est absente : pas d'exception, pas de
  `None` à gérer.
- La réponse reste un `Response.text(...)`, donc aucun template.

Au palier suivant, nous passons du texte brut à une vraie page HTML.

[Continuer avec Première vue HTML](first-html-view.md)
