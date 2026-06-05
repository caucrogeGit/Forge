"""Starter Revalidation (step-up) — palier 1 du niveau avancé (welcome-mfa).

Ticket : STARTER-MFA-REVALIDATION-001.

Certaines actions (changer son mot de passe, supprimer son compte) exigent une
**MFA récente**, même déjà connecté : c'est le *step-up*. ``mark_mfa_revalidated``
enregistre une revalidation en session ; ``has_recent_mfa_revalidation`` dit si elle
est encore fraîche. Le décorateur ``require_recent_mfa`` s'appuie sur ces briques.

  ``index``      — `GET  /mfa-revalidation` : affiche si une revalidation est récente.
  ``revalidate`` — `POST /mfa-revalidation` : marque une revalidation maintenant.

Démo **en session** (utilisateur démo). Aucune base de données, aucune clé requise.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.security.session import get_session, get_session_id
from core.sessions.manager import get_session_store

from forge_mvc_mfa import has_recent_mfa_revalidation, mark_mfa_revalidated

_DEMO_USER_ID = 1
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
    response = BaseController.render("mfa_revalidation/index.html", context=context, request=request)
    response.headers["Set-Cookie"] = _COOKIE.format(sid=sid)
    return response


def _is_recent(request) -> bool:
    try:
        return bool(has_recent_mfa_revalidation(request, _DEMO_USER_ID))
    except Exception:
        return False


class MfaRevalidationController(BaseController):
    """Starter pédagogique : exiger une MFA récente avant une action sensible."""

    @staticmethod
    def index(request: Request) -> Response:
        _, sid, _ = _ensure_session(request)
        return _render(request, sid, {
            "csrf_token": BaseController.csrf_token(request),
            "recent": _is_recent(request),
        })

    @staticmethod
    def revalidate(request: Request) -> Response:
        _, sid, _ = _ensure_session(request)
        context = {"csrf_token": BaseController.csrf_token(request)}
        try:
            mark_mfa_revalidated(request, _DEMO_USER_ID)
            context["marked"] = True
        except Exception as exc:
            context["error"] = f"Revalidation impossible : {exc}"
        context["recent"] = _is_recent(request)
        return _render(request, sid, context)
