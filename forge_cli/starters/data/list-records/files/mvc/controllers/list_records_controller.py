"""Starter Lister des enregistrements — palier 1 du niveau intermédiaire.

Ticket : STARTER-LIST-RECORDS-001.

Premier palier intermédiaire : lire **plusieurs** lignes et les afficher
dans une vue. Le palier débutant Première base SQL lisait UNE ligne avec
``fetch_one`` ; ici on lit toute la table avec ``core.database.db.fetch_all``
(qui retourne une **liste** de dictionnaires) et on l'itère dans la vue avec
une boucle Jinja ``{% for %}``.

  ``index`` — `GET /list-records`, exécute `SELECT id, content FROM
              first_sql_messages ORDER BY id` via ``fetch_all`` et rend la vue
              ``list_records/index.html`` avec la liste ``messages``.

Aucun formulaire, aucune écriture, aucune entité JSON. La table neutre
``first_sql_messages`` (issue du palier Première base SQL) est créée et
peuplée de plusieurs lignes par la migration livrée avec ce starter.
"""
from core.database.db import fetch_all
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


SELECT_ALL_MESSAGES = "SELECT id, content FROM first_sql_messages ORDER BY id"


class ListRecordsController(BaseController):
    """Starter pédagogique : lister plusieurs lignes SQL dans une vue."""

    @staticmethod
    def index(request: Request) -> Response:
        messages = fetch_all(SELECT_ALL_MESSAGES)
        return BaseController.render(
            "list_records/index.html",
            context={"messages": messages},
            request=request,
        )
