"""Contrôleur de challenge MFA à la connexion."""
from __future__ import annotations

from typing import Any, Callable

from core.auth.audit import (
    AUTH_EVENT_MFA_CHALLENGE_FAILED,
    AUTH_EVENT_MFA_CHALLENGE_SUCCESS,
    safe_log_auth_event,
)
try:
    from forge_mvc_mfa import (
        get_mfa_challenge_user_id,
        has_pending_mfa_challenge,
        verify_mfa_challenge,
    )
    _MFA_AVAILABLE = True
except ImportError:
    _MFA_AVAILABLE = False

    def get_mfa_challenge_user_id(_request):  # type: ignore[override]
        return None

    def has_pending_mfa_challenge(_request):  # type: ignore[override]
        return False

    def verify_mfa_challenge(_request, _code, *, factors=None):  # type: ignore[override]
        return None

from core.forge import get as _cfg
from core.mvc.controller.base_controller import BaseController
from core.security.cookies import set_session_cookie
from core.security.session import authenticate_session, get_session, get_session_id


class MfaChallengeController(BaseController):
    """Routes GET /login/mfa et POST /login/mfa pour le challenge MFA."""

    @staticmethod
    def _resolve_session(request: Any) -> tuple[str | None, dict | None]:
        """Retourne (session_id, session) depuis request.session ou via cookie."""
        session = getattr(request, "session", None)
        if isinstance(session, dict):
            return None, session
        session_id = get_session_id(request)
        return session_id, get_session(session_id) if session_id else None

    @staticmethod
    def _mfa_unavailable_redirect() -> Any:
        return BaseController.redirect("/login")

    @staticmethod
    def form(request: Any) -> Any:
        """GET /login/mfa — affiche le formulaire de code MFA si challenge actif."""
        if not _MFA_AVAILABLE:
            return MfaChallengeController._mfa_unavailable_redirect()
        _, session = MfaChallengeController._resolve_session(request)
        if not has_pending_mfa_challenge(request):
            return BaseController.redirect("/login")
        return BaseController.render("auth/mfa_challenge.html", base=None, context={
            "csrf_token": session.get("csrf_token", "") if session else "",
            "app_name": _cfg("app_name"),
            "erreur": "",
        })

    @staticmethod
    def verify(
        request: Any,
        *,
        _load_factors: Callable | None = None,
        _finalize_login: Callable | None = None,
    ) -> Any:
        """POST /login/mfa — vérifie le code MFA et finalise la connexion.

        _load_factors(user_id) et _finalize_login(user_id, session_id, session, request)
        peuvent être injectés pour les tests sans base de données réelle.
        """
        if not _MFA_AVAILABLE:
            return MfaChallengeController._mfa_unavailable_redirect()
        session_id, session = MfaChallengeController._resolve_session(request)

        if not session:
            return BaseController.render("errors/403.html", 403, base=None)

        if not has_pending_mfa_challenge(request):
            return BaseController.redirect("/login")

        user_id = get_mfa_challenge_user_id(request)
        if user_id is None:
            return BaseController.redirect("/login")

        code = request.body.get("code", [""])[0]

        if _load_factors is not None:
            factors = _load_factors(user_id)
        else:
            from mvc.models.mfa_model import get_active_mfa_factors
            factors = get_active_mfa_factors(user_id)

        result = verify_mfa_challenge(request, code, factors=factors)
        if result is None:
            safe_log_auth_event(
                AUTH_EVENT_MFA_CHALLENGE_FAILED,
                user_id=user_id,
                ip_address=getattr(request, "ip", None),
            )
            return BaseController.render("auth/mfa_challenge.html", base=None, context={
                "csrf_token": session.get("csrf_token", ""),
                "app_name": _cfg("app_name"),
                "erreur": "Code MFA invalide.",
            })

        safe_log_auth_event(
            AUTH_EVENT_MFA_CHALLENGE_SUCCESS,
            user_id=user_id,
            ip_address=getattr(request, "ip", None),
        )
        if _finalize_login is not None:
            return _finalize_login(user_id, session_id, session, request)

        return _default_finalize(user_id, session_id)


def _default_finalize(user_id: int, session_id: str | None) -> Any:
    """Finalise la connexion après validation MFA (chemin production)."""
    from mvc.models.mfa_model import get_user_by_id
    utilisateur = get_user_by_id(user_id)
    if utilisateur is None:
        return BaseController.render("errors/403.html", 403, base=None)
    if session_id is None:
        return BaseController.render("errors/403.html", 403, base=None)
    nouveau_id = authenticate_session(session_id, utilisateur)
    if not nouveau_id:
        return BaseController.render("errors/403.html", 403, base=None)
    from core.http.response import Response
    response = Response(302, headers={"Location": "/"})
    set_session_cookie(response, nouveau_id)
    return response
