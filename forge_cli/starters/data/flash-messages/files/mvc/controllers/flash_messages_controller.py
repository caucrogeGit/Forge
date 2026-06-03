"""Starter Messages flash — dernier palier du niveau intermédiaire.

Ticket : STARTER-FLASH-MESSAGES-001.

Un **message flash** confirme une action à la requête **suivante**, puis
disparaît (one-shot). C'est le motif **POST-Redirect-GET** : l'action POST pose
un flash et **redirige** ; la page cible lit le flash (``get_flash``, qui le
supprime) et l'affiche. Combine session (palier précédent), CSRF et redirection.

  ``index``  — `GET /flash-messages` : garantit une session, lit le flash
               éventuel, affiche un bouton d'action (POST + CSRF).
  ``action`` — `POST /flash-messages/action` : pose un flash et redirige vers
               la page (PRG).

Aucune base de données : le store de session par défaut est en mémoire.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.security.session import get_flash, get_session, get_session_id
from core.sessions.manager import get_session_store


SESSION_COOKIE = "session_id={sid}; Path=/; HttpOnly; SameSite=Strict; Secure"


class FlashMessagesController(BaseController):
    """Starter pédagogique : messages flash (POST-Redirect-GET)."""

    @staticmethod
    def index(request: Request) -> Response:
        store = get_session_store()
        session_id = get_session_id(request)
        session = get_session(session_id) if session_id else None
        if not session:
            session_id = store.create()
            session = get_session(session_id)

        flash = get_flash(session_id)  # lecture one-shot : le message disparaît
        response = BaseController.render(
            "flash_messages/index.html",
            context={"flash": flash, "csrf_token": BaseController.csrf_token(request)},
            request=request,
        )
        response.headers["Set-Cookie"] = SESSION_COOKIE.format(sid=session_id)
        return response

    @staticmethod
    def action(request: Request) -> Response:
        BaseController.set_flash(request, "Action effectuée avec succès !")
        return BaseController.redirect("/flash-messages")
