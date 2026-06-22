# Validation serveur

**Objectif**{ .intro-label } : refuser une saisie invalide côté serveur, sans jamais faire confiance aveuglément au navigateur.

**Ce que vous allez apprendre :**{ .intro-label } nettoyer une valeur avec `.strip()` et renvoyer une réponse d'erreur avec un statut HTTP `422` quand la saisie est vide.

`WelcomeController` porte déjà les méthodes des paliers précédents, et `mvc/routes.py` déclare les routes jusqu'à `/welcome/form`.

Nous ajoutons deux méthodes, deux routes et un gabarit.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [L'objet Request](../../../core-http/references/request.md) | l'accesseur `form(...)` pour lire la saisie |
    | [L'objet Response](../../../core-http/references/response.md) | comment fixer un statut HTTP, ici `422` |
    | [La protection CSRF](../../../reference/http/csrf.md) | le champ caché `csrf_token` toujours requis |

??? note "Contrôleurs"
    Ajoutez ces deux méthodes à la classe `WelcomeController` :

    ```python
        @staticmethod
        def validate(request: Request) -> Response:
            session_id, csrf_token = WelcomeController._start_session(request)
            response = BaseController.render(
                "welcome/server_validation.html",
                request=request,
                context={"csrf_token": csrf_token},
            )
            set_session_cookie(response, session_id)
            return response

        @staticmethod
        def validate_submit(request: Request) -> Response:
            name = request.form("name", default="").strip()
            if not name:
                return Response.text("Le prénom est obligatoire", status=422)
            return Response.text(f"Bonjour {name}")
    ```

    | Élément | Rôle |
    |---|---|
    | `.strip()` | Retire les espaces de début et de fin : une saisie qui ne contient que des espaces devient une chaîne vide. |
    | `if not name:` | Détecte la saisie vide et renvoie une erreur explicite. |
    | `status=422` | « Contenu non traitable » : signale au client que la donnée est invalide, sans planter ni accepter une valeur fausse. |

??? note "Routes"
    Ajoutez les deux routes (`GET` et `POST`) dans le groupe public de `mvc/routes.py` :

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
        public.add("GET",  "/welcome/csrf", WelcomeController.csrf, name="welcome-csrf")
        public.add("GET",  "/welcome/form", WelcomeController.form, name="welcome-form")
        public.add("POST", "/welcome/form-submit", WelcomeController.form_submit, name="welcome-form_submit")
        public.add("GET",  "/welcome/validate", WelcomeController.validate, name="welcome-validate")
        public.add("POST", "/welcome/validate-submit", WelcomeController.validate_submit, name="welcome-validate_submit")
    ```

??? note "Vues"
    Créez le gabarit `mvc/views/welcome/server_validation.html` :

    ```html
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="utf-8">
        <title>Validation serveur</title>
    </head>
    <body>
        <h1>Validation serveur</h1>
        <form method="post" action="/welcome/validate-submit">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <label>Prénom : <input type="text" name="name" value=""></label>
            <button type="submit">Envoyer</button>
        </form>
    </body>
    </html>
    ```

    Le champ prénom part **vide** : c'est ce qui permet de déclencher l'erreur de validation.

??? note "Tests"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/welcome/validate` | le formulaire avec un champ prénom vide |
    | Soumettre avec `Roger` | `Bonjour Roger` |
    | Soumettre vide ou avec des espaces | `Le prénom est obligatoire` (statut `422`) |

??? note "À retenir"
    - La validation se fait toujours côté serveur, jamais seulement dans le navigateur.
    - `.strip()` neutralise les saisies qui ne sont que des espaces.
    - Le statut `422` exprime une donnée invalide de façon claire.

Au palier suivant, nous lisons pour la première fois des données en base SQL.

[Continuer avec Première base SQL](first-sql.md)
