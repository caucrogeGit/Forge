# Écrire en base

**Objectif**{ .intro-label } : enregistrer une nouvelle ligne en base à partir d'un formulaire, avec une requête `INSERT` paramétrée.

**Ce que vous allez apprendre :**{ .intro-label } insérer une donnée avec `insert(...)`, après avoir validé la saisie côté serveur comme au palier « Validation serveur ».

`MessageController` possède déjà la méthode `index` (palier précédent) qui lit la table `first_sql_messages`, et `mvc/routes.py` déclare la route `/message`.
L'import `insert` et la constante `INSERT_MESSAGE` sont déjà présents dans le contrôleur.

Nous ajoutons deux méthodes, deux routes et un gabarit.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [L'objet Request](../../../reference/http/request.md) | l'accesseur `form(...)` pour lire la saisie |
    | [La protection CSRF](../../../reference/http/csrf.md) | le champ caché `csrf_token` requis pour le POST |
    | [Migrations SQL](../../../features/migrations.md) | la table `first_sql_messages` créée au palier précédent |

??? note "Contrôleurs"
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

    | Élément | Rôle |
    |---|---|
    | `insert(INSERT_MESSAGE, (content,))` | Exécute la requête `INSERT ... VALUES (?)` en passant la valeur séparément : le `?` est un paramètre lié, ce qui protège contre l'injection SQL. |
    | `.strip()` + `status=422` | La saisie est validée avant l'écriture : un message vide est refusé, comme au palier « Validation serveur ». |
    | `BaseController.csrf_token(request)` | Fournit le jeton à placer dans le champ caché du formulaire. |

    Après l'insertion, la ligne devient visible : `/message` peut désormais renvoyer un autre contenu si vous en avez enregistré un.

??? note "Routes"
    Ajoutez les deux routes (`GET` et `POST`) dans le groupe public de `mvc/routes.py` :

    ```python
    # mvc/routes.py
    from core.http.router import Router
    from mvc.controllers.home_controller import HomeController
    from mvc.controllers.welcome_controller import WelcomeController
    from mvc.controllers.message_controller import MessageController

    router = Router()

    with router.group("", public=True) as public:
        public.add("GET", "/", HomeController.index, name="home-index")
        public.add("GET",  "/welcome", WelcomeController.index, name="welcome-index")
        public.add("GET",  "/welcome/hello", WelcomeController.hello, name="welcome-hello")
        public.add("GET",  "/welcome/html", WelcomeController.html, name="welcome-html")
        public.add("GET",  "/welcome/article/{id}", WelcomeController.article, name="welcome-article")
        public.add("GET",  "/welcome/debug", WelcomeController.debug, name="welcome-debug")
        public.add("GET",  "/welcome/json", WelcomeController.json_demo, name="welcome-json")
        public.add("GET",  "/welcome/csrf", WelcomeController.csrf, name="welcome-csrf")
        public.add("GET",  "/welcome/form", WelcomeController.form, name="welcome-form")
        public.add("POST", "/welcome/form-submit", WelcomeController.form_submit, name="welcome-form_submit")
        public.add("GET",  "/welcome/validate", WelcomeController.validate, name="welcome-validate")
        public.add("POST", "/welcome/validate-submit", WelcomeController.validate_submit, name="welcome-validate_submit")
        public.add("GET",  "/message", MessageController.index, name="message-index")
        public.add("GET",  "/message/create", MessageController.create, name="message-create")
        public.add("POST", "/message/store", MessageController.store, name="message-store")
    ```

??? note "Vues"
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

??? note "Tests"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/message/create` | le formulaire d'enregistrement |
    | Soumettre `Bonjour la base` | `Message enregistré : Bonjour la base` |
    | Soumettre vide | `Le message est obligatoire` (statut `422`) |

??? note "À retenir"
    - `insert(requete, (valeur,))` écrit une ligne avec des paramètres liés.
    - Le `?` paramétré protège contre l'injection SQL.
    - On valide toujours la saisie avant d'écrire en base.

Vous avez parcouru tous les paliers du niveau débutant. Place au bilan.

[Continuer avec le Bilan](bilan.md)
