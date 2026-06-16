# Bilan : niveau avancé

Vous venez de construire à la main, palier après palier, un seul et même mini-projet : le **Catalogue d'articles**.

Cette page récapitule les quatre notions acquises, puis montre l'état final complet du contrôleur et des routes.

## Les quatre notions acquises

- Palier 1 : relier deux tables par une **clé étrangère** et les lire avec un `JOIN` SQL visible (`articles` joint à `categories`).
- Palier 2 : grouper des écritures **atomiques** avec `with transaction() as tx:` (créer un article et incrémenter le compteur de sa catégorie, rollback sur erreur).
- Palier 3 : recevoir un fichier (`multipart`), le récupérer avec `request.file`, le stocker via `forge_mvc_files.save_upload` (validé) et l'attacher à un article.
- Palier 4 : exposer le catalogue en JSON (`Response.json`) derrière un jeton `Authorization: Bearer …` lu avec `request.header`.

??? note "État final de mvc/controllers/article_controller.py"
    ```python
    # mvc/controllers/article_controller.py
    from core.database.db import execute, fetch_all, fetch_one, insert
    from core.database.transaction import transaction
    from core.http.request import Request
    from core.http.response import Response
    from core.mvc.controller.base_controller import BaseController
    from core.security.cookies import set_session_cookie
    from core.security.session import get_session, get_session_id
    from core.sessions.manager import get_session_store
    from forge_mvc_files import UploadError, save_upload

    SELECT_ARTICLES_WITH_CATEGORY = (
        "SELECT a.id, a.title, c.name AS category "
        "FROM articles a "
        "JOIN categories c ON c.id = a.category_id "
        "ORDER BY a.id"
    )
    SELECT_CATEGORIES = "SELECT id, name FROM categories ORDER BY name"
    SELECT_ONE = "SELECT id, title FROM articles WHERE id = ?"
    INSERT_ARTICLE = "INSERT INTO articles (title, category_id) VALUES (?, ?)"
    INCREMENT_COUNT = "UPDATE categories SET article_count = article_count + 1 WHERE id = ?"
    SET_DOCUMENT = "UPDATE articles SET document_path = ? WHERE id = ?"
    API_TOKEN = "forge-demo-token"


    class ArticleController(BaseController):

        @staticmethod
        def _start_session(request: Request):
            """Garantit une session active et renvoie (session_id, csrf_token)."""
            session_id = get_session_id(request)
            if session_id is None or get_session(session_id) is None:
                session_id = get_session_store().create()
            session = get_session(session_id) or {}
            return session_id, session.get("csrf_token", "")

        @staticmethod
        def index(request: Request) -> Response:
            articles = fetch_all(SELECT_ARTICLES_WITH_CATEGORY)
            return BaseController.render(
                "article/index.html",
                request=request,
                context={"articles": articles},
            )

        @staticmethod
        def create(request: Request) -> Response:
            session_id, csrf_token = ArticleController._start_session(request)
            response = BaseController.render(
                "article/new.html",
                request=request,
                context={"categories": fetch_all(SELECT_CATEGORIES), "csrf_token": csrf_token},
            )
            set_session_cookie(response, session_id)
            return response

        @staticmethod
        def store(request: Request) -> Response:
            title = request.form("title", default="").strip()
            category_id = request.form("category_id", default="").strip()
            try:
                with transaction() as tx:
                    insert(INSERT_ARTICLE, (title, category_id), tx=tx)
                    if not title:
                        raise ValueError("Le titre est obligatoire : tout est annulé.")
                    execute(INCREMENT_COUNT, (category_id,), tx=tx)
            except ValueError as exc:
                return BaseController.render(
                    "article/new.html",
                    status=422,
                    request=request,
                    context={"categories": fetch_all(SELECT_CATEGORIES), "error": str(exc)},
                )
            return BaseController.redirect("/article", request=request, flash="Article créé.")

        @staticmethod
        def attach(request: Request) -> Response:
            article = fetch_one(SELECT_ONE, (int(request.route("id", default="0")),))
            if article is None:
                return Response.text("Article introuvable.", status=404)
            session_id, csrf_token = ArticleController._start_session(request)
            response = BaseController.render(
                "article/attach.html",
                request=request,
                context={"article": article, "csrf_token": csrf_token},
            )
            set_session_cookie(response, session_id)
            return response

        @staticmethod
        def attach_store(request: Request) -> Response:
            record_id = int(request.route("id", default="0"))
            uploaded = request.file("document")
            if uploaded is None:
                return Response.text("Aucun fichier sélectionné.", status=422)
            try:
                saved = save_upload(uploaded, "documents")
            except UploadError as exc:
                return Response.text(str(exc), status=422)
            execute(SET_DOCUMENT, (saved.path, record_id))
            return BaseController.redirect("/article", request=request, flash="Document attaché.")

        @staticmethod
        def api_index(request: Request) -> Response:
            authorization = request.header("Authorization") or ""
            if authorization != f"Bearer {API_TOKEN}":
                return Response.json({"error": "Jeton manquant ou invalide."}, status=401)
            articles = fetch_all(SELECT_ARTICLES_WITH_CATEGORY)
            return Response.json({"articles": articles})
    ```

??? note "État final de mvc/routes.py"
    ```python
    # mvc/routes.py
    from core.http.router import Router
    from mvc.controllers.home_controller import HomeController
    from mvc.controllers.article_controller import ArticleController

    router = Router()

    with router.group("", public=True) as public:
        public.add("GET",  "/", HomeController.index, name="home-index")
        public.add("GET",  "/article", ArticleController.index, name="article-index")
        public.add("GET",  "/article/create", ArticleController.create, name="article-create")
        public.add("POST", "/article/store", ArticleController.store, name="article-store")
        public.add("GET",  "/article/attach/{id}", ArticleController.attach, name="article-attach")
        public.add("POST", "/article/attach-store/{id}", ArticleController.attach_store, name="article-attach_store")
        public.add("GET",  "/article/api-index", ArticleController.api_index, name="article-api_index")
    ```

## Et ensuite

Vous savez relier vos données sans ORM, écrire de façon atomique, recevoir des fichiers et exposer une API JSON protégée, le SQL restant explicite.

Le **récapitulatif** rassemble toutes les API de la progression sur une seule page.

[Récapitulatif de la progression](../recapitulatif.md)
