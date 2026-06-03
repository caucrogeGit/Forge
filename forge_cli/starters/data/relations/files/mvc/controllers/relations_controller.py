"""Starter Relations entre tables — palier 1 du niveau avancé.

Ticket : STARTER-RELATIONS-001.

Une vraie application relie ses données. Ici, deux tables sont liées par une
**clé étrangère** : un ``article`` appartient à une ``categorie``
(``articles.category_id`` → ``categories.id``). La lecture combine les deux avec
une **jointure SQL** ``JOIN`` visible — pas d'ORM, pas de magie.

  ``index`` — `GET /relations` : ``SELECT … FROM articles JOIN categories …``
              via ``core.database.db.fetch_all``, affiche chaque article avec le
              nom de sa catégorie.

Aucune écriture. Les deux tables sont créées et peuplées par la migration.
"""
from core.database.db import fetch_all
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


SELECT_ARTICLES_WITH_CATEGORY = (
    "SELECT a.id, a.title, c.name AS category "
    "FROM articles a "
    "JOIN categories c ON c.id = a.category_id "
    "ORDER BY a.id"
)


class RelationsController(BaseController):
    """Starter pédagogique : lire des données reliées avec un JOIN."""

    @staticmethod
    def index(request: Request) -> Response:
        articles = fetch_all(SELECT_ARTICLES_WITH_CATEGORY)
        return BaseController.render(
            "relations/index.html",
            context={"articles": articles},
            request=request,
        )
