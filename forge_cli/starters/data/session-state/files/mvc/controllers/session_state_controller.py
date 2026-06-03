"""Starter Mémoriser un état en session — palier 7 du niveau intermédiaire.

Ticket : STARTER-SESSION-STATE-001.

Une requête HTTP est **sans mémoire** : le serveur oublie tout d'une requête à
l'autre. La **session** permet de mémoriser un état côté serveur, rattaché à
l'utilisateur via un cookie `session_id`. Ce palier compte les visites.

  ``index`` — `GET /session-state` : lit la session (la crée si besoin),
              incrémente un compteur, le ré-enregistre, et pose le cookie
              `session_id` durci sur la réponse.

Aucune base de données : le store de session par défaut est en mémoire.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.security.session import get_session, get_session_id
from core.sessions.manager import get_session_store


SESSION_COOKIE = "session_id={sid}; Path=/; HttpOnly; SameSite=Strict; Secure"


class SessionStateController(BaseController):
    """Starter pédagogique : mémoriser un compteur de visites en session."""

    @staticmethod
    def index(request: Request) -> Response:
        store = get_session_store()
        session_id = get_session_id(request)
        session = get_session(session_id) if session_id else None
        if not session:
            session_id = store.create()
            session = get_session(session_id)

        visits = int(session.get("visits", 0)) + 1
        store.set(session_id, {"visits": visits})

        response = BaseController.render(
            "session_state/index.html",
            context={"visits": visits},
            request=request,
        )
        response.headers["Set-Cookie"] = SESSION_COOKIE.format(sid=session_id)
        return response
