# Premier formulaire POST

Objectif : recevoir les données d'un formulaire envoyé en POST et les lire
côté serveur.

**Ce que vous allez apprendre :** afficher un formulaire, le soumettre en
POST, et lire un champ avec `request.form("name", default=...)`, le POST
étant protégé par le jeton CSRF du palier précédent.

## Là où nous en sommes

`WelcomeController` porte déjà les méthodes des paliers 1 à 7, et
`mvc/routes.py` déclare les routes jusqu'à `/csrf`. Nous ajoutons deux
méthodes (afficher le formulaire, traiter l'envoi), deux routes et un
gabarit.

## L'ajout

Ajoutez ces deux méthodes à la classe `WelcomeController` :

```python
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
```

Créez le gabarit `mvc/views/welcome/form_post.html` :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Premier formulaire POST</title>
</head>
<body>
    <h1>Premier formulaire POST</h1>
    <form method="post" action="/form-post">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <label>Prénom : <input type="text" name="name" value="Forge"></label>
        <button type="submit">Envoyer</button>
    </form>
</body>
</html>
```

Puis ajoutez les deux routes (`GET` et `POST` sur `/form-post`) dans le
groupe public de `mvc/routes.py`.

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
    pub.add("GET",  "/form-post", WelcomeController.form, name="form_post_index")
    pub.add("POST", "/form-post", WelcomeController.form_submit, name="form_post_submit")
```

## Comprendre ce code

- Deux routes partagent le chemin `/form-post` : `GET` affiche le
  formulaire, `POST` traite l'envoi.
- `request.form("name", default="Forge")` lit un champ du corps du
  formulaire, là où `request.param(...)` lisait la chaîne de requête.
- Le champ caché `csrf_token` du gabarit permet au POST de passer la
  protection CSRF du groupe public.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/form-post` | le formulaire avec le champ prénom |
| Soumettre avec `Roger` | `Bonjour Roger` |
| Soumettre en laissant `Forge` | `Bonjour Forge` |

## À retenir

- `request.form(cle, default=...)` lit un champ envoyé en POST.
- Un même chemin peut servir `GET` (afficher) et `POST` (traiter).
- Le champ caché `csrf_token` est requis pour que le POST soit accepté.

Au palier suivant, nous refusons une saisie invalide côté serveur.

[Continuer avec Validation serveur](server-validation.md)
