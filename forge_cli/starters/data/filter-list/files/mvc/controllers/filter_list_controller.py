"""Starter Rechercher / filtrer une liste — palier 2 du niveau intermédiaire.

Ticket : STARTER-FILTER-LIST-001.

Combine deux notions déjà vues — les **paramètres d'URL** (`request.param`) et
le **SQL visible** — pour filtrer une liste. Le mot-clé saisi pilote une clause
``WHERE content LIKE ?`` **paramétrée** (jamais concaténée).

  ``index`` — `GET /filter-list?q=<mot>`. Sans `q`, liste tout ; avec `q`,
              filtre via ``SELECT … WHERE content LIKE ?`` (motif ``%q%``).

Aucune écriture. La table neutre ``first_sql_messages`` est peuplée par la
migration livrée avec ce starter.
"""
from core.database.db import fetch_all
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


SELECT_ALL = "SELECT id, content FROM first_sql_messages ORDER BY id"
SELECT_FILTERED = (
    "SELECT id, content FROM first_sql_messages "
    "WHERE content LIKE ? ORDER BY id"
)


class FilterListController(BaseController):
    """Starter pédagogique : filtrer une liste avec un WHERE paramétré."""

    @staticmethod
    def index(request: Request) -> Response:
        query = request.query("q", default="").strip()
        if query:
            messages = fetch_all(SELECT_FILTERED, (f"%{query}%",))
        else:
            messages = fetch_all(SELECT_ALL)
        return BaseController.render(
            "filter_list/index.html",
            context={"messages": messages, "q": query},
            request=request,
        )
