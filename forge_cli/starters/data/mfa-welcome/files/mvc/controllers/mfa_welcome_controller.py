"""Starter Bonjour Forge MFA — palier 1 du niveau débutant (progression welcome-mfa).

Ticket : STARTER-MFA-WELCOME-001.

Premier contact avec le module **opt-in** ``forge-mvc-mfa`` : TOTP, codes de
récupération, challenge de connexion, revalidation. Ce parcours décortique chaque
brique ; le flux Auth+MFA câblé de bout en bout vit dans le starter
``welcome-optin-mfa``.

  ``index``   — `GET /mfa-welcome` : réponse texte « Bonjour Forge MFA ».
  ``inspect`` — `GET /mfa-welcome/inspect` : facteurs, statuts, et présence de la
                clé de chiffrement ``FORGE_MFA_SECRET_KEY`` (sans la révéler).

Aucune base de données. Installe le module : ``pip install --pre forge-mvc-mfa``
(publié sur PyPI) et configure ``FORGE_MFA_SECRET_KEY`` (voir « Installation »).
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_mfa import (
    MFA_FACTOR_RECOVERY,
    MFA_FACTOR_TOTP,
    MFA_STATUS_ACTIVE,
    MFA_STATUS_DISABLED,
    MFA_STATUS_PENDING,
    validate_mfa_secret_key_config,
)


def _capabilities() -> dict:
    """Décrit les facteurs/statuts MFA et l'état de la clé de chiffrement."""
    try:
        validate_mfa_secret_key_config()
        secret_key = "configurée"
    except Exception as exc:  # clé absente, invalide, ou placeholder
        secret_key = f"non configurée ({type(exc).__name__})"
    return {
        "factors": [MFA_FACTOR_TOTP, MFA_FACTOR_RECOVERY],
        "statuses": [MFA_STATUS_PENDING, MFA_STATUS_ACTIVE, MFA_STATUS_DISABLED],
        "secret_key": secret_key,
    }


class MfaWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge MFA."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge MFA")

    @staticmethod
    def inspect(request: Request) -> Response:
        return Response.json(_capabilities())
