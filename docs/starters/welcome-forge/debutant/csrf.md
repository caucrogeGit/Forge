# Le jeton CSRF

Objectif : comprendre le jeton CSRF avant d'écrire un vrai formulaire qui
modifie des données.

**Ce que vous allez apprendre :** obtenir un jeton CSRF avec
`BaseController.csrf_token(request)` et le placer dans un champ caché du
formulaire, pour protéger les requêtes POST.

## Là où nous en sommes

`WelcomeController` porte déjà les méthodes des paliers 1 à 6, et
`mvc/routes.py` déclare les routes jusqu'à `/json-response`. Nous ajoutons
une méthode, une route et un gabarit illustratif.

## L'ajout

Ajoutez cette méthode à la classe `WelcomeController` :

```python
    @staticmethod
    def csrf_demo(request: Request) -> Response:
        return BaseController.render(
            "welcome/csrf.html",
            request=request,
            context={"csrf_token": BaseController.csrf_token(request)},
        )
```

Créez le gabarit `mvc/views/welcome/csrf.html` :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Le jeton CSRF</title>
</head>
<body>
    <h1>Le jeton CSRF</h1>
    <p>
        Le champ caché ci-dessous transporte le jeton CSRF. Il prouve que la
        requête provient bien de cette page, et non d'un site tiers.
    </p>
    <form>
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <label>Prénom : <input type="text" name="name"></label>
    </form>
</body>
</html>
```

Ce formulaire n'a volontairement ni `method` ni `action` : il sert seulement
à montrer où se place le champ caché. Puis ajoutez la route dans le groupe
public de `mvc/routes.py`.

## Votre mvc/routes.py à ce stade

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.welcome_controller import WelcomeController

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
```

## Comprendre ce code

- `BaseController.csrf_token(request)` renvoie le jeton CSRF de la session
  courante.
- On le passe au gabarit via `context={"csrf_token": ...}`, puis on le place
  dans un champ caché `name="csrf_token"`.
- Le groupe public a la protection CSRF active : un POST sans jeton valide
  sera refusé. Ce palier prépare donc les formulaires des paliers suivants.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/csrf` | la page avec le champ caché `csrf_token` rempli |

## À retenir

- Le jeton CSRF prouve qu'une requête vient bien de votre site.
- `BaseController.csrf_token(request)` fournit ce jeton.
- Il se transmet dans un champ caché `name="csrf_token"` du formulaire.

Au palier suivant, nous traitons un vrai formulaire POST protégé par ce jeton.

[Continuer avec Premier formulaire POST](form-post.md)
