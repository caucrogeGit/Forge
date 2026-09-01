# pyright: strict
"""Session utilisateur minimale pour Auth/User."""

from __future__ import annotations

from core.sessions.keys import SESSION_KEY_AUTH_USER_ID

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from core.auth.audit import (
    AUTH_EVENT_LOGIN_FAILED,
    AUTH_EVENT_LOGIN_SUCCESS,
    AUTH_EVENT_LOGOUT,
)
from core.auth.exceptions import AuthError, InvalidAuthUserError
from core.auth.password import verify_password
from core.auth.user import AuthUser, normalize_auth_user, validate_auth_user_contract
from core.http.response import Response

logger = logging.getLogger(__name__)

#: Alias public historique de `core.sessions.keys.SESSION_KEY_AUTH_USER_ID`.
AUTH_USER_ID_SESSION_KEY = SESSION_KEY_AUTH_USER_ID


def authenticate_user(
    login: str,
    password: str,
    user_loader: Callable[[str], Any],
) -> AuthUser | None:
    """Authentifie un identifiant et un mot de passe via un loader applicatif.

    Le premier paramètre s'appelait `email` alors qu'il reçoit une **identité**,
    laquelle n'est pas nécessairement une adresse depuis l'ADR-089 : une
    application y met légitimement `2TNE1-01`. Le nom disait donc le contraire
    de ce que la valeur porte, et c'est ce genre d'écart qui a produit les deux
    divergences de la CLI, sur la casse et sur la forme.
    """
    if not isinstance(login, str) or not login.strip():  # pyright: ignore[reportUnnecessaryIsInstance]
        return None
    if not isinstance(password, str) or not password:  # pyright: ignore[reportUnnecessaryIsInstance]
        return None
    if not callable(user_loader):
        raise AuthError("user_loader doit etre callable")

    try:
        raw_user = user_loader(login.strip())
    except Exception:
        logger.warning(
            "Le user_loader a levé une exception à l'authentification ; traité comme échec d'auth "
            "(distinct d'un mot de passe invalide). Vérifiez le loader applicatif / la base.",
            exc_info=True,
        )
        _emettre_echec("loader_error")
        return None

    if raw_user is None:
        _emettre_echec("user_not_found")
        return None

    try:
        user = raw_user if isinstance(raw_user, AuthUser) else normalize_auth_user(raw_user)
    except (InvalidAuthUserError, TypeError, ValueError):
        _emettre_echec("invalid_user_row")
        return None

    if not user.is_active:
        _emettre_echec("user_inactive", user_id=user.id)
        return None
    if not verify_password(password, user.password_hash):
        _emettre_echec("bad_password", user_id=user.id)
        return None

    _emettre(AUTH_EVENT_LOGIN_SUCCESS, user_id=user.id)
    return user


# ── Émission des événements d'authentification (ADR-091) ─────────────────────
#
# `authenticate_user` est le SEUL endroit qui sait pourquoi une connexion
# échoue : l'appelant ne reçoit qu'un `None` et ne peut distinguer un
# identifiant inconnu d'un mot de passe faux ou d'un compte désactivé. C'est
# donc ici que l'événement est émis, et non dans le contrôleur engendré, où il
# serait à la fois moins précis et supprimable en silence.
#
# L'ADR-008 reste inchangé : Forge ÉMET vers le logger `forge.auth.audit`, et
# la persistance appartient à l'application. Ce qui manquait n'était pas la
# persistance mais l'émission elle-même, que Forge annonçait sans la faire.


def _emettre(event_type: str, *, user_id: int | None = None, **metadata: Any) -> None:
    """Émet un événement d'audit sans jamais interrompre l'authentification.

    `safe_log_auth_event` avale l'exception, la journalise et incrémente un
    compteur : une table saturée, un disque plein ou un verrou ne doivent
    jamais empêcher quelqu'un d'entrer.
    """
    from core.auth.audit import safe_log_auth_event

    safe_log_auth_event(event_type, user_id=user_id, metadata=metadata or None)


def _emettre_echec(raison: str, *, user_id: int | None = None) -> None:
    """Émet `login.failed` en portant la RAISON, jamais la valeur saisie.

    Ni le mot de passe, ni sa longueur, ni l'identifiant tenté ne sont émis :
    une faute de frappe sur un mot de passe ressemble trop à un mot de passe.
    La raison suffit à une enquête et ne divulgue rien.
    """
    _emettre(AUTH_EVENT_LOGIN_FAILED, user_id=user_id, reason=raison)


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
    """Retire l'identifiant utilisateur Auth/User de la session et persiste.

    Émet `logout` en portant le compte quitté (ADR-091). L'identifiant est lu
    AVANT le retrait, sans quoi l'événement ne dirait pas qui part.
    """
    session = _resolve_request_session(request)
    if session is None:
        return
    quitte = session.get(AUTH_USER_ID_SESSION_KEY)
    session.pop(AUTH_USER_ID_SESSION_KEY, None)
    _persist_request_session(request, session)
    if isinstance(quitte, int):
        _emettre(AUTH_EVENT_LOGOUT, user_id=quitte)


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
    except (InvalidAuthUserError, TypeError, ValueError) as _invalide:
        # La branche du dessus journalise, celle-ci se taisait
        # (`CORE-WSGI-AUTH-GATE-001`). Or les deux situations n'ont pas la même
        # cause : un loader qui lève est un incident, un loader qui rend une
        # ligne incomplète est un **défaut de programmation**, et il produit
        # une boucle de redirection vers `/login` que rien n'explique.
        #
        # Le cas se produit dès qu'un `load_user_by_id` applicatif omet une
        # colonne obligatoire, `password_hash` la première. La session est
        # valide, le compte existe, et l'utilisateur ne peut simplement plus
        # entrer. Le refus reste le bon comportement ; le silence, non.
        logger.warning(
            "Le user_loader a rendu un utilisateur invalide (%s) ; session traitée "
            "comme anonyme. Vérifiez que le loader rend tous les champs "
            "obligatoires d'AuthUser.",
            _invalide,
        )
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
        from core.sessions.access import get_session, get_session_id

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
        from core.sessions.access import get_session_id
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
