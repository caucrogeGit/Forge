import re

from core.sessions.keys import SESSION_KEY_AUTHENTICATED, SESSION_KEY_USER, session_get
from core.sessions.manager import get_session_store as _get_store

_SESSION_ID_RE = re.compile(r"^[0-9a-f]{64}$")

SESSION_COOKIE_NAME = "__Host-session_id"

_store = _get_store()

SESSION_DURATION = 3600  # 1 heure en secondes


def create_session() -> str:
    """Crée une nouvelle session et retourne son identifiant."""
    return _store.create()


def get_session(session_id: str) -> dict | None:
    """Retourne les données de la session ou None si inexistante ou expirée."""
    return _store.get(session_id)


def delete_session(session_id: str) -> None:
    """Supprime la session."""
    _store.delete(session_id)


def regenerate_session(old_session_id: str) -> str:
    """Crée un nouveau session_id en conservant les données — protège contre la session fixation."""
    return _store.regenerate(old_session_id)


def authenticate_session(session_id: str, user: dict) -> str | None:
    """
    Marque une session comme authentifiée et y stocke l'utilisateur courant.

    Returns :
        str | None : nouveau session_id après rotation, ou None si session absente
    """
    user_data = {
        "id"    : user["UtilisateurId"],
        "login" : user["Login"],
        "prenom": user.get("Prenom") or "",
        "nom"   : user.get("Nom") or "",
        "email" : user.get("Email") or "",
        "roles" : list(user.get("roles", [])),
    }
    return _store.authenticate(session_id, user_data, SESSION_DURATION)


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
    session_id = get_session_id(request)
    if not session_id:
        return False
    session = _store.get(session_id)
    if session is None:
        return False
    if session_get(session, SESSION_KEY_AUTHENTICATED, False) and session_get(session, SESSION_KEY_USER):
        _store.touch_expiry(session_id, SESSION_DURATION)
        return True
    return False


def get_user(request) -> dict | None:
    """Retourne l'utilisateur courant depuis la session si authentifié."""
    session_id = get_session_id(request)
    if not session_id:
        return None
    session = get_session(session_id)
    if not session or not session_get(session, SESSION_KEY_AUTHENTICATED):
        return None
    return session_get(session, SESSION_KEY_USER)


def user_has_role(request, role: str) -> bool:
    """Retourne True si l'utilisateur courant possède le rôle demandé."""
    user = get_user(request)
    if not user:
        return False
    return role in user.get("roles", [])


def set_flash(session_id: str | None, message: str, level: str = "success") -> None:
    """Stocke un message flash dans la session (affiché une seule fois)."""
    if not session_id:
        return
    _store.set_flash(session_id, message, level)


def get_flash(session_id: str | None) -> dict | None:
    """Retourne et supprime le message flash de la session."""
    if not session_id:
        return None
    return _store.get_flash(session_id)
