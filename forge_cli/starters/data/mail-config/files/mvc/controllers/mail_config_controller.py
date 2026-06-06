from core.http.request import Request
from core.http.response import Response
from forge_mvc_mail import MailConfig
from core.mvc.controller.base_controller import BaseController


class MailConfigController(BaseController):
    """Charger et inspecter la configuration mail (mot de passe masque)."""

    @staticmethod
    def index(request: Request) -> Response:
        context = {}
        try:
            cfg = MailConfig.from_forge()
            context.update({
                "enabled": cfg.enabled,
                "transport": cfg.transport_name,
                "host": cfg.host or "(non defini)",
                "port": cfg.port,
                "from_email": cfg.from_email or "(non defini)",
                "password_set": bool(cfg.password),
            })
        except Exception as exc:
            context["error"] = str(exc)
        return BaseController.render(
            "mail_config/index.html", context=context, request=request
        )
