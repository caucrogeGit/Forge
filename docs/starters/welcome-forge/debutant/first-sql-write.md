# Écrire en base

Objectif : enregistrer une nouvelle ligne en base à partir d'un formulaire,
avec une requête `INSERT` paramétrée.

**Ce que vous allez apprendre :** insérer une donnée avec `insert(...)`,
après avoir validé la saisie côté serveur comme au palier 9.

## Là où nous en sommes

`MessageController` possède déjà la méthode `index` (palier 10) qui lit la
table `first_sql_messages`, et `mvc/routes.py` déclare la route `/message`.
L'import `insert` et la constante `INSERT_MESSAGE` sont déjà présents dans le
contrôleur. Nous ajoutons deux méthodes, deux routes et un gabarit.

## L'ajout

Ajoutez ces deux méthodes à la classe `MessageController` :

```python
    @staticmethod
    def create(request: Request) -> Response:
        return BaseController.render(
            "message/first_sql_write.html",
            request=request,
            context={"csrf_token": BaseController.csrf_token(request)},
        )

    @staticmethod
    def store(request: Request) -> Response:
        content = request.form("content", default="").strip()
        if not content:
            return Response.text("Le message est obligatoire", status=422)
        insert(INSERT_MESSAGE, (content,))
        return Response.text(f"Message enregistré : {content}")
```

Créez le gabarit `mvc/views/message/first_sql_write.html` :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Écrire en base</title>
</head>
<body>
    <h1>Écrire en base</h1>
    <form method="post" action="/message/store">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <label>Message : <input type="text" name="content" value=""></label>
        <button type="submit">Enregistrer</button>
    </form>
</body>
</html>
```

Puis ajoutez les deux routes (`GET` et `POST` sur `/message/create`) dans le
groupe public de `mvc/routes.py`.

## Votre mvc/routes.py à ce stade

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.welcome_controller import WelcomeController
from mvc.controllers.message_controller import MessageController

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
    pub.add("GET",  "/welcome/validate", WelcomeController.validate, name="welcome-validate")
    pub.add("POST", "/welcome/validate-submit", WelcomeController.validate_submit, name="welcome-validate_submit")
    pub.add("GET",  "/message", MessageController.index, name="message-index")
    pub.add("GET",  "/message/create", MessageController.create, name="message-create")
    pub.add("POST", "/message/store", MessageController.store, name="message-store")
```

## Comprendre ce code

- `insert(INSERT_MESSAGE, (content,))` exécute la requête `INSERT ... VALUES
  (?)` en passant la valeur séparément : le `?` est un paramètre lié, ce qui
  protège contre l'injection SQL.
- La saisie est validée avant l'écriture : un message vide est refusé avec un
  statut `422`, comme au palier 9.
- Après l'insertion, la ligne devient visible : `/message` peut désormais
  renvoyer un autre contenu si vous en avez enregistré un.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/message/create` | le formulaire d'enregistrement |
| Soumettre `Bonjour la base` | `Message enregistré : Bonjour la base` |
| Soumettre vide | `Le message est obligatoire` (statut `422`) |

## À retenir

- `insert(requete, (valeur,))` écrit une ligne avec des paramètres liés.
- Le `?` paramétré protège contre l'injection SQL.
- On valide toujours la saisie avant d'écrire en base.

Vous avez parcouru les onze paliers. Place au bilan du niveau débutant.

[Continuer avec le Bilan](bilan.md)
