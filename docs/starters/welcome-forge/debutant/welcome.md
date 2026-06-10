# Bonjour Forge

!!! info "Le mini-projet du niveau débutant"
    Chaque niveau de welcome-forge est un **mini-projet autonome** que vous écrivez à la main, palier après palier.
    Au niveau débutant, vous partez de « Bonjour Forge » (une simple réponse texte) et faites grandir le projet jusqu'à **lire et écrire en base** : vues HTML, route dynamique, réponse JSON, jeton CSRF, formulaire POST, validation serveur, puis SQL.

    Un `WelcomeController` accumule les paliers HTTP, puis un `MessageController` porte les paliers base de données.

**Objectif**{ .intro-label } : écrire votre tout premier contrôleur et le relier à une URL.

**Ce que vous allez apprendre :**{ .intro-label } déclarer une route et renvoyer une réponse texte avec `Response.text(...)`, sans vue HTML ni base de données.

Le squelette fournit déjà `mvc/routes.py` avec `router = Router()` et la route d'accueil `/` (servie par `HomeController`).

Nous allons greffer notre travail dessus.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [L'objet Request](../../../reference/http/request.md) | l'objet reçu par chaque action de contrôleur |
    | [L'objet Response](../../../reference/http/response.md) | ce que renvoie une action ; ici `Response.text(...)` |

??? note "Contrôleurs"
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

    | Élément | Rôle |
    |---|---|
    | `BaseController` | Classe mère de tout contrôleur ; chaque action est une méthode statique qui reçoit un `request: Request` et retourne un `Response`. |
    | `Response.text(...)` | Construit une réponse `text/plain`, sans moteur de rendu ni gabarit. |

??? note "Routes"
    Dans `mvc/routes.py`, ajoutez l'import du contrôleur puis la route `/welcome` à l'intérieur du groupe public déjà présent :

    ```python
    # mvc/routes.py
    from core.http.router import Router
    from mvc.controllers.home_controller import HomeController
    from mvc.controllers.welcome_controller import WelcomeController

    router = Router()

    with router.group("", public=True) as public:
        public.add("GET", "/", HomeController.index, name="home-index")
        public.add("GET", "/welcome", WelcomeController.index, name="welcome-index")
    ```

    Le groupe `with router.group("", public=True) as public:` regroupe les routes publiques.
    La protection CSRF y est active par défaut, ce qui protégera nos futurs formulaires POST.

??? note "Tests"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/welcome` | `Bonjour Forge` |

??? note "À retenir"
    - Une URL est associée à une route, qui appelle une méthode de contrôleur.
    - La méthode reçoit `request` et retourne `Response`.
    - `Response.text(...)` renvoie du texte brut, sans moteur de rendu.

Au palier suivant, votre contrôleur va lire une valeur passée dans l'adresse.

[Continuer avec Paramètres d'URL](query-params.md)
