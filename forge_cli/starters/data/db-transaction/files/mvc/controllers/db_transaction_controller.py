"""Starter Écritures transactionnelles — dernier palier du niveau avancé.

Ticket : STARTER-DB-TRANSACTION-001.

Certaines opérations doivent être **atomiques** : soit toutes les écritures
réussissent, soit aucune. Forge fournit ``transaction()`` : un bloc
``with transaction() as tx:`` ouvre une transaction explicite et passe ``tx`` aux
helpers DB, qui réutilisent la connexion **sans jamais committer eux-mêmes**. À
la sortie du bloc, Forge committe ; si une exception traverse le bloc, Forge
**annule** (rollback).

  ``index`` — `GET  /db-transaction` : formulaire (deux messages) + liste.
  ``store`` — `POST /db-transaction` : insère les DEUX messages dans une seule
              transaction. Si le second est vide, on lève une erreur APRÈS avoir
              inséré le premier : le rollback annule tout — rien n'est écrit.

Table neutre ``first_sql_messages``.
"""
from core.database.db import fetch_all, insert
from core.database.transaction import transaction
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


INSERT_MESSAGE = "INSERT INTO first_sql_messages (content) VALUES (?)"
SELECT_MESSAGES = "SELECT id, content FROM first_sql_messages ORDER BY id"


class DbTransactionController(BaseController):
    """Starter pédagogique : deux écritures atomiques (commit / rollback)."""

    @staticmethod
    def index(request: Request) -> Response:
        return DbTransactionController._page(request)

    @staticmethod
    def store(request: Request) -> Response:
        first = (request.form("message_a") or "").strip()
        second = (request.form("message_b") or "").strip()
        try:
            with transaction() as tx:
                insert(INSERT_MESSAGE, (first,), tx=tx)
                if not second:
                    # Erreur APRÈS la première insertion : le rollback l'annule.
                    raise ValueError(
                        "Le second message est obligatoire : tout est annulé."
                    )
                insert(INSERT_MESSAGE, (second,), tx=tx)
        except ValueError as exc:
            return DbTransactionController._page(request, error=str(exc))
        return BaseController.redirect("/db-transaction")

    @staticmethod
    def _page(request: Request, error: str | None = None) -> Response:
        context = {
            "messages": fetch_all(SELECT_MESSAGES),
            "csrf_token": BaseController.csrf_token(request),
        }
        if error:
            context["error"] = error
        return BaseController.render(
            "db_transaction/index.html", context=context, request=request
        )
