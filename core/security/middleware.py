from core.http.response import Response
from core.http.helpers import html as _html
from core.security.session import est_authentifie, get_session_id, get_session


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

    def __init__(self, login_url: str = "/login"):
        self._login_url = login_url

    def check(self, request) -> Response | None:
        if not est_authentifie(request):
            return Response(302, headers={"Location": self._login_url})
        return None


class CsrfMiddleware:
    """
    Vérifie le token CSRF d'une requête unsafe déjà déclarée comme protégée.

    Le middleware ne décide pas quelles routes sont concernées : cette décision
    reste portée par RouteEntry.csrf et par la méthode HTTP.
    """

    def __init__(self, field_name: str = "csrf_token", header_name: str = "X-CSRF-Token"):
        self._field_name = field_name
        self._header_name = header_name

    def check(self, request) -> Response | None:
        session_id = get_session_id(request)
        session = get_session(session_id) if session_id else None
        expected = session.get("csrf_token") if session else None
        provided = self._extract_token(request)

        if not expected or provided != expected:
            return _html("errors/403.html", 403)
        return None

    def _extract_token(self, request) -> str | None:
        value = request.body.get(self._field_name, [None])
        if isinstance(value, list):
            token = value[0] if value else None
        else:
            token = value

        if token:
            return token

        header_value = request.headers.get(self._header_name, "")
        return header_value or None
