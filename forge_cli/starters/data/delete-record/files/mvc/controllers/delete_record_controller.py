"""Starter Supprimer un enregistrement — palier 6 du niveau intermédiaire.

Ticket : STARTER-DELETE-RECORD-001.

Dernière opération du CRUD à la main : **supprimer** une ligne. La suppression
est une action destructive : elle passe par un **POST protégé par CSRF** (jamais
un simple lien `GET`) et `core.database.db.execute("DELETE … WHERE id = ?")`.
Après écriture, on **relit la base et on ré-affiche** la liste.

  ``index``  — `GET /delete-record` : liste avec un bouton « supprimer » par
               ligne (mini-formulaire POST + jeton CSRF).
  ``delete`` — `POST /delete-record/{id}` : supprime puis ré-affiche la liste.
"""
from core.database.db import execute, fetch_all
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


SELECT_ALL = "SELECT id, content FROM first_sql_messages ORDER BY id"
DELETE_ONE = "DELETE FROM first_sql_messages WHERE id = ?"


class DeleteRecordController(BaseController):
    """Starter pédagogique : supprimer une ligne avec DELETE."""

    @staticmethod
    def index(request: Request) -> Response:
        messages = fetch_all(SELECT_ALL)
        return BaseController.render(
            "delete_record/index.html",
            context={"messages": messages, "csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def delete(request: Request) -> Response:
        record_id = int(request.route_param("id"))
        execute(DELETE_ONE, (record_id,))
        # On relit la base et on ré-affiche la liste à jour.
        messages = fetch_all(SELECT_ALL)
        return BaseController.render(
            "delete_record/index.html",
            context={
                "messages": messages,
                "csrf_token": BaseController.csrf_token(request),
                "deleted": True,
            },
            request=request,
        )
