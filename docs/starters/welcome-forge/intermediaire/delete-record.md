# Supprimer un enregistrement

**Objectif**{ .intro-label } : supprimer une note via une action **destructive sécurisée**.

**Ce que vous allez apprendre :**{ .intro-label } une suppression ne se fait **jamais** par un simple lien `GET` : elle passe par un **POST protégé par CSRF** et `core.database.db.execute("DELETE … WHERE id = ?")`, puis une redirection vers la liste (motif POST-Redirect-GET).

Le Carnet de notes sait lister et modifier.

Nous complétons par la suppression.
La liste affiche déjà un lien « éditer » par note ; nous y ajoutons un bouton « supprimer ».
Comme la liste portera désormais un formulaire, `index` doit lui fournir un **jeton CSRF**.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [La protection CSRF](../../../reference/http/csrf.md) | pourquoi chaque bouton de suppression porte un jeton |
    | [L'objet Response](../../../core-http/response.md) | la redirection après écriture (POST-Redirect-GET) |
    | [La session HTTP](../../../reference/http/session.md) | où vit le jeton fourni à la liste |

??? note "Contrôleurs"
    Ajoutez la requête et la méthode `delete` dans `mvc/controllers/note_controller.py`, et faites garantir la session par `index`, car la liste porte désormais des formulaires de suppression (le jeton CSRF doit donc être non vide) :

    ```python
    DELETE_ONE = "DELETE FROM notes WHERE id = ?"


    class NoteController(BaseController):

        @staticmethod
        def index(request: Request) -> Response:
            # … lecture de q, page, notes inchangée …
            session_id, csrf_token = NoteController._start_session(request)
            response = BaseController.render(
                "note/index.html",
                request=request,
                context={
                    "notes": notes,
                    "q": q,
                    "page": page,
                    "has_prev": page > 1,
                    "has_next": page * PAGE_SIZE < total,
                    "csrf_token": csrf_token,
                },
            )
            set_session_cookie(response, session_id)
            return response

        @staticmethod
        def delete(request: Request) -> Response:
            record_id = int(request.route("id", default="0"))
            execute(DELETE_ONE, (record_id,))
            return BaseController.redirect("/note")
    ```

    | Élément | Rôle |
    |---|---|
    | `delete` en `POST` | Une action qui modifie l'état n'est **jamais** un `GET` (un lien ou un robot ne doivent pas pouvoir supprimer). |
    | `execute(DELETE_ONE, (record_id,))` | L'`id` est un **paramètre lié**. |
    | `redirect("/note")` | Après l'écriture, le navigateur recharge l'état réel par un `GET` (motif POST-Redirect-GET). |

??? note "Vues"
    Dans `mvc/views/note/index.html`, ajoutez le bouton de suppression à côté du lien « éditer » de chaque note :

    ```html
    <li>#{{ note.id }} : {{ note.content }}
        <a href="/note/edit/{{ note.id }}">éditer</a>
        <form method="post" action="/note/delete/{{ note.id }}" style="display:inline">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <button type="submit">supprimer</button>
        </form>
    </li>
    ```

    Chaque ligne porte son **propre mini-formulaire** `POST` vers `/note/delete/{id}` avec le **jeton CSRF**.

??? note "Routes"
    Déclarez la route de suppression dans `mvc/routes.py` :

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
        public.add("POST", "/note/delete/{id}", NoteController.delete, name="note-delete")
    ```

??? note "Tests"
    | URL | Résultat |
    |---|---|
    | `https://localhost:8000/note` | la liste, avec « éditer » et « supprimer » par note |
    | Cliquer « supprimer » | la note disparaît, la liste se recharge |

??? note "À retenir"
    - Supprimer, c'est `POST` plus CSRF plus `DELETE … WHERE id = ?` paramétré.
    - Une action qui change l'état n'est **jamais** un `GET`.
    - Après l'écriture, on **redirige** vers la liste (POST-Redirect-GET).

Au palier suivant, nous confirmons ces actions par un message flash.

[Continuer avec Messages flash](flash-messages.md)
