"""Starter Paginer une liste — palier 3 du niveau intermédiaire.

Ticket : STARTER-PAGINATION-001.

N'afficher qu'une **tranche** des lignes à la fois. Le numéro de page (lu avec
``request.param``) pilote un ``LIMIT ? OFFSET ?`` paramétré ; un ``COUNT(*)``
donne le total pour savoir s'il reste une page suivante.

  ``index`` — `GET /pagination?page=N`. Lit ``PAGE_SIZE`` lignes à partir de
              l'offset ``(N-1) * PAGE_SIZE`` et calcule les liens précédent /
              suivant.

Aucune écriture. Table neutre ``first_sql_messages`` peuplée par la migration.
"""
from core.database.db import fetch_all, fetch_one
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


PAGE_SIZE = 3
SELECT_PAGE = (
    "SELECT id, content FROM first_sql_messages "
    "ORDER BY id LIMIT ? OFFSET ?"
)
COUNT_ALL = "SELECT COUNT(*) AS total FROM first_sql_messages"


def _page_number(raw: str) -> int:
    """Convertit le paramètre `page` en entier >= 1, tolérant aux valeurs invalides."""
    try:
        page = int(raw)
    except (TypeError, ValueError):
        return 1
    return page if page >= 1 else 1


class PaginationController(BaseController):
    """Starter pédagogique : paginer une liste avec LIMIT / OFFSET."""

    @staticmethod
    def index(request: Request) -> Response:
        page = _page_number(request.query("page", default="1"))
        offset = (page - 1) * PAGE_SIZE
        messages = fetch_all(SELECT_PAGE, (PAGE_SIZE, offset))
        total = fetch_one(COUNT_ALL)["total"]
        return BaseController.render(
            "pagination/index.html",
            context={
                "messages": messages,
                "page": page,
                "has_prev": page > 1,
                "has_next": page * PAGE_SIZE < total,
            },
            request=request,
        )
