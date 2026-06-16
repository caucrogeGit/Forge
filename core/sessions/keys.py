# pyright: strict
"""Cles de session canoniques (anglais, ADR-003) et helper de lecture.

Les noms legacy (francais) sont acceptes en lecture pour ne pas invalider
les sessions creees avant Forge 3.0.1 (migration livree en
SESSIONS-LANG-ALIGN-001). Ils seront retires en Forge 4.0.
"""
from __future__ import annotations

from typing import Any

SESSION_KEY_AUTHENTICATED = "authenticated"
SESSION_KEY_USER = "user"
SESSION_KEY_EXPIRES_AT = "expires_at"

_LEGACY = {
    SESSION_KEY_AUTHENTICATED: "authentifie",
    SESSION_KEY_USER: "utilisateur",
}


def session_get(session: dict[str, Any], key: str, default: Any = None) -> Any:
    """Lit une valeur de session avec fallback sur le nom legacy francais."""
    if key in session:
        return session[key]
    legacy = _LEGACY.get(key)
    if legacy is not None and legacy in session:
        return session[legacy]
    return default
