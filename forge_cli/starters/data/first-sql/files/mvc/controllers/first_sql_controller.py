"""Starter Première base SQL — palier 8 de la progression pédagogique.

Ticket : STARTER-FIRST-SQL-001.

Le contrôleur expose une route qui apprend à lire UNE donnée depuis
MariaDB avec du SQL visible — pas de CRUD, pas d'ORM, pas d'entité
JSON. La requête SQL reste une chaîne lisible définie au niveau du
module.

  ``index`` — `GET /first-sql`, exécute `SELECT content FROM
              first_sql_messages ORDER BY id LIMIT 1`
              via `core.database.db.fetch_one` et retourne
              `Response.text("Message depuis la base : {content}")`.

Aucun formulaire, aucune entité, aucune relation, aucune validation
serveur. La table est créée par la migration livrée avec ce starter
(`mvc/migrations/20260527120000_create_first_sql_messages.sql`).
"""
from core.database.db import fetch_one
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


SELECT_FIRST_MESSAGE = "SELECT content FROM first_sql_messages ORDER BY id LIMIT 1"


class FirstSqlController(BaseController):
    """Starter pédagogique : lire une donnée SQL."""

    @staticmethod
    def index(request: Request) -> Response:
        row = fetch_one(SELECT_FIRST_MESSAGE)
        message = row["content"] if row else "(aucun message)"
        return Response.text(f"Message depuis la base : {message}")
