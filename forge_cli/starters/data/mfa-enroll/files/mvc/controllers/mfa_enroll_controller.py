"""Starter Enrôler un facteur TOTP — palier 1 du niveau intermédiaire (welcome-mfa).

Ticket : STARTER-MFA-ENROLL-001.

L'enrôlement en deux temps : ``create_totp_factor`` crée un facteur **pending**
(son secret est déjà **chiffré au repos** via ``FORGE_MFA_SECRET_KEY``) ;
``confirm_totp_factor`` l'**active** après qu'on a vérifié un premier code — preuve
que l'utilisateur a bien enregistré le secret.

  ``index``   — `GET  /mfa-enroll` : crée un facteur pending, affiche le secret/URI
                une fois, et garde le facteur **en session** (la persistance réelle
                est le job de l'application).
  ``confirm`` — `POST /mfa-enroll` : confirme le facteur avec un code.

Démo **sans base** (facteur gardé en session). Nécessite ``FORGE_MFA_SECRET_KEY``.
"""
import dataclasses

from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.security.session import get_session, get_session_id
from core.sessions.manager import get_session_store

from forge_mvc_mfa import AuthMfaFactor, confirm_totp_factor, create_totp_factor

_DEMO_USER_ID = 1
_SESSION_KEY = "mfa_enroll_pending_factor"
_COOKIE = "session_id={sid}; Path=/; HttpOnly; SameSite=Strict; Secure"


def _ensure_session(request):
    store = get_session_store()
    sid = get_session_id(request)
    session = get_session(sid) if sid else None
    if not session:
        sid = store.create()
        session = get_session(sid)
    return store, sid, session


def _render(request, sid, context):
    response = BaseController.render("mfa_enroll/index.html", context=context, request=request)
    response.headers["Set-Cookie"] = _COOKIE.format(sid=sid)
    return response


class MfaEnrollController(BaseController):
    """Starter pédagogique : enrôler et confirmer un facteur TOTP."""

    @staticmethod
    def index(request: Request) -> Response:
        store, sid, session = _ensure_session(request)
        context = {"csrf_token": BaseController.csrf_token(request)}
        try:
            setup = create_totp_factor(_DEMO_USER_ID, account_name="demo@forge.example")
        except Exception as exc:
            context["error"] = f"Enrôlement impossible (clé MFA ?) : {exc}"
            return _render(request, sid, context)
        store.set(sid, {**session, _SESSION_KEY: dataclasses.asdict(setup.factor)})
        context["secret"] = setup.secret
        context["uri"] = setup.provisioning_uri
        return _render(request, sid, context)

    @staticmethod
    def confirm(request: Request) -> Response:
        store, sid, session = _ensure_session(request)
        context = {"csrf_token": BaseController.csrf_token(request)}
        data = (session or {}).get(_SESSION_KEY)
        code = (request.form("code") or "").strip()
        if not data:
            context["error"] = "Démarrez d'abord l'enrôlement (rechargez la page)."
            return _render(request, sid, context)
        active = confirm_totp_factor(AuthMfaFactor(**data), code)
        if active is None:
            context["error"] = "Code invalide — facteur non confirmé."
        else:
            context["confirmed"] = True
            store.set(sid, {k: v for k, v in session.items() if k != _SESSION_KEY})
        return _render(request, sid, context)
