# Validation serveur

Objectif : refuser une saisie invalide côté serveur, sans jamais faire
confiance aveuglément au navigateur.

**Ce que vous allez apprendre :** nettoyer une valeur avec `.strip()` et
renvoyer une réponse d'erreur avec un statut HTTP `422` quand la saisie est
vide.

## Là où nous en sommes

`WelcomeController` porte déjà les méthodes des paliers 1 à 8, et
`mvc/routes.py` déclare les routes jusqu'à `/form-post`. Nous ajoutons deux
méthodes, deux routes et un gabarit.

## L'ajout

Ajoutez ces deux méthodes à la classe `WelcomeController` :

```python
    @staticmethod
    def validate(request: Request) -> Response:
        return BaseController.render(
            "welcome/server_validation.html",
            request=request,
            context={"csrf_token": BaseController.csrf_token(request)},
        )

    @staticmethod
    def validate_submit(request: Request) -> Response:
        name = request.form("name", default="").strip()
        if not name:
            return Response.text("Le prénom est obligatoire", status=422)
        return Response.text(f"Bonjour {name}")
```

Créez le gabarit `mvc/views/welcome/server_validation.html` :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Validation serveur</title>
</head>
<body>
    <h1>Validation serveur</h1>
    <form method="post" action="/server-validation">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <label>Prénom : <input type="text" name="name" value=""></label>
        <button type="submit">Envoyer</button>
    </form>
</body>
</html>
```

Puis ajoutez les deux routes (`GET` et `POST` sur `/server-validation`) dans
le groupe public de `mvc/routes.py`.

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
    pub.add("GET",  "/server-validation", WelcomeController.validate, name="server_validation_index")
    pub.add("POST", "/server-validation", WelcomeController.validate_submit, name="server_validation_submit")
```

## Comprendre ce code

- `.strip()` retire les espaces de début et de fin : une saisie qui ne
  contient que des espaces devient une chaîne vide.
- `if not name:` détecte la saisie vide et renvoie une erreur explicite.
- Le statut `422` (« contenu non traitable ») signale au client que la
  donnée envoyée est invalide, sans planter ni accepter une valeur fausse.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/server-validation` | le formulaire avec un champ prénom vide |
| Soumettre avec `Roger` | `Bonjour Roger` |
| Soumettre vide ou avec des espaces | `Le prénom est obligatoire` (statut `422`) |

## À retenir

- La validation se fait toujours côté serveur, jamais seulement dans le
  navigateur.
- `.strip()` neutralise les saisies qui ne sont que des espaces.
- Le statut `422` exprime une donnée invalide de façon claire.

Au palier suivant, nous lisons pour la première fois des données en base SQL.

[Continuer avec Première base SQL](first-sql.md)
