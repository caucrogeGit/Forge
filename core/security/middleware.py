# pyright: strict
from __future__ import annotations

import hmac as _hmac
from typing import TYPE_CHECKING

from core.auth.session import (
    current_user as _current_user,
    get_authenticated_user_id as _get_authenticated_user_id,
    is_authenticated as _is_authenticated,
    logout_user as _logout_user,
)
from core.http.response import Response
from core.http.helpers import error_page as _error_page
from core.security.cookies import clear_session_cookie as _clear_session_cookie
from core.security.session import get_session_id, get_session

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from core.http.request import Request


class AuthMiddleware:
    """
    Vérifie qu'une session authentifiée est présente.
    Retourne une réponse 302 vers login_url si ce n'est pas le cas.

    Avec un ``user_loader`` (ADR-080), le middleware valide l'**existence** du
    sujet : un ``user_id`` en session qui ne pointe plus aucun compte (supprimé,
    réattribué, inactif) est une session orpheline ; elle est fermée (logout +
    purge du cookie) avant la redirection, pour ne pas reboucler. Sans loader, le
    contrôle reste id-based (présence d'un id d'auth), rétrocompatible.

    Usage :
        auth = AuthMiddleware(user_loader=charger_utilisateur)
        denied = auth.check(request)
        if denied:
            return denied
    """

    def __init__(
        self,
        login_url: str = "/login",
        *,
        user_loader: "Callable[[int], Any] | None" = None,
    ) -> None:
        self._login_url = login_url
        self._user_loader = user_loader

    def check(self, request: Request) -> Response | None:
        loader = self._user_loader
        if loader is None:
            # Contrôle id-based (rétrocompat) : un id d'auth est-il en session ?
            if not _is_authenticated(request):
                return Response(302, headers={"Location": self._login_url})
            return None

        # ADR-080 : l'id en session doit pointer un compte existant et actif.
        user_id = _get_authenticated_user_id(request)
        if user_id is not None and _current_user(request, loader) is not None:
            return None

        response = Response(302, headers={"Location": self._login_url})
        if user_id is not None:
            # Session orpheline : id présent mais sujet absent. On la ferme.
            _logout_user(request)
            _clear_session_cookie(response)
        return response


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
            return _error_page("errors/403.html", 403)
        if not _hmac.compare_digest(str(provided), str(expected)):
            return _error_page("errors/403.html", 403)
        return None

    def _extract_token(self, request: Request) -> str | None:
        values = request.body.get(self._field_name)
        token = values[0] if values else None
        if token:
            return token

        header_value = request.headers.get(self._header_name, "")
        return header_value or None
