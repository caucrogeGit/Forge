# Bilan : niveau intermédiaire

Vous venez de construire à la main, palier après palier, un seul et même
mini-projet : le **Carnet de notes**. Cette page récapitule les huit notions
acquises, puis montre l'état final complet du contrôleur et du fichier de routes.

## Les huit notions acquises

- Palier 1 : lire **plusieurs** lignes avec `fetch_all` et les itérer dans une
  vue (`{% for %}`), depuis une table `notes` créée par migration.
- Palier 2 : factoriser l'enveloppe HTML avec `{% extends %}` et `{% block %}`.
- Palier 3 : filtrer la liste avec `request.query` et `WHERE content LIKE ?`
  paramétré.
- Palier 4 : paginer avec `LIMIT ? OFFSET ?` et `COUNT(*)`, en conservant le
  filtre.
- Palier 5 : modifier une ligne avec un formulaire pré-rempli et
  `UPDATE … WHERE id = ?` (POST + CSRF).
- Palier 6 : supprimer avec `POST` + CSRF + `DELETE … WHERE id = ?`, puis
  redirection.
- Palier 7 : confirmer une écriture par un flash one-shot (motif
  POST-Redirect-GET).
- Palier 8 : mémoriser un état serveur entre requêtes avec la session (compteur
  de visites).

## État final de mvc/controllers/note_controller.py

```python
# mvc/controllers/note_controller.py
from core.database.db import execute, fetch_all, fetch_one
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.security.cookies import set_session_cookie
from core.security.session import get_flash, get_session, get_session_id
from core.sessions.manager import get_session_store

PAGE_SIZE = 5
SELECT_BASE = "SELECT id, content FROM notes"
COUNT_BASE = "SELECT COUNT(*) AS total FROM notes"
WHERE_FILTER = " WHERE content LIKE ?"
SELECT_ONE = "SELECT id, content FROM notes WHERE id = ?"
UPDATE_ONE = "UPDATE notes SET content = ? WHERE id = ?"
DELETE_ONE = "DELETE FROM notes WHERE id = ?"


def _page_number(raw: str) -> int:
    try:
        page = int(raw)
    except (TypeError, ValueError):
        return 1
    return page if page >= 1 else 1


class NoteController(BaseController):

    @staticmethod
    def _start_session(request: Request):
        """Garantit une session active et renvoie (session_id, csrf_token)."""
        session_id = get_session_id(request)
        session = get_session(session_id) if session_id else None
        if session is None:
            session_id = get_session_store().create()
            session = get_session(session_id)
        return session_id, session["csrf_token"]

    @staticmethod
    def index(request: Request) -> Response:
        q = request.query("q", default="").strip()
        page = _page_number(request.query("page", default="1"))
        where = WHERE_FILTER if q else ""
        params = (f"%{q}%",) if q else ()
        total = fetch_one(COUNT_BASE + where, params)["total"]
        offset = (page - 1) * PAGE_SIZE
        notes = fetch_all(
            SELECT_BASE + where + " ORDER BY id LIMIT ? OFFSET ?",
            params + (PAGE_SIZE, offset),
        )
        session_id, csrf_token = NoteController._start_session(request)
        flash = get_flash(session_id)
        store = get_session_store()
        session = get_session(session_id)
        visits = int(session.get("visits", 0)) + 1
        store.set(session_id, {"visits": visits})

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
                "flash": flash,
                "visits": visits,
            },
        )
        set_session_cookie(response, session_id)
        return response

    @staticmethod
    def edit(request: Request) -> Response:
        record_id = int(request.route("id"))
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
        record_id = int(request.route("id"))
        content = request.form("content", default="").strip()
        if not content:
            return Response.text("Le contenu est obligatoire.", status=422)
        execute(UPDATE_ONE, (content, record_id))
        return BaseController.redirect("/note", request=request, flash="Note mise à jour.")

    @staticmethod
    def delete(request: Request) -> Response:
        record_id = int(request.route("id"))
        execute(DELETE_ONE, (record_id,))
        return BaseController.redirect("/note", request=request, flash="Note supprimée.")
```

## État final de mvc/routes.py

```python
# mvc/routes.py
from core.http.router import Router
from mvc.controllers.home_controller import HomeController
from mvc.controllers.note_controller import NoteController

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET",  "/", HomeController.index, name="home-index")
    pub.add("GET",  "/note", NoteController.index, name="note-index")
    pub.add("GET",  "/note/edit/{id}", NoteController.edit, name="note-edit")
    pub.add("POST", "/note/update/{id}", NoteController.update, name="note-update")
    pub.add("POST", "/note/delete/{id}", NoteController.delete, name="note-delete")
```

Le projet compte trois vues : le gabarit `note/_layout.html`, la liste
`note/index.html` (recherche, pagination, flash, compteur de visites) et le
formulaire `note/edit.html`.

## Et ensuite

Vous savez construire à la main une petite application liste, recherche,
pagination, édition, suppression, avec gabarits factorisés, état de session et
retour utilisateur. Place au **niveau avancé** : données reliées, écritures
transactionnelles, upload de fichiers et API JSON.

[Niveau avancé : Relations entre tables](../avance/relations.md)
