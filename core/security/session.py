import re
import warnings

from core.sessions.keys import SESSION_KEY_AUTHENTICATED, SESSION_KEY_USER, session_get
from core.sessions.manager import get_session_store as _get_store

_SESSION_ID_RE = re.compile(r"^[0-9a-f]{64}$")

SESSION_COOKIE_NAME = "__Host-session_id"

# Le store est résolu à chaque appel via _get_store() pour que forge.configure(session_store=...)
# soit pris en compte même si ce module est importé avant la configuration.

SESSION_DURATION = 3600  # 1 heure en secondes


def create_session() -> str:
    """Crée une nouvelle session et retourne son identifiant."""
    warnings.warn(
        "core.security.session.create_session() is deprecated; "
        "use core.sessions.manager.get_session_store().create() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _get_store().create()


def get_session(session_id: str) -> dict | None:
    """Retourne les données de la session ou None si inexistante ou expirée."""
    return _get_store().get(session_id)


def delete_session(session_id: str) -> None:
    """Supprime la session."""
    _get_store().delete(session_id)


def regenerate_session(old_session_id: str) -> str:
    """Crée un nouveau session_id en conservant les données — protège contre la session fixation."""
    return _get_store().regenerate(old_session_id)


def _normalize_legacy_user(user: dict) -> dict:
    """Normalise un dict utilisateur quelconque en structure interne générique.

    Priorité des clés en entrée : génériques EN > legacy FR > legacy PascalCase.
    Sortie : noms canoniques anglais (ADR-003) — `first_name`, `last_name`.
    Les clés legacy `prenom`/`nom` sont conservées en alias de sortie pour
    compatibilité avec les starters historiques (`carnet-contacts`,
    `suivi-comportement-eleves`) qui les consomment encore. À retirer dans
    Forge 2.0 (cf CORE-SESSION-DEDOMAIN-001).

    Cette fonction reste utilisée uniquement par `authenticate_session()`,
    elle-même dépréciée au profit de `core.auth.session.login_user()`.
    """
    first = user.get("first_name") or user.get("prenom") or user.get("Prenom") or ""
    last = user.get("last_name") or user.get("nom") or user.get("Nom") or ""
    return {
        "id"        : user.get("id") or user.get("user_id") or user.get("UtilisateurId"),
        "login"     : (
            user.get("login") or user.get("username")
            or user.get("Login") or user.get("email") or user.get("Email") or ""
        ),
        "first_name": first,
        "last_name" : last,
        # Alias legacy — à supprimer dans Forge 2.0.
        "prenom"    : first,
        "nom"       : last,
        "email"     : user.get("email") or user.get("Email") or "",
        "roles"     : list(user.get("roles", [])),
    }


def authenticate_session(session_id: str, user: dict) -> str | None:
    """
    Marque une session comme authentifiée et y stocke l'utilisateur courant.

    Returns :
        str | None : nouveau session_id après rotation, ou None si session absente
    """
    warnings.warn(
        "core.security.session.authenticate_session() is deprecated; "
        "use core.auth.session.login_user(request, user) with AuthUser instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    user_data = _normalize_legacy_user(user)
    return _get_store().authenticate(session_id, user_data, SESSION_DURATION)


def get_session_id(request) -> str | None:
    """Extrait et valide l'identifiant de session depuis le cookie de la requête.

    Retourne None si le cookie est absent ou si le format est invalide
    (attendu : 64 caractères hexadécimaux).
    """
    prefix = SESSION_COOKIE_NAME + "="
    cookie = request.headers.get("Cookie", "")
    for part in cookie.split(";"):
        part = part.strip()
        if part.startswith(prefix):
            sid = part[len(prefix):]
            if _SESSION_ID_RE.match(sid):
                return sid
            return None
    return None


def is_authenticated(request) -> bool:
    """
    Retourne True si la requête provient d'un utilisateur authentifié.
    Repousse l'expiration de la session à chaque requête valide.
    """
    warnings.warn(
        "core.security.session.is_authenticated() is deprecated; "
        "use core.auth.session.is_authenticated(request) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    session_id = get_session_id(request)
    if not session_id:
        return False
    session = _get_store().get(session_id)
    if session is None:
        return False

    # Chemin legacy : authenticated=True + user={...}
    if session_get(session, SESSION_KEY_AUTHENTICATED, False) and session_get(session, SESSION_KEY_USER):
        _get_store().touch_expiry(session_id, SESSION_DURATION)
        return True

    # Pont de compatibilité : session canonique créée par login_user()
    _CANONICAL_KEY = "_auth_user_id"  # core.auth.session.AUTH_USER_ID_SESSION_KEY
    user_id = session.get(_CANONICAL_KEY)
    if isinstance(user_id, int) and not isinstance(user_id, bool) and user_id > 0:
        _get_store().touch_expiry(session_id, SESSION_DURATION)
        return True

    return False


def get_user(request) -> dict | None:
    """Retourne l'utilisateur courant depuis la session si authentifié."""
    warnings.warn(
        "core.security.session.get_user() is deprecated; "
        "use core.auth.session.current_user(request, user_loader) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    session_id = get_session_id(request)
    if not session_id:
        return None
    session = get_session(session_id)
    if not session or not session_get(session, SESSION_KEY_AUTHENTICATED):
        return None
    return session_get(session, SESSION_KEY_USER)


def user_has_role(request, role: str) -> bool:
    """Retourne True si l'utilisateur courant possède le rôle demandé."""
    session_id = get_session_id(request)
    if not session_id:
        return False
    session = _get_store().get(session_id)
    if not session or not session_get(session, SESSION_KEY_AUTHENTICATED):
        return False
    user = session_get(session, SESSION_KEY_USER)
    if not user:
        return False
    return role in user.get("roles", [])


def set_flash(session_id: str | None, message: str, level: str = "success") -> None:
    """Stocke un message flash dans la session (affiché une seule fois)."""
    if not session_id:
        return
    _get_store().set_flash(session_id, message, level)


def get_flash(session_id: str | None) -> dict | None:
    """Retourne et supprime le message flash de la session."""
    if not session_id:
        return None
    return _get_store().get_flash(session_id)
