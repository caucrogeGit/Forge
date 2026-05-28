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

## Classes Forge utilisées

| Classe | Rôle dans ce starter | Référence |
|--------|----------------------|-----------|
| `Request` | Reçue par la méthode et transmise à `render(...)`. | [Request](../../reference/http.md#3-request-reference) |
| `Response` | Retournée par le contrôleur (produite ici via `render`). | [Response](../../reference/http.md#4-response-reference) |
| `BaseController` | Fournit le helper `render(...)` qui rend la vue HTML. | [BaseController](../../reference/api.md#coremvccontroller) |

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

### Comprendre ce code

- Une seule route publique : `GET /first-html-view` →
  `FirstHtmlViewController.index`.
- Le `name="first_html_view_index"` permet de référencer cette URL
  depuis un template ou une redirection sans la coder en dur.

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

### Comprendre ce code

- Le contrôleur ne construit plus la réponse à la main : il délègue à
  `BaseController.render(...)` la production du HTML.
- `render(...)` charge le template `first_html_view/index.html` depuis
  `mvc/views/`, l'exécute via Jinja2, et retourne une `Response` HTML
  prête à être renvoyée au navigateur.
- Pour transmettre des données au template, on passe un `context={...}`
  à `render(...)`. Ce starter n'en a pas besoin — la vue est statique.
- À comparer avec `Response.text(...)` : ici, la réponse passe par un
  fichier `.html` séparé, ce qui rend le contenu éditable sans toucher
  au contrôleur.

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
