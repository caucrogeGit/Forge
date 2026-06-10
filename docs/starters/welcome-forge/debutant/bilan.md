# Bilan : starter Bonjour Forge

Vous venez de construire à la main, palier après palier, un seul et même projet Forge.

Cette page récapitule les onze notions acquises, puis montre l'état final complet des deux contrôleurs et du fichier de routes.

## Les onze notions acquises

- Palier 1 : le cycle requête vers contrôleur vers réponse, avec `Response.text(...)`.
- Palier 2 : lire la chaîne de requête avec `request.query("cle", default=...)`.
- Palier 3 : rendre une page HTML avec `BaseController.render(...)`.
- Palier 4 : capturer un segment de chemin avec `request.route("id", default=...)`.
- Palier 5 : inspecter une requête avec `Response.debug(request.data)` (en développement seulement).
- Palier 6 : renvoyer des données structurées avec `Response.json({...})`.
- Palier 7 : garantir une session (le jeton CSRF y vit) avec `_start_session` et `set_session_cookie`, puis transmettre le jeton dans un champ caché.
- Palier 8 : traiter un POST et lire un champ avec `request.form("cle", default=...)`.
- Palier 9 : valider côté serveur et refuser une saisie vide avec un statut `422`.
- Palier 10 : lire en base avec du SQL visible (`fetch_one(...)`) via une table créée par migration.
- Palier 11 : insérer une ligne avec `insert(...)` et des paramètres liés.

??? note "État final de mvc/controllers/welcome_controller.py"
    ```python
    # mvc/controllers/welcome_controller.py
    from core.http.request import Request
    from core.http.response import Response
    from core.mvc.controller.base_controller import BaseController
    from core.security.cookies import set_session_cookie
    from core.security.session import get_session, get_session_id
    from core.sessions.manager import get_session_store


    class WelcomeController(BaseController):

        @staticmethod
        def _start_session(request: Request):
            """Garantit une session active et renvoie (session_id, csrf_token).

            Le jeton CSRF vit dans la session : sans session, il serait vide.
            """
            session_id = get_session_id(request)
            session = get_session(session_id) if session_id else None
            if session is None:
                session_id = get_session_store().create()
                session = get_session(session_id)
            return session_id, session["csrf_token"]

        @staticmethod
        def index(request: Request) -> Response:
            return Response.text("Bonjour Forge")

        # Ajoutez ?name=Roger à l'URL, puis ouvrez /welcome/hello?name=Roger
        @staticmethod
        def hello(request: Request) -> Response:
            name = request.query("name", default="Forge")
            return Response.text(f"Bonjour {name}")

        @staticmethod
        def html(request: Request) -> Response:
            return BaseController.render("welcome/first.html", request=request)

        @staticmethod
        def article(request: Request) -> Response:
            article_id = request.route("id", default="inconnu")
            return Response.text(f"Article {article_id}")

        @staticmethod
        def debug(request: Request) -> Response:
            return Response.debug(request.data)

        @staticmethod
        def json(request: Request) -> Response:
            return Response.json(
                {
                    "framework": "Forge",
                    "message": "Bonjour JSON",
                    "items": ["alpha", "beta", "gamma"],
                }
            )

        @staticmethod
        def csrf(request: Request) -> Response:
            session_id, csrf_token = WelcomeController._start_session(request)
            response = BaseController.render(
                "welcome/csrf.html",
                request=request,
                context={"csrf_token": csrf_token},
            )
            set_session_cookie(response, session_id)
            return response

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

??? note "État final de mvc/controllers/message_controller.py"
    ```python
    # mvc/controllers/message_controller.py
    from core.database.db import fetch_one, insert
    from core.http.request import Request
    from core.http.response import Response
    from core.mvc.controller.base_controller import BaseController

    SELECT_FIRST_MESSAGE = "SELECT content FROM first_sql_messages ORDER BY id LIMIT 1"
    INSERT_MESSAGE = "INSERT INTO first_sql_messages (content) VALUES (?)"


    class MessageController(BaseController):

        @staticmethod
        def index(request: Request) -> Response:
            row = fetch_one(SELECT_FIRST_MESSAGE)
            message = row["content"] if row else "(aucun message)"
            return Response.text(f"Message depuis la base : {message}")

        @staticmethod
        def create(request: Request) -> Response:
            return BaseController.render(
                "message/first_sql_write.html",
                request=request,
                context={"csrf_token": BaseController.csrf_token(request)},
            )

        @staticmethod
        def store(request: Request) -> Response:
            content = request.form("content", default="").strip()
            if not content:
                return Response.text("Le message est obligatoire", status=422)
            insert(INSERT_MESSAGE, (content,))
            return Response.text(f"Message enregistré : {content}")
    ```

??? note "État final de mvc/routes.py"
    ```python
    # mvc/routes.py
    from core.http.router import Router
    from mvc.controllers.home_controller import HomeController
    from mvc.controllers.welcome_controller import WelcomeController
    from mvc.controllers.message_controller import MessageController

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
        public.add("GET",  "/welcome/validate", WelcomeController.validate, name="welcome-validate")
        public.add("POST", "/welcome/validate-submit", WelcomeController.validate_submit, name="welcome-validate_submit")
        public.add("GET",  "/message", MessageController.index, name="message-index")
        public.add("GET",  "/message/create", MessageController.create, name="message-create")
        public.add("POST", "/message/store", MessageController.store, name="message-store")
    ```

## Et ensuite

Vous avez terminé le niveau débutant : HTTP, vues, formulaires protégés, validation et SQL en lecture et écriture.

Le projet est prêt à grandir encore.
Place au niveau intermédiaire : listes, recherche, pagination, gabarits, mise à jour et suppression, sessions et messages flash.

[Niveau intermédiaire : Lister des enregistrements](../intermediaire/list-records.md)
