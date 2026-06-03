"""Starter Modifier un enregistrement — palier 5 du niveau intermédiaire.

Ticket : STARTER-UPDATE-RECORD-001.

Complète le CRUD à la main : après *créer* (insert, niveau débutant) et *lire*,
on apprend à **modifier** une ligne existante. Le formulaire est **pré-rempli**
avec la valeur courante (``fetch_one``) ; l'enregistrement passe par
``core.database.db.execute("UPDATE … WHERE id = ?")``, en POST protégé par CSRF.

Conformément aux autres starters, après écriture on **relit la base et on
ré-affiche** (dans une vraie application on ferait un POST-Redirect-GET).

  ``index``  — `GET /update-record` : liste avec un lien « éditer » par ligne.
  ``edit``   — `GET /update-record/{id}/edit` : formulaire pré-rempli.
  ``update`` — `POST /update-record/{id}` : enregistre, puis ré-affiche.
"""
from core.database.db import execute, fetch_all, fetch_one
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


SELECT_ALL = "SELECT id, content FROM first_sql_messages ORDER BY id"
SELECT_ONE = "SELECT id, content FROM first_sql_messages WHERE id = ?"
UPDATE_ONE = "UPDATE first_sql_messages SET content = ? WHERE id = ?"


class UpdateRecordController(BaseController):
    """Starter pédagogique : modifier une ligne avec UPDATE."""

    @staticmethod
    def index(request: Request) -> Response:
        messages = fetch_all(SELECT_ALL)
        return BaseController.render(
            "update_record/index.html",
            context={"messages": messages},
            request=request,
        )

    @staticmethod
    def edit(request: Request) -> Response:
        record_id = int(request.route_param("id"))
        message = fetch_one(SELECT_ONE, (record_id,))
        if message is None:
            return Response.text("Enregistrement introuvable.", status=404)
        return BaseController.render(
            "update_record/edit.html",
            context={"message": message, "csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def update(request: Request) -> Response:
        record_id = int(request.route_param("id"))
        content = request.form("content", default="").strip()
        if not content:
            return Response.text("Le contenu est obligatoire.", status=422)
        execute(UPDATE_ONE, (content, record_id))
        # On relit la base et on ré-affiche le formulaire avec la valeur à jour.
        message = fetch_one(SELECT_ONE, (record_id,))
        return BaseController.render(
            "update_record/edit.html",
            context={
                "message": message,
                "csrf_token": BaseController.csrf_token(request),
                "updated": True,
            },
            request=request,
        )
