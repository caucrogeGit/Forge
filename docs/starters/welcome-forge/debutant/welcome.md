# Bonjour Forge

Premier palier d'un tutoriel continu : vous allez construire à la main un
seul projet qui grandit palier après palier. On démarre par la réponse la
plus simple possible.

!!! info "Le mini-projet du niveau débutant"
    Chaque niveau de welcome-forge est un **mini-projet autonome** que vous
    écrivez à la main, palier après palier. Au niveau débutant, vous partez de
    « Bonjour Forge » (une simple réponse texte) et faites grandir le projet
    jusqu'à **lire et écrire en base** : vues HTML, route dynamique, réponse
    JSON, jeton CSRF, formulaire POST, validation serveur, puis SQL. Un
    `WelcomeController` accumule les paliers HTTP, puis un `MessageController`
    porte les paliers base de données.

**Ce que vous allez apprendre :** écrire votre premier contrôleur, déclarer
une route et renvoyer une réponse texte avec `Response.text(...)`, sans vue
HTML ni base de données.

Le squelette fournit déjà `mvc/routes.py` avec `router = Router()` et la
route d'accueil `/` (servie par `HomeController`). Nous allons greffer notre
travail dessus.

## L'ajout

Créez le fichier `mvc/controllers/welcome_controller.py` :

```python
# mvc/controllers/welcome_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class WelcomeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge")
```

Dans `mvc/routes.py`, ajoutez l'import du contrôleur puis la route
`/welcome` à l'intérieur du groupe public déjà présent.

## Votre mvc/routes.py à ce stade

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.welcome_controller import WelcomeController

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET", "/", HomeController.index, name="home-index")
    pub.add("GET", "/welcome", WelcomeController.index, name="welcome-index")
```

## Comprendre ce code

- Un contrôleur est une classe qui hérite de `BaseController` ; chaque
  action reçoit un `request: Request` et retourne un `Response`.
- `Response.text(...)` construit une réponse `text/plain`, sans template.
- Le groupe `with router.group("", public=True) as pub:` regroupe les
  routes publiques ; la protection CSRF y est active par défaut, ce qui
  protégera nos futurs formulaires POST.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/welcome` | `Bonjour Forge` |

## À retenir

- Une URL est associée à une route, qui appelle une méthode de contrôleur.
- La méthode reçoit `request` et retourne `Response`.
- `Response.text(...)` renvoie du texte brut, sans moteur de rendu.

Au palier suivant, votre contrôleur va lire une valeur passée dans
l'adresse.

[Continuer avec Paramètres d'URL](query-params.md)
