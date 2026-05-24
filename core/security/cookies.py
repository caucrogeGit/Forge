"""core/security/cookies.py — Helpers de cookies de session Forge.

Ticket : SECURITY-SESSION-COOKIE-HELPER-001.

Centralise la construction du header `Set-Cookie` pour la session Forge afin
qu'un seul endroit applique les règles de sécurité minimales :

  - HttpOnly        (toujours)
  - SameSite=Strict (par défaut — surchargeable)
  - Path=/          (par défaut, obligatoire pour `__Host-`)
  - Secure          (par défaut, obligatoire pour `__Host-` et `SameSite=None`)
  - pas de Domain   (incompatible avec le préfixe `__Host-`)

La migration des appels existants (`mvc/controllers/auth_controller.py`,
`mvc/controllers/mfa_challenge_controller.py`, starters) est traitée par
`SECURITY-SESSION-COOKIE-STARTERS-001` — ce module fournit seulement la
nouvelle API.
"""
from __future__ import annotations

from core.security.session import SESSION_COOKIE_NAME

_VALID_SAME_SITE = ("Strict", "Lax", "None")


def _validate(cookie_name: str, secure: bool, same_site: str, path: str) -> None:
    if same_site not in _VALID_SAME_SITE:
        raise ValueError(
            f"SameSite invalide : {same_site!r}. "
            f"Valeurs acceptées : {_VALID_SAME_SITE}."
        )
    if same_site == "None" and not secure:
        raise ValueError("SameSite=None exige Secure=True (RFC 6265bis).")
    if cookie_name.startswith("__Host-"):
        if not secure:
            raise ValueError(
                f"Le préfixe `__Host-` ({cookie_name}) exige Secure=True."
            )
        if path != "/":
            raise ValueError(
                f"Le préfixe `__Host-` ({cookie_name}) exige Path='/' "
                f"(reçu : {path!r})."
            )


def _build_cookie(
    cookie_name: str,
    value: str,
    *,
    secure: bool,
    same_site: str,
    path: str,
    max_age: int | None,
) -> str:
    parts = [f"{cookie_name}={value}", f"Path={path}", "HttpOnly", f"SameSite={same_site}"]
    if secure:
        parts.append("Secure")
    if max_age is not None:
        parts.append(f"Max-Age={int(max_age)}")
    return "; ".join(parts)


def set_session_cookie(
    response,
    session_id: str,
    *,
    secure: bool = True,
    same_site: str = "Strict",
    path: str = "/",
    max_age: int | None = None,
    cookie_name: str = SESSION_COOKIE_NAME,
) -> None:
    """Écrit `response.headers["Set-Cookie"]` pour la session Forge.

    Args:
        response: objet `core.http.Response` (ou compatible — doit exposer
            un `.headers` dict mutable).
        session_id: identifiant de session à poser dans le cookie.
        secure: pose l'attribut `Secure`. Imposé pour `__Host-*` et
            `SameSite=None`.
        same_site: `"Strict"`, `"Lax"` ou `"None"`. Toute autre valeur lève
            `ValueError`.
        path: chemin du cookie. Doit rester `/` pour `__Host-*`.
        max_age: si fourni, ajoute `Max-Age=<n>` (utiliser `0` pour
            suppression).
        cookie_name: nom du cookie. Par défaut `__Host-session_id`.

    Raises:
        ValueError: pour toute combinaison qui violerait les règles
            `__Host-` ou `SameSite=None`.
    """
    _validate(cookie_name, secure, same_site, path)
    response.headers["Set-Cookie"] = _build_cookie(
        cookie_name,
        session_id,
        secure=secure,
        same_site=same_site,
        path=path,
        max_age=max_age,
    )


def clear_session_cookie(
    response,
    *,
    secure: bool = True,
    same_site: str = "Strict",
    path: str = "/",
    cookie_name: str = SESSION_COOKIE_NAME,
) -> None:
    """Invalide le cookie de session (utilisé au logout).

    Équivaut à `set_session_cookie(response, "", max_age=0, ...)` mais
    explicite l'intention côté appelant.
    """
    set_session_cookie(
        response,
        "",
        secure=secure,
        same_site=same_site,
        path=path,
        max_age=0,
        cookie_name=cookie_name,
    )
