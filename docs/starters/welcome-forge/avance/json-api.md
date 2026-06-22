# API JSON protégée

**Objectif**{ .intro-label } : exposer le catalogue en **JSON** à des clients, derrière un **jeton d'authentification**.

**Ce que vous allez apprendre :**{ .intro-label } renvoyer du JSON avec `Response.json`, et **protéger** la route par un jeton `Authorization: Bearer …` lu via `request.header(...)`. Sans jeton valide, l'API répond `401`.

Le catalogue est complet côté navigateur : lister et créer.

Nous l'exposons maintenant à des clients (front JavaScript, script, autre service) sous forme d'**API JSON protégée**, en réutilisant la jointure du premier palier.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [API JSON légère](../../../reference/api-json.md) | la façon canonique d'exposer du JSON dans Forge |
    | [L'objet Request](../../../reference/http/request.md) | l'accesseur `header(...)`, dont `Authorization` |
    | [L'objet Response](../../../reference/http/response.md) | `Response.json(data, status=…)` : données **et** code HTTP |

??? note "Contrôleurs"
    Ajoutez le jeton et la méthode dans `mvc/controllers/article_controller.py` :

    ```python
    API_TOKEN = "forge-demo-token"


    class ArticleController(BaseController):

        # … index / create / store inchangés …

        @staticmethod
        def api_index(request: Request) -> Response:
            authorization = request.header("Authorization") or ""
            if authorization != f"Bearer {API_TOKEN}":
                return Response.json({"error": "Jeton manquant ou invalide."}, status=401)
            articles = fetch_all(SELECT_ARTICLES_WITH_CATEGORY)
            return Response.json({"articles": articles})
    ```

    | Élément | Rôle |
    |---|---|
    | `request.header("Authorization")` | Lit l'en-tête envoyé par le client ; on le compare à `Bearer <jeton>` (convention des API à jeton). |
    | Refus → `status=401` | Si le jeton ne correspond pas, on renvoie **immédiatement** : on ne lit même pas la base. La sécurité vient **avant** la donnée. |
    | `fetch_all(SELECT_ARTICLES_WITH_CATEGORY)` | Réutilise la jointure du premier palier ; les dictionnaires sont directement sérialisables. |

    Le jeton est ici une **constante de démonstration**.
    Une vraie application le garderait secret (hors du code versionné) et le renouvellerait.

??? note "Routes"
    Déclarez la route `/article/api-index` dans `mvc/routes.py` :

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
        public.add("GET",  "/article/api-index", ArticleController.api_index, name="article-api_index")
    ```

??? note "Tests"
    Sans jeton, la requête est refusée :

    ```bash
    curl -k https://localhost:8000/article/api-index
    # {"error": "Jeton manquant ou invalide."}  (HTTP 401)
    ```

    Avec le jeton de démonstration, l'API renvoie les données :

    ```bash
    curl -k -H "Authorization: Bearer forge-demo-token" https://localhost:8000/article/api-index
    # {"articles": [{"id": 1, "title": "…", "category": "…"}, …]}
    ```

??? note "À retenir"
    - `Response.json(data, status=…)` renvoie données **et** code HTTP.
    - `request.header(...)` donne accès aux en-têtes, dont `Authorization`.
    - On vérifie l'autorisation **avant** de produire la donnée ; un refus, c'est `401`.

Vous avez parcouru les trois paliers du niveau avancé. Place au bilan.

[Bilan du niveau avancé](bilan.md)
