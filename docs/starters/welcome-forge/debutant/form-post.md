# Premier formulaire POST

Objectif : recevoir les données d'un formulaire envoyé en POST et les lire
côté serveur.

**Ce que vous allez apprendre :** afficher un formulaire, le soumettre en
POST, et lire un champ avec `request.form("name", default=...)`, le POST
étant protégé par le jeton CSRF du palier précédent.

## Là où nous en sommes

`WelcomeController` porte déjà les méthodes des paliers 1 à 7, dont le helper
`_start_session` introduit au palier CSRF, et `mvc/routes.py` déclare les routes
jusqu'à `/welcome/csrf`. Nous ajoutons deux méthodes (afficher le formulaire, traiter
l'envoi), deux routes et un gabarit.

## L'ajout

Ajoutez ces deux méthodes à la classe `WelcomeController`. Comme ce formulaire
fait un **vrai POST protégé**, `form` réutilise `_start_session` (garantir la
session, donc un jeton non vide) et pose le cookie de session :

```python
    @staticmethod
    def form(request: Request) -> Response:
        session_id, csrf_token = WelcomeController._start_session(request)
        response = BaseController.render(
            "welcome/form_post.html",
            request=request,
            context={"csrf_token": csrf_token},
        )
        set_session_cookie(response, session_id)
        return response

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
    <form method="post" action="/welcome/form-submit">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <label>Prénom : <input type="text" name="name" value="Forge"></label>
        <button type="submit">Envoyer</button>
    </form>
</body>
</html>
```

Puis ajoutez les deux routes (`GET` et `POST` sur `/welcome/form`) dans le
groupe public de `mvc/routes.py`.

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
    pub.add("GET",  "/welcome/article/{id}", WelcomeController.article, name="welcome-article")
    pub.add("GET",  "/welcome/debug", WelcomeController.debug, name="welcome-debug")
    pub.add("GET",  "/welcome/json", WelcomeController.json, name="welcome-json")
    pub.add("GET",  "/welcome/csrf", WelcomeController.csrf, name="welcome-csrf")
    pub.add("GET",  "/welcome/form", WelcomeController.form, name="welcome-form")
    pub.add("POST", "/welcome/form-submit", WelcomeController.form_submit, name="welcome-form_submit")
```

## Comprendre ce code

- Deux routes partagent le chemin `/welcome/form` : `GET` affiche le
  formulaire, `POST` traite l'envoi.
- `request.form("name", default="Forge")` lit un champ du corps du
  formulaire, là où `request.query(...)` lisait la chaîne de requête.
- Le champ caché `csrf_token` du gabarit permet au POST de passer la
  protection CSRF du groupe public.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/welcome/form` | le formulaire avec le champ prénom |
| Soumettre avec `Roger` | `Bonjour Roger` |
| Soumettre en laissant `Forge` | `Bonjour Forge` |

## À retenir

- `request.form(cle, default=...)` lit un champ envoyé en POST.
- Un même chemin peut servir `GET` (afficher) et `POST` (traiter).
- Le champ caché `csrf_token` est requis pour que le POST soit accepté.

Au palier suivant, nous refusons une saisie invalide côté serveur.

[Continuer avec Validation serveur](server-validation.md)
