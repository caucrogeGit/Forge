"""Starter Écrire en base — palier de la progression pédagogique.

Ticket : STARTER-FIRST-SQL-WRITE-001.

Palier-pont entre la **lecture** SQL (palier « Première base SQL ») et le
**CRUD complet**. Deux actions :

  ``index``  — `GET /first-sql-write`, rend un formulaire (jeton CSRF).
  ``submit`` — `POST /first-sql-write`, lit `content`, refuse une valeur
               vide (`422`), sinon insère une ligne dans
               `first_sql_messages` avec `db.insert(...)`.

Réutilise la table `first_sql_messages` créée par la migration du palier
« Première base SQL » — appliquez d'abord cette migration. SQL visible,
aucun ORM, aucune entité JSON.
"""
from core.database.db import insert
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


INSERT_MESSAGE = "INSERT INTO first_sql_messages (content) VALUES (?)"


class FirstSqlWriteController(BaseController):
    """Starter pédagogique : écrire une donnée en base depuis un formulaire."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "first_sql_write/index.html",
            request=request,
            context={"csrf_token": BaseController.csrf_token(request)},
        )

    @staticmethod
    def submit(request: Request) -> Response:
        content = request.form("content", default="").strip()

        if not content:
            return Response.text("Le message est obligatoire", status=422)

        insert(INSERT_MESSAGE, (content,))
        return Response.text(f"Message enregistré : {content}")
