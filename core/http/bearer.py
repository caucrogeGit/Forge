# pyright: strict
"""Authentification optionnelle par jeton Bearer (CORE-HTTP-BEARER-PRIMITIVE-001).

Primitive partagée par les opt-ins qui exposent des routes HTTP protégeables par
un jeton d'API (forge-mvc-video, forge-mvc-audio, forge-mvc-iot) : quand un jeton
est configuré, la route exige ``Authorization: Bearer <token>`` comparé en temps
constant ; sans jeton configuré, la route est ouverte (mode local/pédagogique).

Centraliser cette logique évite qu'un correctif de sécurité appliqué à une seule
copie laisse les autres vulnérables (charte principe 7 : sécuriser par défaut).
"""
from __future__ import annotations

import secrets
from typing import Any


BEARER_PREFIX = "Bearer "


def extract_bearer_token(request: Any) -> str | None:
    """Jeton d'un en-tête ``Authorization: Bearer <token>``, ou ``None``.

    Retourne ``None`` si l'en-tête est absent ou si le schéma n'est pas
    exactement ``Bearer `` (le nom du schéma n'est pas secret : comparaison
    ordinaire, pas de temps constant ici). ``request`` doit exposer
    ``header(name, default)`` (contrat des objets de requête Forge).
    """
    header = request.header("Authorization", None)
    if not header or not header.startswith(BEARER_PREFIX):
        return None
    return header[len(BEARER_PREFIX):]


def is_bearer_authorized(request: Any, api_token: str | None) -> bool:
    """Autorise la requête selon un jeton d'API optionnel.

    - ``api_token is None`` : API ouverte (mode local/pédagogique) ;
    - sinon, exige un Bearer token égal au jeton configuré, comparé avec
      ``secrets.compare_digest`` (temps constant, anti-timing).
    """
    if api_token is None:
        return True
    provided = extract_bearer_token(request)
    if provided is None:
        return False
    return secrets.compare_digest(provided, api_token)
