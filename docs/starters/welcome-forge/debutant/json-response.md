# Réponse JSON

Objectif : renvoyer des données structurées plutôt qu'une page HTML ou du
texte.

**Ce que vous allez apprendre :** produire une réponse JSON avec
`Response.json({...})`, utile pour une API ou un échange machine à machine.

## Là où nous en sommes

`WelcomeController` porte déjà les méthodes des paliers 1 à 5, et
`mvc/routes.py` déclare les routes jusqu'à `/welcome/debug`. Nous ajoutons
une méthode et une route.

## L'ajout

Ajoutez cette méthode à la classe `WelcomeController` :

```python
    @staticmethod
    def json(request: Request) -> Response:
        return Response.json(
            {
                "framework": "Forge",
                "message": "Bonjour JSON",
                "items": ["alpha", "beta", "gamma"],
            }
        )
```

Puis ajoutez la route dans le groupe public de `mvc/routes.py`.

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
    pub.add("GET",  "/welcome/debug", WelcomeController.debug, name="welcome-debug")
    pub.add("GET",  "/welcome/json", WelcomeController.json, name="welcome-json")
```

## Comprendre ce code

- `Response.json({...})` sérialise un dictionnaire Python en JSON et fixe
  l'en-tête `Content-Type: application/json`.
- Les structures imbriquées (listes, dictionnaires) sont prises en charge,
  comme la liste `items` ci-dessus.
- C'est la réponse adaptée à une API : un consommateur peut analyser le
  résultat sans extraire de données d'une page HTML.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/welcome/json` | le document JSON `{"framework": "Forge", ...}` |

## À retenir

- `Response.json({...})` renvoie des données structurées en JSON.
- Le type de contenu est positionné automatiquement.
- À privilégier pour les échanges machine à machine plutôt que du texte.

Au palier suivant, nous préparons les formulaires en découvrant le jeton CSRF.

[Continuer avec Le jeton CSRF](csrf.md)
