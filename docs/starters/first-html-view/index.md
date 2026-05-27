# Première vue HTML

Objectif : rendre une page HTML avec `BaseController.render(...)`.

Palier 3 de la
[progression officielle des starters](../index.md#progression-recommandee),
après [Paramètres d'URL](../query-params/index.md).

## Ce que ce starter montre

- une route `/first-html-view`
- un contrôleur `FirstHtmlViewController`
- une vue `mvc/views/first_html_view/index.html`
- un appel à `BaseController.render(...)`

## Tester

Depuis le projet Forge déjà créé avec ce starter :

```bash
forge run
```

Ouvrez :

```
http://localhost:8000/first-html-view
```

## Code essentiel

```python
# mvc/routes.py
from mvc.controllers.first_html_view_controller import FirstHtmlViewController

with router.group("", public=True) as pub:
    pub.add("GET", "/first-html-view", FirstHtmlViewController.index, name="first_html_view_index")
```

```python
# mvc/controllers/first_html_view_controller.py
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class FirstHtmlViewController(BaseController):
    """Starter pédagogique : rendre une première vue HTML."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render("first_html_view/index.html", request=request)
```

```html
<!-- mvc/views/first_html_view/index.html -->
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Première vue HTML — Forge</title>
</head>
<body>
  <h1>Première vue HTML</h1>
  <p>Cette page est rendue avec <code>BaseController.render(...)</code>.</p>
</body>
</html>
```

## À retenir

- `Response.text(...)` retourne du texte directement (paliers 1 et 2).
- `BaseController.render(...)` rend une vue HTML.
- La vue se trouve dans `mvc/views/`.
- Le nom du fichier passé à `render(...)` est un chemin relatif à
  `mvc/views/`, séparateur `/`.

## Après ce starter

Passez au palier suivant : **Route dynamique**.

Vous y apprendrez à lire un paramètre de route avec :

```python
request.route_param("id", default="inconnu")
```

[Continuer avec Route dynamique](../dynamic-route/index.md)
