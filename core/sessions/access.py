# pyright: strict
"""Lecture de session depuis la requête (CORE-AUTH-SECURITY-LAYERING-001).

`get_session_id` (cookie → identifiant) et `get_session` (identifiant → données)
vivent ici, dans la couche basse `core.sessions`, et non plus dans
`core.security.session`. Motif : `core.auth.session` a besoin de lire la session,
et l'importait de `core.security.session` par un import différé pour éviter un
cycle (`core.security` importe `core.auth` au niveau module). En logeant la
lecture sous `core.sessions` — qui ne dépend ni de `core.security` ni de
`core.auth` — auth et security en dépendent tous deux sans cycle.

`core.security.session` ré-exporte ces symboles : le chemin d'import public
`core.security.session` (utilisé par du code généré) reste inchangé.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from core.sessions.manager import get_session_store as _get_store

if TYPE_CHECKING:
    from core.http.request import Request

# Nom du cookie de session Forge (`__Host-` : lié à l'hôte, HTTPS, Path=/).
SESSION_COOKIE_NAME = "__Host-session_id"

# Un identifiant de session valide est 64 caractères hexadécimaux.
_SESSION_ID_RE = re.compile(r"^[0-9a-f]{64}$")


def get_session_id(request: Request) -> str | None:
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
            if _SESSION_ID_RE.fullmatch(sid):
                return sid
            return None
    return None


def get_session(session_id: str | None) -> dict[str, Any] | None:
    """Retourne les données de la session ou None si inexistante ou expirée.

    Le store est résolu à chaque appel via `get_session_store()` pour que
    `forge.configure(session_store=...)` soit pris en compte même si ce module
    est importé avant la configuration.
    """
    if session_id is None:
        return None
    return _get_store().get(session_id)
