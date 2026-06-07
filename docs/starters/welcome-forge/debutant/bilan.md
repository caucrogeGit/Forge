# Bilan : starter Bonjour Forge

Vous venez de construire à la main, palier après palier, un seul et même
projet Forge. Cette page récapitule les onze notions acquises, puis montre
l'état final complet des deux contrôleurs et du fichier de routes.

## Les onze notions acquises

- Palier 1 : le cycle requête vers contrôleur vers réponse, avec
  `Response.text(...)`.
- Palier 2 : lire la chaîne de requête avec `request.param("cle", default=...)`.
- Palier 3 : rendre une page HTML avec `BaseController.render(...)`.
- Palier 4 : capturer un segment de chemin avec `request.route_param("id", default=...)`.
- Palier 5 : inspecter une requête avec `Response.debug(request.data)` (en
  développement seulement).
- Palier 6 : renvoyer des données structurées avec `Response.json({...})`.
- Palier 7 : obtenir un jeton CSRF avec `BaseController.csrf_token(request)`.
- Palier 8 : traiter un POST et lire un champ avec `request.form("cle", default=...)`.
- Palier 9 : valider côté serveur et refuser une saisie vide avec un statut `422`.
- Palier 10 : lire en base avec du SQL visible (`fetch_one(...)`) via une
  table créée par migration.
- Palier 11 : insérer une ligne avec `insert(...)` et des paramètres liés.

## État final de mvc/controllers/welcome_controller.py

```python
# mvc/controllers/welcome_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class WelcomeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge")

    @staticmethod
    def query_params_index(request: Request) -> Response:
        return Response.text(
            "Ajoutez ?name=Roger à l'URL, puis ouvrez /query-params/hello?name=Roger"
        )

    @staticmethod
    def hello(request: Request) -> Response:
        name = request.param("name", default="Forge")
        return Response.text(f"Bonjour {name}")

    @staticmethod
    def html_view(request: Request) -> Response:
        return BaseController.render("welcome/first_html_view.html", request=request)

    @staticmethod
    def show_article(request: Request) -> Response:
        article_id = request.route_param("id", default="inconnu")
        return Response.text(f"Article {article_id}")

    @staticmethod
    def debug(request: Request) -> Response:
        return Response.debug(request.data)

    @staticmethod
    def json_demo(request: Request) -> Response:
        return Response.json(
            {
                "framework": "Forge",
                "message": "Bonjour JSON",
                "items": ["alpha", "beta", "gamma"],
            }
        )

    @staticmethod
    def csrf_demo(request: Request) -> Response:
        return BaseController.render(
            "welcome/csrf.html",
            request=request,
            context={"csrf_token": BaseController.csrf_token(request)},
        )

    @staticmethod
    def form(request: Request) -> Response:
        return BaseController.render(
            "welcome/form_post.html",
            request=request,
            context={"csrf_token": BaseController.csrf_token(request)},
        )

    @staticmethod
    def form_submit(request: Request) -> Response:
        name = request.form("name", default="Forge")
        return Response.text(f"Bonjour {name}")

    @staticmethod
    def validate(request: Request) -> Response:
        return BaseController.render(
            "welcome/server_validation.html",
            request=request,
            context={"csrf_token": BaseController.csrf_token(request)},
        )

    @staticmethod
    def validate_submit(request: Request) -> Response:
        name = request.form("name", default="").strip()
        if not name:
            return Response.text("Le prénom est obligatoire", status=422)
        return Response.text(f"Bonjour {name}")
```

## État final de mvc/controllers/message_controller.py

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

## État final de mvc/routes.py

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.welcome_controller import WelcomeController
from mvc.controllers.message_controller import MessageController

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET", "/", HomeController.index, name="home_index")
    pub.add("GET",  "/welcome", WelcomeController.index, name="welcome_index")
    pub.add("GET",  "/query-params", WelcomeController.query_params_index, name="query_params_index")
    pub.add("GET",  "/query-params/hello", WelcomeController.hello, name="query_params_hello")
    pub.add("GET",  "/first-html-view", WelcomeController.html_view, name="first_html_view_index")
    pub.add("GET",  "/dynamic-route/articles/{id}", WelcomeController.show_article, name="dynamic_route_article_show")
    pub.add("GET",  "/request-debug", WelcomeController.debug, name="request_debug_index")
    pub.add("GET",  "/json-response", WelcomeController.json_demo, name="json_response_index")
    pub.add("GET",  "/csrf", WelcomeController.csrf_demo, name="csrf_index")
    pub.add("GET",  "/form-post", WelcomeController.form, name="form_post_index")
    pub.add("POST", "/form-post", WelcomeController.form_submit, name="form_post_submit")
    pub.add("GET",  "/server-validation", WelcomeController.validate, name="server_validation_index")
    pub.add("POST", "/server-validation", WelcomeController.validate_submit, name="server_validation_submit")
    pub.add("GET",  "/first-sql", MessageController.index, name="first_sql_index")
    pub.add("GET",  "/first-sql-write", MessageController.create, name="first_sql_write_index")
    pub.add("POST", "/first-sql-write", MessageController.store, name="first_sql_write_submit")
```

## Et ensuite

Vous avez terminé le niveau débutant : HTTP, vues, formulaires protégés,
validation et SQL en lecture et écriture. Le projet est prêt à grandir
encore. Place au niveau intermédiaire : listes, recherche, pagination,
gabarits, mise à jour et suppression, sessions et messages flash.

[Niveau intermédiaire : Lister des enregistrements](../intermediaire/list-records.md)
