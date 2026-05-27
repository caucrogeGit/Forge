"""Réponse HTTP — `core.http.response`.

`Response` est volontairement minimal : pas de helpers métier, pas de
sérialisation cachée. La classe applique aussi la convention
API-INSPECTABLE-OBJECTS-CONVENTION-001 (constructeurs nommés, `.data` sûr).
"""

from __future__ import annotations

import json as _json
from typing import Any


_TEXT_CONTENT_TYPE = "text/plain; charset=utf-8"
_HTML_CONTENT_TYPE = "text/html; charset=utf-8"
_JSON_CONTENT_TYPE = "application/json; charset=utf-8"


# Headers à masquer dans `response.data` (cf. API-INSPECTABLE-OBJECTS-
# CONVENTION-001). Tout cookie posé par `Set-Cookie` contient typiquement
# un token de session — on n'affiche jamais la valeur, seuls les noms via
# la propriété `cookies`.
_SENSITIVE_RESPONSE_HEADERS: frozenset[str] = frozenset({
    "set-cookie",
    "authorization",
})


def _is_sensitive_response_header(name: str) -> bool:
    return str(name).lower() in _SENSITIVE_RESPONSE_HEADERS


class Response:
    """Encapsule une réponse HTTP à envoyer au navigateur.

    Attributs publics :
        status       (int)   : code HTTP — 200, 403, 404…
        content_type (str)   : type MIME — text/html, text/css…
        body         (bytes) : contenu à envoyer (`str` converti en UTF-8).
        headers      (dict)  : en-têtes additionnels.

    Convention d'inspection (API-INSPECTABLE-OBJECTS-CONVENTION-001) :
        - `Response.text(...)`, `Response.html(...)`, `Response.json(...)`
          construisent une réponse avec le bon `Content-Type` ;
        - `Response.debug(obj)` rend une page HTML lisible en
          `APP_ENV=dev` et refuse en `APP_ENV=prod` ;
        - `response.data` retourne une vue publique masquant les valeurs
          sensibles (`Set-Cookie`, `Authorization`) ;
        - `response.cookies` retourne la liste des **noms** de cookies
          posés (jamais les valeurs).
    """

    def __init__(self, status=200, body=b"", content_type=_HTML_CONTENT_TYPE, headers=None):
        self.status = status
        self.content_type = content_type
        if isinstance(body, str):
            self.body = body.encode("utf-8")
        elif body is None:
            self.body = b""
        else:
            self.body = body
        self.headers = headers if headers is not None else {}

    # ── Constructeurs nommés ────────────────────────────────────────────────

    @classmethod
    def text(cls, body: str, status: int = 200, headers: dict | None = None) -> "Response":
        """Réponse `text/plain; charset=utf-8`."""
        return cls(status=status, body=body, content_type=_TEXT_CONTENT_TYPE, headers=headers)

    @classmethod
    def html(cls, body: str, status: int = 200, headers: dict | None = None) -> "Response":
        """Réponse `text/html; charset=utf-8`. Le rendu Jinja2 reste à la
        charge du contrôleur (voir `core.http.helpers.html`)."""
        return cls(status=status, body=body, content_type=_HTML_CONTENT_TYPE, headers=headers)

    @classmethod
    def json(
        cls,
        data: Any,
        status: int = 200,
        headers: dict | None = None,
    ) -> "Response":
        """Réponse `application/json; charset=utf-8` sérialisée via
        `json.dumps(..., ensure_ascii=False)`.

        Lève `ValueError` si `data` n'est pas sérialisable en JSON.
        """
        try:
            body = _json.dumps(data, ensure_ascii=False)
        except TypeError as exc:
            raise ValueError(f"Données JSON non sérialisables : {exc}") from exc
        return cls(status=status, body=body, content_type=_JSON_CONTENT_TYPE, headers=headers)

    @classmethod
    def debug(cls, obj: Any, status: int = 200) -> "Response":
        """Réponse HTML lisible affichant `obj` de manière inspectable.

        En `APP_ENV=dev` : retourne une page HTML pédagogique
        (`text/html; charset=utf-8`) qui déballe ``obj.data`` si défini,
        sinon le conteneur natif, sinon ``type + repr``. Les clés
        sensibles sont masquées, les chaînes échappées, la profondeur
        bornée et les cycles détectés (voir
        ``core.http.debug_dumper``).

        En `APP_ENV=prod` : refuse — retourne une réponse 404 minimale
        qui ne contient AUCUN détail sur `obj`. Pas d'option pour
        contourner cette protection.
        """
        # Import paresseux : Response est importée tôt dans le boot ; éviter
        # d'introduire une dépendance circulaire avec core.forge.
        from core.forge import get as _cfg

        try:
            env = str(_cfg("app_env")).lower()
        except KeyError:
            env = "dev"

        if env != "dev":
            return cls.text(
                "Response.debug() est désactivé en production.",
                status=404,
            )

        # Import paresseux : évite de charger le renderer (et ses
        # dépendances) tant que `Response.debug` n'est pas réellement appelé.
        from core.http.debug_dumper import render_debug_html

        return cls.html(render_debug_html(obj), status=status)

    # ── Vue d'inspection ────────────────────────────────────────────────────

    @property
    def cookies(self) -> list[str]:
        """Liste des **noms** de cookies posés via `Set-Cookie`.

        Ne renvoie jamais les valeurs : ce sont typiquement des tokens de
        session. La liste est vide si aucun cookie n'est posé.
        """
        raw = self.headers.get("Set-Cookie") if isinstance(self.headers, dict) else None
        if not raw:
            return []
        if isinstance(raw, list):
            cookie_headers = raw
        else:
            cookie_headers = [raw]
        names: list[str] = []
        for header_value in cookie_headers:
            name = str(header_value).split(";", 1)[0].split("=", 1)[0].strip()
            if name:
                names.append(name)
        return names

    @property
    def data(self) -> dict:
        """Représentation publique stable, sûre à afficher en debug.

        N'inclut pas le corps brut (potentiellement HTML rendu, donc
        sensible aux données utilisateur). Les valeurs des headers
        sensibles (`Set-Cookie`, `Authorization`) sont masquées.
        """
        masked_headers: dict[str, Any] = {}
        if isinstance(self.headers, dict):
            for key, value in self.headers.items():
                if _is_sensitive_response_header(key):
                    masked_headers[key] = "[masked]"
                else:
                    masked_headers[key] = value
        return {
            "status": self.status,
            "content_type": self.content_type,
            "body_size": len(self.body),
            "headers": masked_headers,
            "cookies": self.cookies,
        }

    def __repr__(self) -> str:  # pragma: no cover — purement cosmétique
        return f"<Response {self.status} {self.content_type} {len(self.body)}o>"
