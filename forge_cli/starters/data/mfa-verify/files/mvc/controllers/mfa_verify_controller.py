"""Starter Vérifier un code TOTP — palier 3 du niveau débutant (progression welcome-mfa).

Ticket : STARTER-MFA-VERIFY-001.

``verify_totp_code`` confronte un code à 6 chiffres au **secret** partagé, avec une
petite **fenêtre de tolérance** (`valid_window`) pour absorber le décalage d'horloge.
C'est le contrôle au cœur du TOTP — celui qui se rejoue à chaque connexion.

  ``index`` — `GET  /mfa-verify` : formulaire (secret + code).
  ``check`` — `POST /mfa-verify` : vérifie le code et affiche valide / invalide.

Aucune base de données, aucune clé de chiffrement requise (on travaille sur un
secret brut, fourni par l'utilisateur pour la démonstration).
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_mfa import verify_totp_code


class MfaVerifyController(BaseController):
    """Starter pédagogique : vérifier un code TOTP contre un secret."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "mfa_verify/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def check(request: Request) -> Response:
        secret = (request.form("secret") or "").strip()
        code = (request.form("code") or "").strip()
        context = {"csrf_token": BaseController.csrf_token(request), "secret": secret}
        if not secret or not code:
            context["error"] = "Renseignez le secret et le code."
            return BaseController.render("mfa_verify/index.html", context=context, request=request)
        try:
            context["valid"] = bool(verify_totp_code(secret, code))
        except Exception as exc:
            context["error"] = f"Secret invalide : {exc}"
        return BaseController.render("mfa_verify/index.html", context=context, request=request)
