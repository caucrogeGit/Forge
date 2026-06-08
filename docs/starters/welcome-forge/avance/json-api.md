# API JSON protégée

Objectif : exposer le catalogue en **JSON** à des clients, derrière un **jeton
d'authentification**.

**Ce que vous allez apprendre :** renvoyer du JSON avec `Response.json`, et
**protéger** la route par un jeton `Authorization: Bearer …` lu via
`request.header(...)`. Sans jeton valide, l'API répond `401`.

## Là où nous en sommes

Le catalogue est complet côté navigateur : lister, créer, attacher un document.
Nous l'exposons maintenant à des clients (front JavaScript, script, autre
service) sous forme d'**API JSON protégée**, en réutilisant la jointure du
premier palier.

## L'ajout

Ajoutez le jeton et la méthode dans `mvc/controllers/article_controller.py` :

```python
API_TOKEN = "forge-demo-token"


class ArticleController(BaseController):

    # … index / create / store / attach / attach_store inchangés …

    @staticmethod
    def api_index(request: Request) -> Response:
        authorization = request.header("Authorization") or ""
        if authorization != f"Bearer {API_TOKEN}":
            return Response.json({"error": "Jeton manquant ou invalide."}, status=401)
        articles = fetch_all(SELECT_ARTICLES_WITH_CATEGORY)
        return Response.json({"articles": articles})
```

Puis déclarez la route `/api/articles` dans `mvc/routes.py`.

## Votre mvc/routes.py à ce stade

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.article_controller import ArticleController

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET",  "/", HomeController.index, name="home_index")
    pub.add("GET",  "/articles", ArticleController.index, name="articles_index")
    pub.add("GET",  "/articles/new", ArticleController.create, name="articles_new")
    pub.add("POST", "/articles", ArticleController.store, name="articles_store")
    pub.add("GET",  "/articles/{id}/attach", ArticleController.attach, name="articles_attach")
    pub.add("POST", "/articles/{id}/attach", ArticleController.attach_store, name="articles_attach_store")
    pub.add("GET",  "/api/articles", ArticleController.api_index, name="api_articles")
```

## Comprendre ce code

- `request.header("Authorization")` lit l'en-tête envoyé par le client. On le
  compare à `Bearer <jeton>` : c'est la convention des API à jeton.
- Si le jeton ne correspond pas, on renvoie **immédiatement** `Response.json(…,
  status=401)` : on ne lit même pas la base. La sécurité vient **avant** la donnée.
- Sinon, on réutilise la jointure `SELECT_ARTICLES_WITH_CATEGORY` du palier 1 et on
  renvoie les lignes en JSON ; `fetch_all` rend des dictionnaires directement
  sérialisables.
- Le jeton est ici une **constante de démonstration**. Une vraie application le
  garderait secret (hors du code versionné) et le renouvellerait.

## Tester avec curl

Sans jeton, la requête est refusée :

```bash
curl -k https://localhost:8000/api/articles
# {"error": "Jeton manquant ou invalide."}  (HTTP 401)
```

Avec le jeton de démonstration, l'API renvoie les données :

```bash
curl -k -H "Authorization: Bearer forge-demo-token" https://localhost:8000/api/articles
# {"articles": [{"id": 1, "title": "…", "category": "…"}, …]}
```

## À retenir

- `Response.json(data, status=…)` renvoie données **et** code HTTP.
- `request.header(...)` donne accès aux en-têtes, dont `Authorization`.
- On vérifie l'autorisation **avant** de produire la donnée ; un refus, c'est `401`.

Vous avez parcouru les quatre paliers du niveau avancé. Place au bilan.

[Bilan du niveau avancé](bilan.md)
