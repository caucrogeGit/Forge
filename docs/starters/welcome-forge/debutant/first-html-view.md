# Première vue HTML

Objectif : rendre une vraie page HTML au lieu de texte brut.

**Ce que vous allez apprendre :** rendre un gabarit avec
`BaseController.render(...)`, qui passe la requête au moteur de template et
renvoie la page HTML.

## Là où nous en sommes

`WelcomeController` porte déjà `index`, `query_params` et `hello`
(paliers 1 et 2), et `mvc/routes.py` déclare `/welcome` et les deux routes
`/welcome/query-params`. Nous ajoutons une méthode, une route et un gabarit.

## L'ajout

Ajoutez cette méthode à la classe `WelcomeController` :

```python
    @staticmethod
    def html(request: Request) -> Response:
        return BaseController.render("welcome/first_html_view.html", request=request)
```

Créez le gabarit `mvc/views/welcome/first_html_view.html` :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Première vue HTML</title>
</head>
<body>
    <h1>Première vue HTML</h1>
    <p>
        Cette page est rendue par <code>BaseController.render(...)</code> :
        le contrôleur ne construit plus le texte à la main, il délègue
        l'affichage à un gabarit.
    </p>
</body>
</html>
```

Puis ajoutez la route dans le groupe public de `mvc/routes.py`.

## Votre mvc/routes.py à ce stade

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.welcome_controller import WelcomeController

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET", "/", HomeController.index, name="home-index")
    pub.add("GET",  "/welcome", WelcomeController.index, name="welcome-index")
    pub.add("GET",  "/welcome/query-params", WelcomeController.query_params, name="welcome-query_params")
    pub.add("GET",  "/welcome/hello", WelcomeController.hello, name="welcome-hello")
    pub.add("GET",  "/welcome/html", WelcomeController.html, name="welcome-html")
```

## Comprendre ce code

- `BaseController.render("welcome/first_html_view.html", request=request)`
  cherche le gabarit sous `mvc/views/` et le rend en HTML.
- Le chemin du gabarit est relatif à `mvc/views/` : ici le fichier vit dans
  `mvc/views/welcome/`.
- Passer `request=request` permet au gabarit d'accéder au contexte de la
  requête courante.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/welcome/html` | la page HTML « Première vue HTML » |

## À retenir

- `BaseController.render(...)` renvoie une page HTML rendue par le moteur de
  template.
- Les gabarits vivent sous `mvc/views/`.
- Le contrôleur reste mince : il choisit le gabarit, le gabarit gère
  l'affichage.

Au palier suivant, nous lisons une valeur directement dans le chemin de
l'URL.

[Continuer avec Route dynamique](dynamic-route.md)
