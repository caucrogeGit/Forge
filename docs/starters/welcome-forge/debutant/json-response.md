# Réponse JSON

**Objectif**{ .intro-label } : renvoyer des données structurées plutôt qu'une page HTML ou du texte.

**Ce que vous allez apprendre :**{ .intro-label } produire une réponse JSON avec `Response.json({...})`, utile pour une API ou un échange machine à machine.

`WelcomeController` porte déjà les méthodes des paliers précédents, et `mvc/routes.py` déclare les routes jusqu'à `/welcome/debug`.

Nous ajoutons une méthode et une route.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [L'objet Response](../../../reference/http/response.md) | la fabrique `Response.json(...)` et l'en-tête `Content-Type` |
    | [L'objet Request](../../../reference/http/request.md) | la requête reçue par l'action |

??? note "Contrôleurs"
    Ajoutez cette méthode à la classe `WelcomeController` :

    ```python
        @staticmethod
        def json_demo(request: Request) -> Response:
            return Response.json(
                {
                    "framework": "Forge",
                    "message": "Bonjour JSON",
                    "items": ["alpha", "beta", "gamma"],
                }
            )
    ```

    | Élément | Rôle |
    |---|---|
    | `Response.json({...})` | Sérialise un dictionnaire Python en JSON et fixe l'en-tête `Content-Type: application/json`. |

    Les structures imbriquées (listes, dictionnaires) sont prises en charge, comme la liste `items` ci-dessus.
    C'est la réponse adaptée à une API : un consommateur peut analyser le résultat sans extraire de données d'une page HTML.

??? note "Routes"
    Ajoutez la route dans le groupe public de `mvc/routes.py` :

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
        public.add("GET",  "/welcome/json", WelcomeController.json_demo, name="welcome-json")
    ```

??? note "Tests"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/welcome/json` | le document JSON `{"framework": "Forge", ...}` |

??? note "À retenir"
    - `Response.json({...})` renvoie des données structurées en JSON.
    - Le type de contenu est positionné automatiquement.
    - À privilégier pour les échanges machine à machine plutôt que du texte.

Au palier suivant, nous préparons les formulaires en découvrant le jeton CSRF.

[Continuer avec Le jeton CSRF](csrf.md)
