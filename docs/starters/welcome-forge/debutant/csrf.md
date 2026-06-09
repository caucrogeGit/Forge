# Le jeton CSRF

Objectif : comprendre le jeton CSRF avant d'écrire un vrai formulaire qui
modifie des données.

**Ce que vous allez apprendre :** le jeton CSRF **vit dans la session**. Sans
session active, `BaseController.csrf_token(request)` renvoie une chaîne **vide**,
et tout POST protégé serait refusé. Ce palier montre donc comment **garantir une
session** pour obtenir un jeton non vide, puis le placer dans un champ caché.

## Là où nous en sommes

`WelcomeController` porte déjà les méthodes des paliers 1 à 6, et `mvc/routes.py`
déclare les routes jusqu'à `/welcome/json`. Nous abordons la sécurité des
formulaires : pour cela, il faut une **session** (on approfondira la session au
niveau intermédiaire ; ici on s'en sert juste pour porter le jeton CSRF).

!!! warning "Pourquoi le CSRF fonctionne en duo avec la session"
    Le jeton CSRF est généré et stocké **dans la session**, dès sa création :
    CSRF et session fonctionnent en duo. Tant qu'aucune session n'existe (aucun
    cookie `session_id`), `csrf_token(request)` retourne `""`. Il faut donc
    **créer une session** et **poser son cookie** sur la réponse pour que le
    champ caché soit rempli et que le POST passe.

## L'ajout

Complétez d'abord les imports en tête de `mvc/controllers/welcome_controller.py` :

```python
from core.security.cookies import set_session_cookie
from core.security.session import get_session, get_session_id
from core.sessions.manager import get_session_store
```

Ces quatre fonctions viennent de trois modules du noyau. Les voici regroupées
par module, comme on documenterait les méthodes d'une classe :

`core.security.cookies` : poser le cookie de session sur la réponse.

- `set_session_cookie(response, session_id)` : écrit l'en-tête `Set-Cookie` de la
  session sur la réponse, durci par défaut (`__Host-`, `Secure`, `HttpOnly`,
  `SameSite=Strict`). C'est ce qui permet au navigateur de renvoyer la session à
  la requête suivante.

`core.security.session` : lire la session côté requête.

- `get_session_id(request) -> str | None` : extrait et valide l'identifiant de
  session depuis le cookie de la requête ; renvoie `None` si le cookie est absent
  ou mal formé.
- `get_session(session_id) -> dict | None` : renvoie les données de la session
  (dont le `csrf_token`), ou `None` si elle n'existe pas ou a expiré.

`core.sessions.manager` : accéder au magasin de sessions.

- `get_session_store()` : renvoie le magasin de sessions actif (mémoire par
  défaut, fichier ou MariaDB selon la configuration). On appelle ensuite
  `.create()` dessus pour créer une session neuve et obtenir son identifiant ;
  une session neuve contient déjà un `csrf_token`.

Ajoutez un petit helper et la méthode `csrf` à la classe `WelcomeController` :

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
```

## Comprendre ce code

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

???+ tip "Optionnel : regrouper ces imports dans un helper applicatif"
    Ces trois imports reviennent dès qu'on manipule la session. Si vous voulez
    simplifier, **vous** pouvez les regrouper dans un helper de votre application,
    sous `mvc/helpers/`. Forge ne l'ajoute pas au framework : le noyau reste
    minimal et explicite, l'ergonomie est à votre main.

    Créez `mvc/helpers/session.py` :

    ```python
    # mvc/helpers/session.py
    """Façade de confort pour la session non-auth (helper applicatif)."""
    from core.security.cookies import set_session_cookie as _set_cookie
    from core.security.session import get_session_id as _get_id
    from core.sessions.manager import get_session_store as _store


    def new() -> str:
        return _store().create()

    def current_id(request) -> str | None:
        return _get_id(request)

    def get(session_id: str) -> dict | None:
        return _store().get(session_id)

    def set_cookie(response, session_id, *, max_age=None) -> None:
        _set_cookie(response, session_id, max_age=max_age)
    ```

    Le helper `_start_session` du contrôleur devient alors, avec un seul import :

    ```python
    from mvc.helpers import session

        @staticmethod
        def _start_session(request: Request):
            session_id = session.current_id(request)
            data = session.get(session_id) if session_id else None
            if data is None:
                session_id = session.new()
                data = session.get(session_id)
            return session_id, data["csrf_token"]
    ```

    C'est **votre** code : libre à vous de l'étendre (écriture en session, autres
    helpers…) sans rien attendre du framework.

## Tester dans le navigateur

| URL | Résultat |
|---|---|
| `https://localhost:8000/welcome/csrf` | la page, le champ caché `csrf_token` désormais **rempli** (inspecter la source) |

## À retenir

- Le jeton CSRF **vit dans la session** : sans session active, il est **vide**.
- On garantit une session (`get_session_store().create()`) et on pose son cookie
  avec `set_session_cookie`, sinon le POST serait refusé.
- Le jeton se transmet dans un champ caché `name="csrf_token"` du formulaire.

Au palier suivant, nous traitons un vrai formulaire POST protégé par ce jeton.

[Continuer avec Premier formulaire POST](form-post.md)
