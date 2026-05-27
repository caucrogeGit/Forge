# Bonjour Forge

Premier contact avec Forge : afficher une réponse texte. Pas de vue HTML,
pas de base de données, pas de moteur Jinja2.

Identifiant : `welcome` (alias `bienvenue` / `bonjour` / `bonjour-forge`).

## Ce que ce starter installe

- une route `/welcome`
- une route `/welcome/greet`
- un contrôleur `WelcomeController` avec deux méthodes
- aucune vue HTML
- aucune base de données

## Les routes

```python
# mvc/routes.py
from mvc.controllers.welcome_controller import WelcomeController

with router.group("", public=True) as pub:
    pub.add("GET", "/welcome",       WelcomeController.index, name="welcome_index")
    pub.add("GET", "/welcome/greet", WelcomeController.greet, name="welcome_greet")
```

## Le contrôleur

```python
# mvc/controllers/welcome_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class WelcomeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge")

    @staticmethod
    def greet(request: Request) -> Response:
        name = request.param("name", default="Forge")
        return Response.text(f"Bonjour {name}")
```

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `http://localhost:8000/welcome` | `Bonjour Forge` |
| `http://localhost:8000/welcome/greet` | `Bonjour Forge` |
| `http://localhost:8000/welcome/greet?name=Roger` | `Bonjour Roger` |

## À retenir

- Une URL appelle une route.
- La route appelle une méthode du contrôleur.
- La méthode reçoit `request` et retourne `Response`.
- `Response.text(...)` ne passe par aucun template.

## Après ce starter

Passez au palier suivant : **Paramètres d'URL**.

Vous y apprendrez à lire une valeur transmise dans l'adresse, par
exemple :

```text
/query-params/hello?name=Roger
```

avec :

```python
request.param("name", default="Forge")
```

[Continuer avec Paramètres d'URL](../query-params/index.md)
