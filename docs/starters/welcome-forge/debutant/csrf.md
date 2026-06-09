# Le jeton CSRF

**Objectif** : comprendre le jeton CSRF avant d'écrire un vrai formulaire qui
modifie des données.

**Ce que vous allez apprendre :** après les paliers de lecture (texte, vue HTML,
route dynamique, réponse JSON), vous abordez la **sécurité des formulaires**. Le
jeton CSRF vit dans la **session** : sans session active, il reste vide et tout
envoi protégé serait refusé. Vous allez donc garantir une session pour obtenir un
jeton non vide, puis le placer dans un champ caché.

??? note "Documentation utile"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [La session HTTP](../../../reference/http/session.md) | où vit le jeton CSRF, et ce que contient une session |
    | [Le cookie HTTP](../../../reference/http/cookie.md) | comment la session est retrouvée d'une page à l'autre |
    | [La protection CSRF](../../../reference/http/csrf.md) | le mécanisme complet : jeton, vérification, `403` |
    | [L'objet Request](../../../reference/http/request.md) | d'où le serveur lit le jeton envoyé |
    | [L'objet Response](../../../reference/http/response.md) | où l'on pose le cookie de session |

??? note "L'ajout"
    Complétez d'abord les imports en tête de `mvc/controllers/welcome_controller.py` :

    ```python
    from core.security.cookies import set_session_cookie
    from core.security.session import get_session, get_session_id
    from core.sessions.manager import get_session_store
    ```

    Ces quatre fonctions viennent de trois modules du noyau.

    | Module | Fonction | Rôle |
    |---|---|---|
    | `core.security.cookies` | `set_session_cookie(response, session_id)` | Place l'identifiant de session dans le cookie de la réponse, ce qui permet de retrouver la session aux requêtes suivantes (voir [La session HTTP](../../../reference/http/session.md)). |
    | `core.security.session` | `get_session_id(request)` | Extrait et valide l'identifiant de session depuis le cookie ; `None` s'il est absent ou mal formé. |
    | | `get_session(session_id)` | Renvoie les données de la session (dont le `csrf_token`), ou `None` si elle est absente ou expirée. |
    | `core.sessions.manager` | `get_session_store()` | Renvoie le magasin de sessions actif. `.create()` y crée une session neuve (avec un `csrf_token`) et renvoie son identifiant. |

    Ajoutez une méthode privée `_start_session` et la méthode `csrf` à la classe
    `WelcomeController` :

    ```python
        @staticmethod
        def _start_session(request: Request):
            """Garantit une session active et renvoie (session_id, csrf_token).

            Le jeton CSRF vit dans la session : sans session, il serait vide.
            """
            session_id = get_session_id(request)
            session = get_session(session_id) if session_id else None
            if session is None:
                session_id = get_session_store().create()
                session = get_session(session_id)
            return session_id, session["csrf_token"]

        @staticmethod
        def csrf(request: Request) -> Response:
            session_id, csrf_token = WelcomeController._start_session(request)
            response = BaseController.render(
                "welcome/csrf.html",
                request=request,
                context={"csrf_token": csrf_token},
            )
            set_session_cookie(response, session_id)
            return response
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

    Ce formulaire n'a volontairement ni `method` ni `action` : il sert seulement à
    montrer où se place le champ caché, désormais **rempli**. Puis ajoutez la route
    dans le groupe public de `mvc/routes.py`.

??? note "Votre mvc/routes.py à ce stade"
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
    ```

??? note "Comprendre ce code"
    - `_start_session` lit la session du cookie ; s'il n'y en a pas, il en **crée**
      une avec `get_session_store().create()`. Une session neuve contient déjà un
      `csrf_token` généré aléatoirement.
    - On passe ce jeton au gabarit **explicitement** : `render(request=…)` ne peut
      pas le déduire seul ici, car la session vient d'être créée et son cookie n'est
      pas encore dans la requête.
    - `set_session_cookie(response, session_id)` pose le cookie `session_id`
      (durci : `HttpOnly`, `SameSite=Strict`, `Secure`) : aux requêtes suivantes, la
      session sera retrouvée et le jeton vérifié côté serveur.
    - Le groupe public a la protection CSRF active : un POST sans jeton valide est
      refusé (`403`). Ce palier prépare donc les formulaires des paliers suivants.

    ??? tip "Optionnel : simplifier avec une classe façade"
        Ces trois imports reviennent dès qu'on manipule la session. Si vous voulez
        simplifier, **vous** pouvez les regrouper dans une **classe façade** de votre
        application, sous `mvc/helpers/`, et n'écrire qu'un seul import :

        ```python
        from mvc.helpers import Session

        session_id = Session.current_id(request)     # au lieu de get_session_id(request)
        ...
        Session.set_cookie(response, session_id)     # au lieu de set_session_cookie(...)
        ```

        Forge ne l'ajoute pas au framework : le noyau reste minimal et explicite,
        l'ergonomie est à votre main. Un parcours dédié vous montre comment construire
        ces façades pas à pas (`Session`, `Cookies`, `Flash`) :
        [Construire vos façades helper](../../welcome-helpers/installation.md).

??? note "Tester dans le navigateur"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/welcome/csrf` | la page, le champ caché `csrf_token` désormais **rempli** (inspecter la source) |

??? note "À retenir"
    - Le jeton CSRF **vit dans la session** : sans session active, il est **vide**.
    - On garantit une session (`get_session_store().create()`) et on pose son cookie
      avec `set_session_cookie`, sinon le POST serait refusé.
    - Le jeton se transmet dans un champ caché `name="csrf_token"` du formulaire.

Au palier suivant, nous traitons un vrai formulaire POST protégé par ce jeton.

[Continuer avec Premier formulaire POST](form-post.md)
