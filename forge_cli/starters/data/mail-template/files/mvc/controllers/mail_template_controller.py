from core.http.request import Request
from core.http.response import Response
from forge_mvc_mail import MailTemplateError, MailTemplateRenderer
from core.mvc.controller.base_controller import BaseController


class MailTemplateController(BaseController):
    """Rendre un email depuis un template Jinja via MailTemplateRenderer."""

    @staticmethod
    def index(request: Request) -> Response:
        context = {}
        try:
            renderer = MailTemplateRenderer("mail_templates")
            message = renderer.render(
                "welcome.txt",
                {"name": "Alice"},
                to="alice@example.test",
            )
            context["subject"] = message.subject
            context["body"] = message.body_text
        except MailTemplateError as exc:
            context["error"] = str(exc)
        return BaseController.render(
            "mail_template/index.html", context=context, request=request
        )
