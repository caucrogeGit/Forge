from core.http.request import Request
from core.http.response import Response
from forge_mvc_mail import MailConfig
from core.mvc.controller.base_controller import BaseController


class MailDoctorController(BaseController):
    """Diagnostic non invasif du module mail, expose en JSON."""

    @staticmethod
    def index(request: Request) -> Response:
        checks: dict = {}
        try:
            cfg = MailConfig.from_forge()
            checks["config_loaded"] = True
            checks["enabled"] = cfg.enabled
            checks["transport"] = cfg.transport_name
            checks["from_email_set"] = bool(cfg.from_email)
        except Exception as exc:
            checks["config_loaded"] = False
            checks["error"] = str(exc)
        return Response.json(checks)
