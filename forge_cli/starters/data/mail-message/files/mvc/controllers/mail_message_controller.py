from core.http.request import Request
from core.http.response import Response
from forge_mvc_mail import MailMessage
from core.mvc.controller.base_controller import BaseController


class MailMessageController(BaseController):
    """Composer un MailMessage et inspecter ses champs (sans envoi)."""

    @staticmethod
    def index(request: Request) -> Response:
        message = MailMessage(
            subject="Bienvenue sur Forge",
            to="alice@example.test",
            cc="equipe@example.test",
            body_text="Bonjour Alice, ceci est un message de demonstration.",
            body_html="<p>Bonjour Alice, ceci est un message de <strong>demonstration</strong>.</p>",
            from_email="noreply@example.test",
        )
        return BaseController.render(
            "mail_message/index.html",
            context={
                "subject": message.subject,
                "to": message.to,
                "cc": message.cc,
                "has_html": message.body_html is not None,
            },
            request=request,
        )
