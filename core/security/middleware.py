# pyright: strict
from __future__ import annotations

import hmac as _hmac
from typing import TYPE_CHECKING

from core.auth.session import is_authenticated as _is_authenticated
from core.http.response import Response
from core.http.helpers import html as _html
from core.security.session import get_session_id, get_session

if TYPE_CHECKING:
    from core.http.request import Request


class AuthMiddleware:
    """
    Vérifie qu'une session authentifiée est présente.
    Retourne une réponse 302 vers login_url si ce n'est pas le cas.

    Usage :
        auth = AuthMiddleware()
        denied = auth.check(request)
        if denied:
            return denied
    """

    def __init__(self, login_url: str = "/login") -> None:
        self._login_url = login_url

    def check(self, request: Request) -> Response | None:
        if not _is_authenticated(request):
            return Response(302, headers={"Location": self._login_url})
        return None


class CsrfMiddleware:
    """
    Vérifie le token CSRF d'une requête unsafe déjà déclarée comme protégée.

    Le middleware ne décide pas quelles routes sont concernées : cette décision
    reste portée par RouteEntry.csrf et par la méthode HTTP.
    """

    def __init__(self, field_name: str = "csrf_token", header_name: str = "X-CSRF-Token") -> None:
        self._field_name = field_name
        self._header_name = header_name

    def check(self, request: Request) -> Response | None:
        session_id = get_session_id(request)
        session = get_session(session_id) if session_id else None
        expected = session.get("csrf_token") if session else None
        provided = self._extract_token(request)

        if not expected or not provided:
            return _html("errors/403.html", 403)
        if not _hmac.compare_digest(str(provided), str(expected)):
            return _html("errors/403.html", 403)
        return None

    def _extract_token(self, request: Request) -> str | None:
        values = request.body.get(self._field_name)
        token = values[0] if values else None
        if token:
            return token

        header_value = request.headers.get(self._header_name, "")
        return header_value or None
