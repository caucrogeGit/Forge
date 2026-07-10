# pyright: strict
"""Session utilisateur minimale pour Auth/User."""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from core.auth.exceptions import AuthError, InvalidAuthUserError
from core.auth.password import verify_password
from core.auth.user import AuthUser, normalize_auth_user, validate_auth_user_contract
from core.http.response import Response

logger = logging.getLogger(__name__)

AUTH_USER_ID_SESSION_KEY = "_auth_user_id"


def authenticate_user(
    email: str,
    password: str,
    user_loader: Callable[[str], Any],
) -> AuthUser | None:
    """Authentifie un email/mot de passe via un loader applicatif."""
    if not isinstance(email, str) or not email.strip():  # pyright: ignore[reportUnnecessaryIsInstance]
        return None
    if not isinstance(password, str) or not password:  # pyright: ignore[reportUnnecessaryIsInstance]
        return None
    if not callable(user_loader):
        raise AuthError("user_loader doit etre callable")

    try:
        raw_user = user_loader(email.strip())
    except Exception:
        logger.warning(
            "Le user_loader a levé une exception à l'authentification ; traité comme échec d'auth "
            "(distinct d'un mot de passe invalide). Vérifiez le loader applicatif / la base.",
            exc_info=True,
        )
        return None

    if raw_user is None:
        return None

    try:
        user = raw_user if isinstance(raw_user, AuthUser) else normalize_auth_user(raw_user)
    except (InvalidAuthUserError, TypeError, ValueError):
        return None

    if not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def login_user(request: Any, user: AuthUser) -> None:
    """Stocke l'identifiant utilisateur dans la session et le persiste.

    La mutation in-place ne suffit pas : les backends FileSessionStore et
    DbSessionStore (forge-mvc-sessions-db) renvoient une copie désérialisée à chaque `get()`.
    Sans `store.set()`, la connexion serait perdue sur ces backends (seul
    MemorySessionStore renvoie une référence vivante). On persiste donc
    explicitement, comme le font les contrôleurs starters.

    Sécurité (fixation de session) : `login_user` n'effectue PAS la rotation
    de l'identifiant de session. Pour fermer le vecteur de fixation de session,
    l'appelant DOIT, juste après l'authentification réussie, régénérer
    l'identifiant de session et réémettre le cookie correspondant ::

        login_user(request, user)
        nouvel_id = regenerate_session(get_session_id(request))
        set_session_cookie(response, nouvel_id)

    `login_user` ne peut pas s'en charger seul : il n'a pas accès à la réponse
    HTTP, donc ne peut pas réémettre le cookie. Le contrôleur de référence
    `mvc/controllers/auth_controller.py` applique ce flux ; voir aussi
    docs/features/auth.md (section « fixation de session »).
    """
    validate_auth_user_contract(user)
    session = _resolve_request_session(request)
    if session is None:
        raise AuthError("session introuvable")

    session[AUTH_USER_ID_SESSION_KEY] = user.id
    _persist_request_session(request, session)


def logout_user(request: Any) -> None:
    """Retire l'identifiant utilisateur Auth/User de la session et persiste."""
    session = _resolve_request_session(request)
    if session is None:
        return
    session.pop(AUTH_USER_ID_SESSION_KEY, None)
    _persist_request_session(request, session)


def get_authenticated_user_id(request: Any) -> int | None:
    """Retourne l'identifiant utilisateur stocke par login_user ou authenticate_session."""
    session = _resolve_request_session(request)
    if session is None:
        return None

    # Chemin canonique : clé _auth_user_id posée par login_user()
    user_id = session.get(AUTH_USER_ID_SESSION_KEY)
    if isinstance(user_id, int) and not isinstance(user_id, bool) and user_id > 0:
        return user_id

    # Pont de compatibilité : session legacy créée par authenticate_session()
    from core.sessions.keys import SESSION_KEY_AUTHENTICATED, SESSION_KEY_USER, session_get
    if session_get(session, SESSION_KEY_AUTHENTICATED, False):
        legacy_user = session_get(session, SESSION_KEY_USER)
        if isinstance(legacy_user, dict):
            legacy_id = cast("dict[str, Any]", legacy_user).get("id")
            if isinstance(legacy_id, int) and not isinstance(legacy_id, bool) and legacy_id > 0:
                return legacy_id

    return None


def current_user(request: Any, user_loader: Callable[[int], Any]) -> AuthUser | None:
    """Retourne l'utilisateur courant via un loader applicatif."""
    if not callable(user_loader):
        raise AuthError("user_loader doit etre callable")

    user_id = get_authenticated_user_id(request)
    if user_id is None:
        return None

    try:
        raw_user = user_loader(user_id)
    except Exception:
        logger.warning(
            "Le user_loader a levé une exception au chargement de l'utilisateur de session ; "
            "session traitée comme anonyme (distinct d'une session absente).",
            exc_info=True,
        )
        return None

    if raw_user is None:
        return None

    try:
        user = raw_user if isinstance(raw_user, AuthUser) else normalize_auth_user(raw_user)
    except (InvalidAuthUserError, TypeError, ValueError):
        return None

    if not user.is_active:
        return None
    return user


def is_authenticated(request: Any) -> bool:
    """Retourne True si une session Auth/User contient un id utilisateur."""
    return get_authenticated_user_id(request) is not None


def login_required(
    func: Callable[..., Any] | None = None,
    *,
    redirect_to: str | None = None,
) -> Any:
    """Protege une fonction controleur avec la session Auth/User minimale."""

    def decorator(wrapped: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(wrapped)
        def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            if is_authenticated(request):
                return wrapped(request, *args, **kwargs)
            if redirect_to:
                return Response(302, headers={"Location": redirect_to})
            return Response(401, body=b"Authentication required", content_type="text/plain; charset=utf-8")

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


def _resolve_request_session(request: Any) -> dict[str, Any] | None:
    session = getattr(request, "session", None)
    if isinstance(session, dict):
        return cast("dict[str, Any]", session)

    try:
        from core.security.session import get_session, get_session_id

        session_id = get_session_id(request)
        return get_session(session_id) if session_id else None
    except Exception:
        logger.warning(
            "Résolution de la session impossible (exception) ; session ignorée.",
            exc_info=True,
        )
        return None


def _persist_request_session(request: Any, data: dict[str, Any]) -> None:
    """Réécrit la session dans le store pour les backends sans référence vivante.

    Utilise `replace` (remplacement intégral) et non `set` (merge) : `data` est
    l'état complet voulu de la session, donc `replace` persiste aussi bien
    l'ajout d'une clé (login) que son retrait (logout) — `set` ne pourrait pas
    supprimer une clé absente de `data`.

    Sans session_id (pas de cookie), il n'y a rien à persister côté store ;
    la mutation in-place reste valable pour un éventuel `request.session` vivant.
    """
    try:
        from core.security.session import get_session_id
        from core.sessions.manager import get_session_store

        session_id = get_session_id(request)
        if session_id:
            get_session_store().replace(session_id, data)
    except Exception:
        logger.warning(
            "Persistance de la session impossible (exception) ; non bloquant.",
            exc_info=True,
        )
        return
