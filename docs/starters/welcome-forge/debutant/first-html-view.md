# Première vue HTML

**Objectif**{ .intro-label } : rendre une vraie page HTML au lieu de texte brut.

**Ce que vous allez apprendre :**{ .intro-label } rendre un gabarit avec `BaseController.render(...)`, qui passe la requête au moteur de template et renvoie la page HTML.

`WelcomeController` porte déjà `index` et `hello` (paliers précédents), et `mvc/routes.py` déclare `/welcome` et `/welcome/hello`.

Nous ajoutons une méthode, une route et un gabarit.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [L'objet Response](../../../reference/http/response.md) | la réponse renvoyée, désormais produite par un gabarit |
    | [L'objet Request](../../../reference/http/request.md) | la requête transmise au moteur de template |

??? note "Contrôleurs"
    Ajoutez cette méthode à la classe `WelcomeController` :

    ```python
        @staticmethod
        def html(request: Request) -> Response:
            return BaseController.render("welcome/first.html", request=request)
    ```

    | Élément | Rôle |
    |---|---|
    | `BaseController.render("welcome/first.html", request=request)` | Cherche le gabarit sous `mvc/views/` et le rend en HTML. Le chemin est relatif à `mvc/views/` : ici le fichier vit dans `mvc/views/welcome/`. |
    | `request=request` | Donne au gabarit l'accès au contexte de la requête courante. |

    Le contrôleur reste mince : il choisit le gabarit, le gabarit gère l'affichage.

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
    ```

??? note "Vues"
    Créez le gabarit `mvc/views/welcome/first.html` :

    ```html
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="utf-8">
        <title>Première vue HTML</title>
    </head>
    <body>
        <h1>Première vue HTML</h1>
        <p>
            Cette page est rendue par <code>BaseController.render(...)</code> :
            le contrôleur ne construit plus le texte à la main, il délègue
            l'affichage à un gabarit.
        </p>
    </body>
    </html>
    ```

??? note "Tests"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/welcome/html` | la page HTML « Première vue HTML » |

??? note "À retenir"
    - `BaseController.render(...)` renvoie une page HTML rendue par le moteur de template.
    - Les gabarits vivent sous `mvc/views/`.
    - Le contrôleur reste mince : il choisit le gabarit, le gabarit gère l'affichage.

Au palier suivant, nous lisons une valeur directement dans le chemin de l'URL.

[Continuer avec Route dynamique](dynamic-route.md)
