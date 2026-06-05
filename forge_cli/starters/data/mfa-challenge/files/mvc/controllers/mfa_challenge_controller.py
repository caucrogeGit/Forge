"""Starter Challenge de connexion — palier 2 du niveau intermédiaire (welcome-mfa).

Ticket : STARTER-MFA-CHALLENGE-001.

Le **second facteur à la connexion** : après l'authentification primaire (mot de
passe), ``start_mfa_challenge`` ouvre un challenge **temporaire en session** (sans
connecter l'utilisateur) ; ``verify_mfa_challenge`` confronte le code (TOTP ou code
de récupération) au challenge, avec un nombre de tentatives limité.

  ``index``  — `GET  /mfa-challenge` : prépare un facteur démo, ouvre le challenge
               en session et affiche le secret + un formulaire de code.
  ``verify`` — `POST /mfa-challenge` : vérifie le code contre le challenge.

Démo **en session** (utilisateur démo, facteur en session). Dans une vraie
application, le challenge suit le login et les facteurs viennent de la base.
Nécessite ``FORGE_MFA_SECRET_KEY``.
"""
import dataclasses

from core.auth.user import AuthUser
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.security.session import get_session, get_session_id
from core.sessions.manager import get_session_store

from forge_mvc_mfa import (
    MFA_STATUS_ACTIVE,
    AuthMfaFactor,
    create_totp_factor,
    start_mfa_challenge,
    verify_mfa_challenge,
)

_DEMO_USER = AuthUser(id=1, email="demo@forge.example", password_hash="(démo)", is_active=True)
_SESSION_KEY = "mfa_challenge_factor"
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
    response = BaseController.render("mfa_challenge/index.html", context=context, request=request)
    response.headers["Set-Cookie"] = _COOKIE.format(sid=sid)
    return response


class MfaChallengeController(BaseController):
    """Starter pédagogique : ouvrir et vérifier un challenge MFA de connexion."""

    @staticmethod
    def index(request: Request) -> Response:
        store, sid, session = _ensure_session(request)
        context = {"csrf_token": BaseController.csrf_token(request)}
        try:
            setup = create_totp_factor(_DEMO_USER.id, account_name=_DEMO_USER.email)
            factor_data = dataclasses.asdict(setup.factor)
            factor_data["status"] = MFA_STATUS_ACTIVE
            store.set(sid, {**session, _SESSION_KEY: factor_data})
            start_mfa_challenge(request, _DEMO_USER)
            context["secret"] = setup.secret
        except Exception as exc:
            context["error"] = f"Challenge indisponible (clé MFA / session ?) : {exc}"
        return _render(request, sid, context)

    @staticmethod
    def verify(request: Request) -> Response:
        store, sid, session = _ensure_session(request)
        context = {"csrf_token": BaseController.csrf_token(request)}
        data = (session or {}).get(_SESSION_KEY)
        code = (request.form("code") or "").strip()
        if not data:
            context["error"] = "Ouvrez d'abord le challenge (rechargez la page)."
            return _render(request, sid, context)
        try:
            result = verify_mfa_challenge(request, code, [AuthMfaFactor(**data)])
        except Exception as exc:
            context["error"] = f"Vérification impossible : {exc}"
            return _render(request, sid, context)
        if result is None:
            context["error"] = "Code invalide ou challenge expiré."
        else:
            context["verified"] = result.method
        return _render(request, sid, context)
