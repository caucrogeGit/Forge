"""Auth API minimale — protection par token Bearer statique."""
import os

from core.http import api_error

_BEARER_PREFIX = "bearer"


def _get_configured_token():
    return os.getenv("API_TOKEN", "")


def get_api_token_from_request(request):
    """Extrait le Bearer token depuis le header Authorization.

    Retourne le token (str) si le format est valide, None sinon.
    Ne retourne jamais le header brut — seulement la valeur après 'Bearer '.
    """
    header = request.headers.get("Authorization", "")
    if not header:
        return None
    parts = header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != _BEARER_PREFIX:
        return None
    return parts[1]


def is_valid_api_token(request):
    """Retourne True si le token Bearer correspond à API_TOKEN.

    Retourne False si API_TOKEN n'est pas configuré ou si le token ne correspond pas.
    """
    expected = _get_configured_token()
    if not expected:
        return False
    token = get_api_token_from_request(request)
    return token == expected


def require_api_token(func):
    """Décorateur — protège une route API par token Bearer.

    Réponses JSON en cas de refus :
        - Header absent → 401 unauthorized
        - Format Bearer invalide → 401 invalid_authorization_header
        - Token absent/invalide/API_TOKEN non configuré → 401 invalid_token

    Le token ne figure jamais dans les réponses ni dans les logs.

    Usage :
        @require_api_token
        def status(request):
            return api_success({"status": "ok"})
    """
    def wrapper(request):
        header = request.headers.get("Authorization", "")

        if not header:
            return api_error(
                "Authentification API requise",
                status=401,
                code="unauthorized",
            )

        parts = header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != _BEARER_PREFIX:
            return api_error(
                "Header Authorization invalide",
                status=401,
                code="invalid_authorization_header",
            )

        expected = _get_configured_token()
        if not expected or parts[1] != expected:
            return api_error(
                "Token API invalide",
                status=401,
                code="invalid_token",
            )

        return func(request)
    return wrapper
