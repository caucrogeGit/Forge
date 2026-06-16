# Bonjour Forge

## Niveau débutant : construire un premier mini-projet Forge

Dans ce niveau, vous construisez un premier mini-projet Forge à la main.

Vous partez d'une page très simple qui affiche **Bonjour Forge**, puis vous faites évoluer progressivement le projet.
À chaque palier, vous ajoutez une brique concrète : une route, un contrôleur, une vue HTML, une route dynamique, une réponse JSON, un formulaire, une validation serveur, puis une première interaction avec la base de données.

L'objectif n'est pas seulement d'obtenir une application qui fonctionne.
L'objectif est de comprendre comment un projet Forge est organisé, comment une requête circule dans le framework, et comment le code applicatif se construit sans magie cachée.

Le parcours commence avec un `WelcomeController`, utilisé pour découvrir les bases HTTP du framework.
Il se poursuit ensuite avec un `MessageController`, qui introduit les formulaires, la validation et les premières opérations SQL.

À la fin du niveau débutant, vous aurez construit un mini-projet complet, simple mais réel, capable d'afficher des pages, de recevoir des données utilisateur, de les valider et de les enregistrer en base.

??? note "Voir l'illustration"
    ![](welcome.png){ width="60%" }

??? note "Documentation utile"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [L'objet Request](../../../reference/http/request.md) | L'objet reçu par chaque action de contrôleur. |
    | [L'objet Response](../../../reference/http/response.md) | Ce que renvoie une action de contrôleur. Ici, vous utilisez `Response.text(...)`. |

??? note "Contrôleur"
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
    | `BaseController` | Classe mère du contrôleur. |
    | `index(request: Request)` | Action appelée par la route. Elle reçoit la requête HTTP. |
    | `Response.text(...)` | Construit une réponse en texte brut, sans vue HTML ni moteur de rendu. |

??? note "Route"
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

    Le groupe `with router.group("", public=True) as public:` regroupe les routes publiques du projet.

    La ligne suivante associe l'URL `/welcome` à l'action `WelcomeController.index` :

    ```python
    public.add("GET", "/welcome", WelcomeController.index, name="welcome-index")
    ```

??? note "Tester le palier"
    Ouvrez le chemin `/welcome` dans le navigateur.

    Le port est celui configuré dans `env/dev` (`APP_PORT`), 8000 par défaut.
    Avec le port par défaut, l'adresse est :

    ```text
    https://localhost:8000/welcome
    ```

    Résultat attendu :

    ```text
    Bonjour Forge
    ```


## À retenir
- Une URL est associée à une route.
- Une route appelle une action de contrôleur.
- Une action reçoit un objet `Request`.
- Une action retourne un objet `Response`.
- `Response.text(...)` renvoie du texte brut, sans vue HTML.

## Palier suivant
Votre contrôleur va lire une valeur passée dans l'adresse.

[Continuer avec Paramètres d'URL](query-params.md)
