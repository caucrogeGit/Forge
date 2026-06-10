# Premier formulaire POST

**Objectif**{ .intro-label } : recevoir les données d'un formulaire envoyé en POST et les lire côté serveur.

**Ce que vous allez apprendre :**{ .intro-label } afficher un formulaire, le soumettre en POST, et lire un champ avec `request.form("name", default=...)`, le POST étant protégé par le jeton CSRF du palier précédent.

`WelcomeController` porte déjà les méthodes des paliers précédents, dont la méthode privée `_start_session` introduite au palier CSRF, et `mvc/routes.py` déclare les routes jusqu'à `/welcome/csrf`.

Nous ajoutons deux méthodes (afficher le formulaire, traiter l'envoi), deux routes et un gabarit.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [L'objet Request](../../../reference/http/request.md) | l'accesseur `form(...)` pour lire les champs d'un POST |
    | [La protection CSRF](../../../reference/http/csrf.md) | pourquoi le champ caché `csrf_token` est requis |
    | [La session HTTP](../../../reference/http/session.md) | où vit le jeton réutilisé par `_start_session` |

??? note "Contrôleurs"
    Ajoutez ces deux méthodes à la classe `WelcomeController`.
    Comme ce formulaire fait un **vrai POST protégé**, `form` réutilise `_start_session` (garantir la session, donc un jeton non vide) et pose le cookie de session :

    ```python
        @staticmethod
        def form(request: Request) -> Response:
            session_id, csrf_token = WelcomeController._start_session(request)
            response = BaseController.render(
                "welcome/form_post.html",
                request=request,
                context={"csrf_token": csrf_token},
            )
            set_session_cookie(response, session_id)
            return response

        @staticmethod
        def form_submit(request: Request) -> Response:
            name = request.form("name", default="Forge")
            return Response.text(f"Bonjour {name}")
    ```

    | Élément | Rôle |
    |---|---|
    | `request.form("name", default="Forge")` | Lit un champ du corps du formulaire, là où `request.query(...)` lisait la chaîne de requête. |
    | `_start_session(request)` | Garantit une session active et renvoie un jeton CSRF non vide (méthode introduite au palier CSRF). |

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
        public.add("GET",  "/welcome/json", WelcomeController.json, name="welcome-json")
        public.add("GET",  "/welcome/csrf", WelcomeController.csrf, name="welcome-csrf")
        public.add("GET",  "/welcome/form", WelcomeController.form, name="welcome-form")
        public.add("POST", "/welcome/form-submit", WelcomeController.form_submit, name="welcome-form_submit")
    ```

    Deux routes encadrent le formulaire : `GET /welcome/form` l'affiche, `POST /welcome/form-submit` traite l'envoi.

??? note "Vues"
    Créez le gabarit `mvc/views/welcome/form_post.html` :

    ```html
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="utf-8">
        <title>Premier formulaire POST</title>
    </head>
    <body>
        <h1>Premier formulaire POST</h1>
        <form method="post" action="/welcome/form-submit">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <label>Prénom : <input type="text" name="name" value="Forge"></label>
            <button type="submit">Envoyer</button>
        </form>
    </body>
    </html>
    ```

    Le champ caché `csrf_token` permet au POST de passer la protection CSRF du groupe public.

??? note "Tests"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/welcome/form` | le formulaire avec le champ prénom |
    | Soumettre avec `Roger` | `Bonjour Roger` |
    | Soumettre en laissant `Forge` | `Bonjour Forge` |

??? note "À retenir"
    - `request.form(cle, default=...)` lit un champ envoyé en POST.
    - Un même formulaire s'appuie sur deux routes : `GET` (afficher) et `POST` (traiter).
    - Le champ caché `csrf_token` est requis pour que le POST soit accepté.

??? tip "Astuces"
    Les appels session (`_start_session`, `set_session_cookie`) reviennent à chaque formulaire protégé.
    Si vous voulez simplifier, **vous** pouvez les regrouper dans une **classe façade** de votre application, sous `mvc/helpers/`.

    Forge ne l'ajoute pas au framework : le noyau reste minimal et explicite, l'ergonomie est à votre main.
    Un parcours dédié vous montre comment construire ces façades pas à pas (`Session`, `Cookies`, `Flash`) : [Construire vos façades helper](../../welcome-helpers/installation.md).

Au palier suivant, nous refusons une saisie invalide côté serveur.

[Continuer avec Validation serveur](server-validation.md)
