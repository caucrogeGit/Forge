# pyright: strict
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from core.http.helpers import html as _html
from core.http.response import Response
from core.security.middleware import CsrfMiddleware as _CsrfMiddleware
# is_authenticated : API canonique (core.auth.session), avec pont legacy intégré.
# L'ancienne core.security.session.is_authenticated émet un DeprecationWarning à
# chaque appel ; l'importer ici déclenchait un warning par requête protégée.
from core.auth.session import is_authenticated
from core.security.session import user_has_role

if TYPE_CHECKING:
    from core.http.request import Request
    from core.http.router import Handler

_csrf_check = _CsrfMiddleware()


def require_auth(func: Handler) -> Handler:
    """
    Redirige vers /login si l'utilisateur n'est pas authentifié.

    Usage :
        @staticmethod
        @require_auth
        def list(request): ...
    """
    def wrapper(request: Request) -> Response:
        if not is_authenticated(request):
            return Response(302, headers={"Location": "/login"})
        return func(request)
    return wrapper


def require_csrf(func: Handler) -> Handler:
    """
    Retourne une 403 si le token CSRF du formulaire ne correspond pas à la session.
    Délègue à CsrfMiddleware pour garantir une comparaison constant-time.
    À placer après @require_auth pour garantir qu'une session existe.

    Usage :
        @staticmethod
        @require_auth
        @require_csrf
        def add(request): ...
    """
    def wrapper(request: Request) -> Response:
        denied = _csrf_check.check(request)
        if denied is not None:
            return denied
        return func(request)
    return wrapper


def require_role(role: str) -> "Callable[[Handler], Handler]":
    """
    Redirige vers /login si non authentifié, retourne 403 si rôle absent.

    Usage :
        @staticmethod
        @require_auth
        @require_role("admin")
        def dashboard(request): ...
    """
    def decorator(func: Handler) -> Handler:
        def wrapper(request: Request) -> Response:
            if not is_authenticated(request):
                return Response(302, headers={"Location": "/login"})
            if not user_has_role(request, role):
                return _html("errors/403.html", 403)
            return func(request)
        return wrapper
    return decorator
