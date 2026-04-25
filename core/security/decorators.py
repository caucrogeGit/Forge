from core.http.helpers import html as _html
from core.http.response import Response
from core.security.session import (
    est_authentifie,
    get_session_id,
    get_session,
    utilisateur_a_role,
)


def require_auth(func):
    """
    Redirige vers /login si l'utilisateur n'est pas authentifié.

    Usage :
        @staticmethod
        @require_auth
        def list(request): ...
    """
    def wrapper(request):
        if not est_authentifie(request):
            return Response(302, headers={"Location": "/login"})
        return func(request)
    return wrapper


def require_csrf(func):
    """
    Retourne une 403 si le token CSRF du formulaire ne correspond pas à la session.
    À placer après @require_auth pour garantir qu'une session existe.

    Usage :
        @staticmethod
        @require_auth
        @require_csrf
        def add(request): ...
    """
    def wrapper(request):
        session_id    = get_session_id(request)
        session       = get_session(session_id)
        token_form    = request.body.get("csrf_token", [None])[0]
        token_session = session.get("csrf_token") if session else None
        if token_form != token_session:
            return _html("errors/403.html", 403)
        return func(request)
    return wrapper


def require_role(role):
    """
    Redirige vers /login si non authentifié, retourne 403 si rôle absent.

    Usage :
        @staticmethod
        @require_auth
        @require_role("admin")
        def dashboard(request): ...
    """
    def decorator(func):
        def wrapper(request):
            if not est_authentifie(request):
                return Response(302, headers={"Location": "/login"})
            if not utilisateur_a_role(request, role):
                return _html("errors/403.html", 403)
            return func(request)
        return wrapper
    return decorator
