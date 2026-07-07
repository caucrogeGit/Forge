# Paramètres d'URL

**Objectif**{ .intro-label } : lire une valeur passée dans l'adresse, par exemple `?name=Roger`.

**Ce que vous allez apprendre :**{ .intro-label } récupérer une valeur de la chaîne de requête avec `request.query("name", default=...)`, avec une valeur de repli quand le paramètre est absent.

Votre `WelcomeController` possède déjà la méthode `index` (palier précédent), et `mvc/routes/__init__.py` déclare la route `/welcome`.

Nous y ajoutons une méthode et une route.

??? note "Voir l'illustration"
    ![](query-params.png){ width="60%" }

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [L'objet Request](../../../core-http/request.md) | les accesseurs de la requête, dont `query(...)` |
    | [L'objet Response](../../../core-http/response.md) | la réponse renvoyée, ici encore en texte brut |

??? note "Contrôleurs"
    Ajoutez cette méthode à la classe `WelcomeController` :

    ```python
        # Ajoutez ?name=Roger à l'URL, puis ouvrez /welcome/hello?name=Roger
        @staticmethod
        def hello(request: Request) -> Response:
            name = request.query("name", default="Forge")
            return Response.text(f"Bonjour {name}")
    ```

    | Élément | Rôle |
    |---|---|
    | `request.query("name", default="Forge")` | Lit la valeur `name` de la chaîne de requête ; renvoie `default` si la clé est absente, donc ni exception ni `None` à gérer. |

    La valeur retournée est toujours de type `str` ; une conversion (entier, date) reste à votre charge dans le contrôleur.

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
    ```

??? note "Tests"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/welcome/hello` | `Bonjour Forge` |
    | `https://localhost:8000/welcome/hello?name=Roger` | `Bonjour Roger` |
    | `https://localhost:8000/welcome/hello?name=Alice` | `Bonjour Alice` |

??? note "À retenir"
    - `request.query(cle, default=...)` lit une valeur de la chaîne de requête.
    - `default=...` est renvoyé si la clé est absente : pas d'exception, pas de `None` à gérer.
    - La réponse reste un `Response.text(...)`, donc aucun template.

Au palier suivant, nous passons du texte brut à une vraie page HTML.

[Continuer avec Première vue HTML](first-html-view.md)
