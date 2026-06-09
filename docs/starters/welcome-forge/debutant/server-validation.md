# Validation serveur

Objectif : refuser une saisie invalide côté serveur, sans jamais faire
confiance aveuglément au navigateur.

**Ce que vous allez apprendre :** nettoyer une valeur avec `.strip()` et
renvoyer une réponse d'erreur avec un statut HTTP `422` quand la saisie est
vide.

## Là où nous en sommes

`WelcomeController` porte déjà les méthodes des paliers 1 à 8, et
`mvc/routes.py` déclare les routes jusqu'à `/welcome/form`. Nous ajoutons deux
méthodes, deux routes et un gabarit.

## L'ajout

Ajoutez ces deux méthodes à la classe `WelcomeController` :

```python
    @staticmethod
    def validate(request: Request) -> Response:
        session_id, csrf_token = WelcomeController._start_session(request)
        response = BaseController.render(
            "welcome/server_validation.html",
            request=request,
            context={"csrf_token": csrf_token},
        )
        set_session_cookie(response, session_id)
        return response

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
    <form method="post" action="/welcome/validate-submit">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <label>Prénom : <input type="text" name="name" value=""></label>
        <button type="submit">Envoyer</button>
    </form>
</body>
</html>
```

Puis ajoutez les deux routes (`GET` et `POST` sur `/welcome/validate`) dans
le groupe public de `mvc/routes.py`.

## Votre mvc/routes.py à ce stade

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.welcome_controller import WelcomeController

router = Router()

with router.group("", public=True) as public:
    public.add("GET", "/", HomeController.index, name="home-index")
    public.add("GET",  "/welcome", WelcomeController.index, name="welcome-index")
    public.add("GET",  "/welcome/hello", WelcomeController.hello, name="welcome-hello")
    public.add("GET",  "/welcome/html", WelcomeController.html, name="welcome-html")
    public.add("GET",  "/welcome/article/{id}", WelcomeController.article, name="welcome-article")
    public.add("GET",  "/welcome/debug", WelcomeController.debug, name="welcome-debug")
    public.add("GET",  "/welcome/json", WelcomeController.json, name="welcome-json")
    public.add("GET",  "/welcome/csrf", WelcomeController.csrf, name="welcome-csrf")
    public.add("GET",  "/welcome/form", WelcomeController.form, name="welcome-form")
    public.add("POST", "/welcome/form-submit", WelcomeController.form_submit, name="welcome-form_submit")
    public.add("GET",  "/welcome/validate", WelcomeController.validate, name="welcome-validate")
    public.add("POST", "/welcome/validate-submit", WelcomeController.validate_submit, name="welcome-validate_submit")
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
| `https://localhost:8000/welcome/validate` | le formulaire avec un champ prénom vide |
| Soumettre avec `Roger` | `Bonjour Roger` |
| Soumettre vide ou avec des espaces | `Le prénom est obligatoire` (statut `422`) |

## À retenir

- La validation se fait toujours côté serveur, jamais seulement dans le
  navigateur.
- `.strip()` neutralise les saisies qui ne sont que des espaces.
- Le statut `422` exprime une donnée invalide de façon claire.

Au palier suivant, nous lisons pour la première fois des données en base SQL.

[Continuer avec Première base SQL](first-sql.md)
