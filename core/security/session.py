import secrets
import threading
import time

# Stockage en mémoire : session_id → données.
# Adapté au développement, à la pédagogie et aux petites applications
# mono-processus. Limites assumées en V1 : sessions perdues au redémarrage,
# pas de partage entre workers, pas de scaling horizontal.
# RLock (reentrant) : une même thread peut acquérir le verrou plusieurs fois
# sans se bloquer elle-même (creer_session appelle _nettoyer_sessions).
_sessions: dict = {}
_lock = threading.RLock()

DUREE_SESSION = 3600  # 1 heure en secondes


def creer_session() -> str:
    """Crée une nouvelle session et retourne son identifiant."""
    session_id = secrets.token_hex(32)
    with _lock:
        _sessions[session_id] = {
            "authentifie": False,
            "utilisateur": None,
            "csrf_token" : secrets.token_hex(16),
            "expire_a"   : time.time() + DUREE_SESSION
        }
        _nettoyer_sessions()
    return session_id


def get_session(session_id: str) -> dict | None:
    """Retourne les données de la session ou None si inexistante ou expirée."""
    with _lock:
        session = _sessions.get(session_id)
        if session is None:
            return None
        if time.time() > session["expire_a"]:
            _sessions.pop(session_id, None)
            return None
        return session


def supprimer_session(session_id: str) -> None:
    """Supprime la session."""
    with _lock:
        _sessions.pop(session_id, None)


def regenerer_session(ancien_session_id: str) -> str:
    """Crée un nouveau session_id en conservant les données — protège contre la session fixation."""
    nouveau_id = secrets.token_hex(32)
    with _lock:
        ancien = _sessions.pop(ancien_session_id, {})
        _sessions[nouveau_id] = {
            **ancien,
            "expire_a": time.time() + DUREE_SESSION
        }
    return nouveau_id


def authentifier_session(session_id: str, utilisateur: dict) -> str | None:
    """
    Marque une session comme authentifiée et y stocke l'utilisateur courant.

    Returns :
        str | None : nouveau session_id après rotation, ou None si session absente
    """
    nouveau_id = secrets.token_hex(32)
    with _lock:
        ancien = _sessions.pop(session_id, None)
        if ancien is None:
            return None
        _sessions[nouveau_id] = {
            **ancien,
            "authentifie": True,
            "utilisateur": {
                "id"    : utilisateur["UtilisateurId"],
                "login" : utilisateur["Login"],
                "prenom": utilisateur.get("Prenom") or "",
                "nom"   : utilisateur.get("Nom") or "",
                "email" : utilisateur.get("Email") or "",
                "roles" : list(utilisateur.get("roles", [])),
            },
            "csrf_token": secrets.token_hex(16),
            "expire_a"  : time.time() + DUREE_SESSION,
        }
    return nouveau_id


def get_session_id(request) -> str | None:
    """Extrait le session_id depuis le cookie de la requête."""
    cookie = request.headers.get("Cookie", "")
    for part in cookie.split(";"):
        part = part.strip()
        if part.startswith("session_id="):
            return part[len("session_id="):]
    return None


def est_authentifie(request) -> bool:
    """
    Retourne True si la requête provient d'un utilisateur authentifié.
    Repousse l'expiration de la session à chaque requête valide.
    """
    session_id = get_session_id(request)
    if not session_id:
        return False
    with _lock:
        _nettoyer_sessions()
        session = _sessions.get(session_id)
        if session is None or time.time() > session["expire_a"]:
            _sessions.pop(session_id, None)
            return False
        if session.get("authentifie", False) and session.get("utilisateur"):
            session["expire_a"] = time.time() + DUREE_SESSION
            return True
    return False


def get_utilisateur(request) -> dict | None:
    """Retourne l'utilisateur courant depuis la session si authentifié."""
    session_id = get_session_id(request)
    if not session_id:
        return None
    session = get_session(session_id)
    if not session or not session.get("authentifie"):
        return None
    return session.get("utilisateur")


def utilisateur_a_role(request, role: str) -> bool:
    """Retourne True si l'utilisateur courant possède le rôle demandé."""
    utilisateur = get_utilisateur(request)
    if not utilisateur:
        return False
    return role in utilisateur.get("roles", [])


def set_flash(session_id: str | None, message: str, level: str = "success") -> None:
    """Stocke un message flash dans la session (affiché une seule fois)."""
    if not session_id:
        return
    with _lock:
        session = _sessions.get(session_id)
        if session:
            session["flash"] = {"message": message, "level": level}


def get_flash(session_id: str | None) -> dict | None:
    """Retourne et supprime le message flash de la session."""
    if not session_id:
        return None
    with _lock:
        session = _sessions.get(session_id)
        if session:
            return session.pop("flash", None)
    return None


def _nettoyer_sessions() -> None:
    """Supprime les sessions expirées — doit être appelée avec _lock déjà acquis."""
    maintenant = time.time()
    expirees   = [sid for sid, s in _sessions.items() if maintenant > s["expire_a"]]
    for sid in expirees:
        del _sessions[sid]
