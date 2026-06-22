# Modifier un enregistrement

**Objectif**{ .intro-label } : éditer une note existante via un formulaire pré-rempli.

**Ce que vous allez apprendre :**{ .intro-label } la première **écriture** du niveau. Le formulaire est chargé avec la valeur courante (`fetch_one`), puis l'enregistrement passe par `core.database.db.execute("UPDATE … WHERE id = ?")`, en POST **protégé par CSRF**.

Jusqu'ici, le Carnet de notes est en **lecture seule** : lister, rechercher, paginer.

Nous ajoutons la première écriture.
C'est un nouveau besoin (un formulaire, une route POST, du CSRF), donc deux nouvelles méthodes sur `NoteController` et **deux nouvelles routes**.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [La protection CSRF](../../../reference/http/csrf.md) | pourquoi le POST porte un jeton, et le `403` sinon |
    | [La session HTTP](../../../reference/http/session.md) | où vit le jeton garanti par `_start_session` |
    | [L'objet Request](../../../core-http/request.md) | `route(...)` pour l'`id`, `form(...)` pour la saisie |

??? note "Contrôleurs"
    Complétez les imports et ajoutez le helper de session, les deux requêtes et les deux méthodes dans `mvc/controllers/note_controller.py`.
    Le jeton CSRF vit dans la session : sans session active il serait vide et le POST serait refusé.
    Le helper `_start_session` garantit une session (comme au palier CSRF du niveau débutant) :

    ```python
    from core.database.db import execute, fetch_all, fetch_one
    from core.security.cookies import set_session_cookie
    from core.security.session import get_session, get_session_id
    from core.sessions.manager import get_session_store

    SELECT_ONE = "SELECT id, content FROM notes WHERE id = ?"
    UPDATE_ONE = "UPDATE notes SET content = ? WHERE id = ?"


    class NoteController(BaseController):

        # … index(...) inchangé …

        @staticmethod
        def _start_session(request: Request):
            """Garantit une session active et renvoie (session_id, csrf_token)."""
            session_id = get_session_id(request)
            if session_id is None or get_session(session_id) is None:
                session_id = get_session_store().create()
            session = get_session(session_id) or {}
            return session_id, session.get("csrf_token", "")

        @staticmethod
        def edit(request: Request) -> Response:
            record_id = int(request.route("id", default="0"))
            note = fetch_one(SELECT_ONE, (record_id,))
            if note is None:
                return Response.text("Note introuvable.", status=404)
            session_id, csrf_token = NoteController._start_session(request)
            response = BaseController.render(
                "note/edit.html",
                request=request,
                context={"note": note, "csrf_token": csrf_token},
            )
            set_session_cookie(response, session_id)
            return response

        @staticmethod
        def update(request: Request) -> Response:
            record_id = int(request.route("id", default="0"))
            content = request.form("content", default="").strip()
            if not content:
                return Response.text("Le contenu est obligatoire.", status=422)
            execute(UPDATE_ONE, (content, record_id))
            return BaseController.render(
                "note/edit.html",
                request=request,
                context={
                    "note": {"id": record_id, "content": content},
                    "csrf_token": BaseController.csrf_token(request),
                    "updated": True,
                },
            )
    ```

    | Élément | Rôle |
    |---|---|
    | `edit` | **Pré-remplit** le formulaire : lit la valeur courante avec `fetch_one`, renvoie un `404` si l'`id` est inconnu. |
    | `update` | Valide d'abord (refus `422` si vide), puis `execute(UPDATE_ONE, …)` : l'`id` et le contenu sont des **paramètres liés**. |
    | `request.route("id")` | L'`id` vient de la **route**, pas de la *query string*. |

??? note "Vues"
    Créez la vue `mvc/views/note/edit.html` :

    ```html
    <!-- mvc/views/note/edit.html -->
    {% extends "note/_layout.html" %}

    {% block title %}Modifier la note #{{ note.id }}{% endblock %}

    {% block content %}
    <h1>Modifier la note #{{ note.id }}</h1>

    {% if updated %}<p><strong>Note mise à jour.</strong></p>{% endif %}

    <form method="post" action="/note/update/{{ note.id }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <input type="text" name="content" value="{{ note.content }}">
        <button type="submit">Enregistrer</button>
    </form>

    <p><a href="/note">Retour à la liste</a></p>
    {% endblock %}
    ```

    Ajoutez aussi un lien « éditer » sur chaque note de la liste, dans `mvc/views/note/index.html` :

    ```html
    <li>#{{ note.id }} : {{ note.content }}
        <a href="/note/edit/{{ note.id }}">éditer</a></li>
    ```

    Le `<form>` est en `method="post"` et embarque le **jeton CSRF** : toute écriture est protégée.

??? note "Routes"
    Déclarez les deux routes dans `mvc/routes.py` :

    ```python
    # mvc/routes.py
    from core.http.router import Router
    from mvc.controllers.home_controller import HomeController
    from mvc.controllers.note_controller import NoteController

    router = Router()

    with router.group("", public=True) as public:
        public.add("GET",  "/", HomeController.index, name="home-index")
        public.add("GET",  "/note", NoteController.index, name="note-index")
        public.add("GET",  "/note/edit/{id}", NoteController.edit, name="note-edit")
        public.add("POST", "/note/update/{id}", NoteController.update, name="note-update")
    ```

??? note "Tests"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/note` | la liste, avec un lien « éditer » par note |
    | Éditer une note, changer le texte, Enregistrer | « Note mise à jour. » |
    | Soumettre vide | `Le contenu est obligatoire.` (statut `422`) |

??? note "À retenir"
    - Modifier, c'est pré-remplir (`fetch_one`) plus `UPDATE … WHERE id = ?` paramétré.
    - L'`id` vient de la **route** (`request.route("id")`).
    - Toute écriture est en `POST` **avec CSRF**.

??? tip "Astuces"
    Les appels session (`_start_session`, `set_session_cookie`) reviennent à chaque écriture protégée.
    Si vous voulez simplifier, **vous** pouvez les regrouper dans une **classe façade** de votre application, sous `mvc/helpers/`.

    Forge ne l'ajoute pas au framework : le noyau reste minimal et explicite, l'ergonomie est à votre main.
    Un parcours dédié vous montre comment construire ces façades pas à pas (`Session`, `Cookies`, `Flash`) : [Construire vos façades helper](../../welcome-helpers/installation.md).

Au palier suivant, nous ajoutons la suppression d'une note.

[Continuer avec Supprimer un enregistrement](delete-record.md)
