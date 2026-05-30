"""Starter First CRUD — capstone des fondamentaux.

Ticket : STARTER-PREMIER-CRUD-001.

CRUD complet et minimal sur la table `first_sql_messages` (la même que les
paliers « Première base SQL » et « Écrire en base »), avec du SQL visible
et aucun ORM. Cinq actions :

  ``index``   — `GET  /messages`              liste + formulaire de création.
  ``create``  — `POST /messages`              insère une ligne (`db.insert`).
  ``edit``    — `GET  /messages/{id}/edit`    formulaire de modification.
  ``update``  — `POST /messages/{id}`         met à jour (`db.execute` UPDATE).
  ``destroy`` — `POST /messages/{id}/delete`  supprime (`db.execute` DELETE).

Réutilise la table `first_sql_messages` créée par la migration du palier
« Première base SQL » — appliquez d'abord cette migration. Forge ne fournit
pas de redirection : après une écriture, on ré-affiche la liste à jour en
relisant la base (`index`).
"""
from core.database.db import execute, fetch_all, fetch_one, insert
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


SELECT_ALL = "SELECT id, content FROM first_sql_messages ORDER BY id DESC"
SELECT_ONE = "SELECT id, content FROM first_sql_messages WHERE id = ?"
INSERT_ONE = "INSERT INTO first_sql_messages (content) VALUES (?)"
UPDATE_ONE = "UPDATE first_sql_messages SET content = ? WHERE id = ?"
DELETE_ONE = "DELETE FROM first_sql_messages WHERE id = ?"


class MessagesController(BaseController):
    """Starter pédagogique : CRUD complet à SQL visible."""

    @staticmethod
    def index(request: Request) -> Response:
        messages = fetch_all(SELECT_ALL)
        return BaseController.render(
            "messages/index.html",
            request=request,
            context={
                "messages": messages,
                "csrf_token": BaseController.csrf_token(request),
            },
        )

    @staticmethod
    def create(request: Request) -> Response:
        content = request.form("content", default="").strip()
        if not content:
            return Response.text("Le message est obligatoire", status=422)

        insert(INSERT_ONE, (content,))
        return MessagesController.index(request)

    @staticmethod
    def edit(request: Request) -> Response:
        message = fetch_one(SELECT_ONE, (request.route_param("id"),))
        if message is None:
            return Response.text("Message introuvable", status=404)

        return BaseController.render(
            "messages/edit.html",
            request=request,
            context={
                "message": message,
                "csrf_token": BaseController.csrf_token(request),
            },
        )

    @staticmethod
    def update(request: Request) -> Response:
        content = request.form("content", default="").strip()
        if not content:
            return Response.text("Le message est obligatoire", status=422)

        execute(UPDATE_ONE, (content, request.route_param("id")))
        return MessagesController.index(request)

    @staticmethod
    def destroy(request: Request) -> Response:
        execute(DELETE_ONE, (request.route_param("id"),))
        return MessagesController.index(request)
