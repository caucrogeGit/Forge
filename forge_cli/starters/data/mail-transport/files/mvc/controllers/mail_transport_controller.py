from core.http.request import Request
from core.http.response import Response
from forge_mvc_mail import FakeTransport, Mailer, MailMessage
from core.mvc.controller.base_controller import BaseController


class MailTransportController(BaseController):
    """Envoyer via un transport et lire le TransportResult (sans SMTP reel)."""

    @staticmethod
    def index(request: Request) -> Response:
        transport = FakeTransport()
        result = Mailer(transport).send(MailMessage(
            subject="Test transport",
            to="dest@example.test",
            body_text="Contenu de test.",
        ))
        return BaseController.render(
            "mail_transport/index.html",
            context={
                "transport_name": transport.name,
                "sent_count": transport.sent_count,
                "success": result.success,
                "skipped": result.skipped,
            },
            request=request,
        )
