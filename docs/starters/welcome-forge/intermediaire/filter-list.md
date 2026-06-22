# Rechercher / filtrer une liste

**Objectif**{ .intro-label } : filtrer la liste selon un mot-clé saisi par l'utilisateur.

**Ce que vous allez apprendre :**{ .intro-label } combiner un **paramètre d'URL** (`request.query`) et le **SQL visible** pour construire une recherche. Le mot-clé pilote une clause `WHERE content LIKE ?` **paramétrée**, jamais concaténée.

`NoteController.index` lit toute la table avec `SELECT_ALL`.

Nous allons le faire évoluer pour qu'il lise un mot-clé dans l'URL et filtre la liste quand il est présent.
La route `/note` ne change pas : la recherche passe par la *query string* (`?q=…`).

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [L'objet Request](../../../core-http/references/request.md) | l'accesseur `query(...)` qui lit le mot-clé |

??? note "Contrôleurs"
    Faites évoluer `mvc/controllers/note_controller.py` : ajoutez la requête filtrée et lisez le mot-clé dans `index`.

    ```python
    SELECT_ALL = "SELECT id, content FROM notes ORDER BY id"
    SELECT_FILTERED = (
        "SELECT id, content FROM notes "
        "WHERE content LIKE ? ORDER BY id"
    )


    class NoteController(BaseController):

        @staticmethod
        def index(request: Request) -> Response:
            q = request.query("q", default="").strip()
            if q:
                notes = fetch_all(SELECT_FILTERED, (f"%{q}%",))
            else:
                notes = fetch_all(SELECT_ALL)
            return BaseController.render(
                "note/index.html",
                request=request,
                context={"notes": notes, "q": q},
            )
    ```

    | Élément | Rôle |
    |---|---|
    | `request.query("q", default="")` | Lit le mot-clé dans la *query string* (`?q=…`), vide par défaut. |
    | `fetch_all(SELECT_FILTERED, (f"%{q}%",))` | Le `?` est lié à la valeur côté pilote SQL, **jamais** inséré dans la chaîne : c'est la protection contre l'injection SQL. |

??? note "Vues"
    Ajoutez le champ de recherche dans le bloc `content` de `mvc/views/note/index.html`, juste avant la liste :

    ```html
    {% block content %}
    <h1>Mes notes</h1>

    <form method="get" action="/note">
        <input type="text" name="q" value="{{ q }}" placeholder="Rechercher…">
        <button type="submit">Rechercher</button>
    </form>

    {% if notes %}
    <ul>
        {% for note in notes %}
        <li>#{{ note.id }} : {{ note.content }}</li>
        {% endfor %}
    </ul>
    {% else %}
    <p>Aucune note ne correspond.</p>
    {% endif %}
    {% endblock %}
    ```

    Le formulaire est en `method="get"` : la recherche se reflète dans l'URL (`?q=…`), partageable et rechargeable.
    Pas de `POST`, donc **pas de CSRF** ici (le CSRF protège les écritures, que nous verrons plus loin).

??? note "Routes"
    Inchangé : la recherche réutilise la route `/note` via la *query string*.

    ```python
    # mvc/routes.py
    from core.http.router import Router
    from mvc.controllers.home_controller import HomeController
    from mvc.controllers.note_controller import NoteController

    router = Router()

    with router.group("", public=True) as public:
        public.add("GET", "/", HomeController.index, name="home-index")
        public.add("GET", "/note", NoteController.index, name="note-index")
    ```

??? note "Tests"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/note` | la liste complète |
    | Saisir `Première` puis Rechercher | seules les notes contenant « Première » |

??? note "À retenir"
    - Une recherche, c'est un paramètre d'URL plus une clause SQL **paramétrée**.
    - `LIKE ?` avec `("%mot%",)` : le motif est une **valeur liée**, pas une concaténation.
    - Un formulaire de recherche est en `GET` (idempotent, partageable).

Au palier suivant, nous paginons la liste pour n'en afficher qu'une tranche.

[Continuer avec Paginer une liste](pagination.md)
