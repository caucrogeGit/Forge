"""Starter Secret TOTP et QR — palier 2 du niveau débutant (progression welcome-mfa).

Ticket : STARTER-MFA-SECRET-001.

L'enrôlement TOTP commence par un **secret** partagé entre le serveur et
l'application d'authentification de l'utilisateur. ``generate_totp_secret`` produit
ce secret (base32) ; ``totp_provisioning_uri`` construit l'URI ``otpauth://`` que
les applications (Google Authenticator, etc.) savent lire — typiquement via un QR.

  ``index`` — `GET /mfa-secret` : génère un secret de démonstration et son URI.

Transformation **pure** : aucune base de données, aucune clé de chiffrement requise
(le secret n'est pas encore stocké ici).
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_mfa import generate_totp_secret, totp_provisioning_uri


class MfaSecretController(BaseController):
    """Starter pédagogique : générer un secret TOTP et son URI de provisioning."""

    @staticmethod
    def index(request: Request) -> Response:
        secret = generate_totp_secret()
        uri = totp_provisioning_uri(secret, account_name="demo@forge.example", issuer_name="Forge Demo")
        return BaseController.render(
            "mfa_secret/index.html",
            context={"secret": secret, "uri": uri},
            request=request,
        )
