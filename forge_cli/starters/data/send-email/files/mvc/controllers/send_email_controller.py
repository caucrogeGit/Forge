"""Starter Envoyer un email — palier 3 du niveau avancé.

Ticket : STARTER-SEND-EMAIL-001.

Beaucoup d'applications envoient des emails (confirmation, réinitialisation de
mot de passe…). L'opt-in ``forge-mvc-mail`` fournit ``forge_mvc_mail`` : on construit un ``MailMessage``
puis on le confie à un ``Mailer`` branché sur un **transport**. En développement,
``ConsoleTransport`` **affiche** l'email dans la console — pas besoin de serveur
SMTP pour apprendre le flux.

  ``index`` — `GET  /send-email` : affiche le formulaire (destinataire, message).
  ``send``  — `POST /send-email` : construit le ``MailMessage`` et l'envoie via
              ``Mailer(ConsoleTransport())`` ; affiche le résultat.

Aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from forge_mvc_mail import ConsoleTransport, MailError, Mailer, MailMessage
from core.mvc.controller.base_controller import BaseController


class SendEmailController(BaseController):
    """Starter pédagogique : composer et envoyer un email (transport console)."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "send_email/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def send(request: Request) -> Response:
        recipient = (request.form("recipient") or "").strip()
        body = (request.form("message") or "").strip()
        context = {"csrf_token": BaseController.csrf_token(request)}
        try:
            message = MailMessage(
                subject="Message depuis Forge",
                to=recipient,
                body_text=body,
                from_email="noreply@example.test",
            )
            result = Mailer(ConsoleTransport()).send(message)
        except MailError as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "send_email/index.html", context=context, request=request
            )
        context["sent"] = result.success
        context["recipient"] = recipient
        return BaseController.render(
            "send_email/index.html", context=context, request=request
        )
