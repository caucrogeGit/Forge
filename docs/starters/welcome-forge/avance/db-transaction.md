# Écritures transactionnelles

**Objectif**{ .intro-label } : regrouper plusieurs écritures pour qu'elles soient **atomiques** : soit tout réussit, soit rien.

**Ce que vous allez apprendre :**{ .intro-label } le bloc `with transaction() as tx:`. Il ouvre une transaction explicite et passe `tx` aux helpers DB, qui réutilisent la connexion **sans jamais committer eux-mêmes**. À la sortie du bloc, Forge committe ; si une exception traverse le bloc, Forge **annule** (rollback).

Le catalogue est en lecture seule.

Nous ajoutons la création d'un article.
Créer un article doit faire **deux écritures cohérentes** : insérer l'article **et** incrémenter le compteur `article_count` de sa catégorie.
Ces deux écritures doivent rester atomiques, d'où la transaction.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [La protection CSRF](../../../core-security/csrf.md) | le jeton requis par le formulaire de création |
    | [La session HTTP](../../../core-security/session.md) | où vit le jeton garanti par `_start_session` |
    | [Migrations SQL](../../../features/migrations.md) | les tables `articles` et `categories` du palier précédent |

??? note "Contrôleurs"
    Ajoutez les requêtes et les deux méthodes dans `mvc/controllers/article_controller.py` :

    ```python
    from core.database.db import execute, fetch_all, insert
    from core.database.transaction import transaction
    from core.security.cookies import set_session_cookie
    from core.security.session import get_session, get_session_id
    from core.sessions.manager import get_session_store

    SELECT_CATEGORIES = "SELECT id, name FROM categories ORDER BY name"
    INSERT_ARTICLE = "INSERT INTO articles (title, category_id) VALUES (?, ?)"
    INCREMENT_COUNT = "UPDATE categories SET article_count = article_count + 1 WHERE id = ?"


    class ArticleController(BaseController):

        # … index(...) inchangé …

        @staticmethod
        def _start_session(request: Request):
            """Garantit une session active et renvoie (session_id, csrf_token).

            Le jeton CSRF vit dans la session : sans session, il serait vide.
            """
            session_id = get_session_id(request)
            if session_id is None or get_session(session_id) is None:
                session_id = get_session_store().create()
            session = get_session(session_id) or {}
            return session_id, session.get("csrf_token", "")

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
                        # Erreur APRÈS la première écriture : le rollback l'annule.
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
    ```

    | Élément | Rôle |
    |---|---|
    | `with transaction() as tx:` | Ouvre la transaction ; chaque `insert(..., tx=tx)` ou `execute(..., tx=tx)` écrit **dans** cette transaction, sans committer. |
    | Sortie sans erreur | Forge **committe** : l'article est créé **et** le compteur incrémenté. |
    | Exception dans le bloc | Forge **annule** (rollback) : même la première écriture déjà exécutée est défaite. C'est l'atomicité, **tout ou rien**. |

    Ici on valide après la première écriture pour **démontrer** le rollback ; en pratique on valide souvent avant d'écrire.

??? note "Vues"
    Créez la vue `mvc/views/article/new.html` :

    ```html
    <!-- mvc/views/article/new.html -->
    <!DOCTYPE html>
    <html lang="fr">
    <head><meta charset="utf-8"><title>Nouvel article</title></head>
    <body>
        <h1>Nouvel article</h1>
        {% if error %}<p><strong>{{ error }}</strong></p>{% endif %}
        <form method="post" action="/article/store">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <input type="text" name="title" placeholder="Titre">
            <select name="category_id">
                {% for c in categories %}
                <option value="{{ c.id }}">{{ c.name }}</option>
                {% endfor %}
            </select>
            <button type="submit">Créer</button>
        </form>
        <p><a href="/article">Retour au catalogue</a></p>
    </body>
    </html>
    ```

    Ajoutez un lien vers le formulaire dans `mvc/views/article/index.html` :

    ```html
    <p><a href="/article/create">Nouvel article</a></p>
    ```

??? note "Routes"
    Déclarez les deux routes dans `mvc/routes/__init__.py` :

    ```python
    # mvc/routes/__init__.py
    from core.http.router import Router
    from mvc.controllers.home_controller import HomeController
    from mvc.controllers.article_controller import ArticleController

    router = Router()

    with router.group("", public=True) as public:
        public.add("GET",  "/", HomeController.index, name="home-index")
        public.add("GET",  "/article", ArticleController.index, name="article-index")
        public.add("GET",  "/article/create", ArticleController.create, name="article-create")
        public.add("POST", "/article/store", ArticleController.store, name="article-store")
    ```

??? note "Tests"
    | Action | Résultat |
    |---|---|
    | Créer un article avec un titre | retour au catalogue, l'article apparaît, le compteur de sa catégorie augmente |
    | Soumettre un titre vide | erreur `422`, **aucune** écriture (l'article n'est pas créé, le compteur ne bouge pas) |

??? note "À retenir"
    - `with transaction() as tx:` rend un groupe d'écritures **atomique**.
    - Les helpers DB reçoivent `tx` et ne committent jamais seuls : c'est le bloc qui décide.
    - Une exception dans le bloc, c'est un **rollback** : aucune écriture partielle ne subsiste.

??? tip "Astuces"
    Les appels session (`_start_session`, `set_session_cookie`) reviennent à chaque écriture protégée.
    Si vous voulez simplifier, **vous** pouvez les regrouper dans une **classe façade** de votre application, sous `mvc/helpers/`.

    Forge ne l'ajoute pas au framework : le noyau reste minimal et explicite, l'ergonomie est à votre main.
    Un parcours dédié vous montre comment construire ces façades pas à pas (`Session`, `Cookies`, `Flash`) : [Construire vos façades helper](../../welcome-helpers/installation.md).

Au palier suivant, nous exposons le catalogue en API JSON protégée.

[Continuer avec API JSON protégée](json-api.md)
