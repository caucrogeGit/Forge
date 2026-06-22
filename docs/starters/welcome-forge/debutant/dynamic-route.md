# Route dynamique

**Objectif**{ .intro-label } : capturer une partie variable du chemin de l'URL, par exemple un identifiant d'article.

**Ce que vous allez apprendre :**{ .intro-label } déclarer une route avec un segment dynamique `{id}` et lire ce segment avec `request.route("id", default=...)`.

`WelcomeController` porte déjà `index`, `hello` et `html` (paliers précédents).

Nous ajoutons une méthode et une route avec un segment variable.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [L'objet Request](../../../core-http/references/request.md) | les accesseurs de la requête, dont `route(...)` pour les segments de chemin |
    | [L'objet Response](../../../core-http/references/response.md) | la réponse renvoyée, ici de nouveau en texte brut |

??? note "Contrôleurs"
    Ajoutez cette méthode à la classe `WelcomeController` :

    ```python
        @staticmethod
        def article(request: Request) -> Response:
            article_id = request.route("id", default="inconnu")
            return Response.text(f"Article {article_id}")
    ```

    | Élément | Rôle |
    |---|---|
    | `request.route("id", default="inconnu")` | Lit la valeur capturée par le segment `{id}` du chemin. C'est différent de `request.query(...)` : ici la valeur est dans le chemin lui-même, pas dans la chaîne de requête après le `?`. |

??? note "Routes"
    Ajoutez la route avec son segment `{id}` dans le groupe public de `mvc/routes.py` :

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
    ```

    Le segment `{id}` déclare une partie dynamique du chemin : il accepte n'importe quelle valeur à cet endroit de l'URL.

??? note "Tests"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/welcome/article/42` | `Article 42` |
    | `https://localhost:8000/welcome/article/forge` | `Article forge` |

??? note "À retenir"
    - Un segment `{nom}` dans le chemin capture une valeur variable.
    - `request.route("nom", default=...)` lit cette valeur.
    - Segment de chemin et chaîne de requête sont deux sources distinctes.

Au palier suivant, nous inspectons le contenu d'une requête pour le déboguer.

[Continuer avec Inspecter une requête](request-debug.md)
