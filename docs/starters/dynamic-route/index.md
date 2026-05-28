# Route dynamique

Objectif : lire une partie variable de l'URL avec `request.route_param(...)`.

Palier 4 de la
[progression officielle des starters](../index.md#progression-recommandee),
après [Première vue HTML](../first-html-view/index.md).

## Ce que ce starter montre

- une route `/dynamic-route/articles/{id}`
- un contrôleur `DynamicRouteController`
- une lecture avec `request.route_param("id")`
- une réponse texte avec `Response.text(...)`

Aucune vue HTML.
Aucune base de données.
Aucun formulaire.
Aucun CRUD.

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Lire la partie variable de l'URL avec `request.route_param(...)`. | [Request](../../reference/http.md#3-request-reference) |
| `Response` | Construire la réponse texte avec `Response.text(...)`. | [Response](../../reference/http.md#4-response-reference) |
| `BaseController` | Classe parente du contrôleur. | [BaseController](../../reference/api.md#coremvccontroller) |
| Routage | Déclarer le segment dynamique `{id}` dans `mvc/routes.py`. | [Routage](../../reference/api.md#corehttprouter) |

## Tester

Depuis le projet Forge déjà créé avec ce starter :

```bash
forge run
```

Ouvrez :

```
http://localhost:8000/dynamic-route/articles/42
```

Résultat attendu :

```
Article 42
```

Essayez d'autres valeurs : `/dynamic-route/articles/forge` retourne
`Article forge`, `/dynamic-route/articles/3.14` retourne
`Article 3.14`. Le segment `{id}` accepte n'importe quelle chaîne
non vide.

## Code essentiel

```python
# mvc/routes.py
from mvc.controllers.dynamic_route_controller import DynamicRouteController

with router.group("", public=True) as pub:
    pub.add("GET", "/dynamic-route/articles/{id}", DynamicRouteController.show, name="dynamic_route_article_show")
```

### Comprendre ce code

- Le segment `{id}` dans le motif de route est une partie *variable*
  de l'URL : Forge capture sa valeur et la rend disponible au contrôleur.
- Contrairement à `?id=...` (query string), le segment dynamique fait
  partie du chemin lui-même. Cela produit des URL plus lisibles pour
  identifier une ressource : `/articles/42` plutôt que `/articles?id=42`.

```python
# mvc/controllers/dynamic_route_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class DynamicRouteController(BaseController):
    """Starter pédagogique : lire un paramètre de route."""

    @staticmethod
    def show(request: Request) -> Response:
        article_id = request.route_param("id", default="inconnu")
        return Response.text(f"Article {article_id}")
```

### Comprendre ce code

- `request.route_param("id", default="inconnu")` lit la valeur du
  segment `{id}` déclaré dans la route. Le `default=` protège contre
  une mauvaise déclaration de route.
- Ne pas confondre :
  - `request.param(...)` lit la *query string* (`?id=42`) ;
  - `request.route_param(...)` lit un segment dynamique du chemin
    (`/articles/42`).
- Cette forme est typique pour identifier une ressource précise :
  l'article 42, le contact 7, le produit 18.

## À retenir

- `{id}` dans la route indique une partie variable de l'URL.
- Forge place cette valeur dans les paramètres de route.
- Le contrôleur lit cette valeur avec `request.route_param("id")`.
- `request.route_param(...)` est différent de `request.param(...)` :
  - `request.param(...)` lit la *query string* (`?id=42`) ;
  - `request.route_param(...)` lit un segment dynamique de l'URL
    (`/articles/42`).

## Après ce starter

Passez au palier suivant : **Inspecter une requête**.

Vous y apprendrez à explorer la structure d'une requête avec :

```python
Response.debug(request.data)
```

[Continuer avec Inspecter une requête](../request-debug/index.md)
