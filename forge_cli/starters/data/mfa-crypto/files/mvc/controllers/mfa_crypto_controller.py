"""Starter Secret chiffré au repos — palier 3 du niveau avancé (welcome-mfa).

Ticket : STARTER-MFA-CRYPTO-001.

Un secret TOTP ne doit **jamais** vivre en clair en base. ``encrypt_totp_secret`` le
chiffre (préfixe ``enc:``) avec ``FORGE_MFA_SECRET_KEY`` (Fernet) ;
``decrypt_totp_secret`` le déchiffre au moment de vérifier un code.
``validate_mfa_secret_key_config`` contrôle que la clé est correctement configurée.

  ``index`` — `GET  /mfa-crypto` : état de la clé + formulaire.
  ``demo``  — `POST /mfa-crypto` : chiffre un secret puis le déchiffre (aller-retour).

Aucune base de données. Nécessite ``FORGE_MFA_SECRET_KEY`` (sinon, message clair).
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_mfa import (
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_totp_secret,
    validate_mfa_secret_key_config,
)


def _key_state() -> str:
    try:
        validate_mfa_secret_key_config()
        return "configurée"
    except Exception as exc:
        return f"non configurée ({type(exc).__name__})"


class MfaCryptoController(BaseController):
    """Starter pédagogique : chiffrer/déchiffrer un secret TOTP au repos."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "mfa_crypto/index.html",
            context={"csrf_token": BaseController.csrf_token(request), "key_state": _key_state()},
            request=request,
        )

    @staticmethod
    def demo(request: Request) -> Response:
        raw = (request.form("secret") or "").strip() or generate_totp_secret()
        context = {"csrf_token": BaseController.csrf_token(request), "key_state": _key_state(), "raw": raw}
        try:
            encrypted = encrypt_totp_secret(raw)
            decrypted = decrypt_totp_secret(encrypted)
            context["encrypted"] = encrypted
            context["roundtrip_ok"] = decrypted == raw
        except Exception as exc:
            context["error"] = f"Chiffrement impossible (clé MFA ?) : {exc}"
        return BaseController.render("mfa_crypto/index.html", context=context, request=request)
