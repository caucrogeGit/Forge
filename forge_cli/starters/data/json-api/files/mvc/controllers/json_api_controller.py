"""Starter API JSON protégée — palier 4 du niveau avancé.

Ticket : STARTER-JSON-API-001.

Une API expose des données à des clients (front JavaScript, script, autre
service). Ici, la route renvoie du JSON via ``Response.json`` — mais seulement
si la requête présente un **jeton Bearer** valide dans l'en-tête
``Authorization``. Sans jeton valide, elle répond ``401`` en JSON. C'est le motif
d'authentification le plus courant pour une API.

  ``index`` — `GET /json-api` : vérifie l'en-tête ``Authorization: Bearer …`` ;
              si le jeton correspond, renvoie les messages en JSON, sinon ``401``.

Le jeton est ici une constante de démonstration ; une vraie application le
stockerait de façon sûre et le ferait tourner.
"""
from core.database.db import fetch_all
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


# Jeton de démonstration. Dans une vraie application : secret, non versionné,
# renouvelable.
API_TOKEN = "forge-demo-token"

SELECT_MESSAGES = "SELECT id, content FROM first_sql_messages ORDER BY id"


class JsonApiController(BaseController):
    """Starter pédagogique : exposer une API JSON protégée par jeton Bearer."""

    @staticmethod
    def index(request: Request) -> Response:
        authorization = request.header("Authorization") or ""
        if authorization != f"Bearer {API_TOKEN}":
            return Response.json(
                {"error": "Jeton manquant ou invalide."}, status=401
            )
        messages = fetch_all(SELECT_MESSAGES)
        return Response.json({"messages": messages})
