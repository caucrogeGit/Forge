# Inspecter une requête

**Objectif**{ .intro-label } : visualiser le contenu d'une requête pour comprendre ce que Forge reçoit.

**Ce que vous allez apprendre :**{ .intro-label } afficher les données de la requête avec `Response.debug(request.data)`, une aide pédagogique disponible en environnement de développement.

`WelcomeController` porte déjà les méthodes des paliers précédents, et `mvc/routes/__init__.py` déclare les routes correspondantes jusqu'à `/welcome/article/{id}`.

Nous ajoutons une méthode et une route.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [L'objet Request](../../../core-http/request.md) | ce que regroupe `request.data` |
    | [L'objet Response](../../../core-http/response.md) | la réponse, ici la page de débogage `Response.debug(...)` |

??? note "Contrôleurs"
    Ajoutez cette méthode à la classe `WelcomeController` :

    ```python
        @staticmethod
        def debug(request: Request) -> Response:
            return Response.debug(request.data)
    ```

    | Élément | Rôle |
    |---|---|
    | `request.data` | Rassemble les données utiles de la requête courante. |
    | `Response.debug(...)` | Présente ces données sous forme de page HTML lisible, pensée pour l'inspection pendant le développement. |

    Cette aide n'est active qu'en environnement de développement (`APP_ENV=dev`) ; en production elle répond `404`, pour ne jamais exposer les données d'une requête.

??? note "Routes"
    Ajoutez la route dans le groupe public de `mvc/routes/__init__.py` :

    ```python
    # mvc/routes/__init__.py
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

??? note "Tests"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/welcome/debug` | la page de débogage (en `APP_ENV=dev`) |
    | `https://localhost:8000/welcome/debug?x=1&y=2` | la même page, avec les paramètres affichés |

??? note "À retenir"
    - `Response.debug(request.data)` est un outil d'inspection pédagogique.
    - Il n'est disponible qu'en développement ; il répond `404` en production.
    - À n'utiliser que pour comprendre, jamais comme réponse définitive.

Au palier suivant, nous renvoyons des données structurées au format JSON.

[Continuer avec Réponse JSON](json-response.md)
