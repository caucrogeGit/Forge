from core.mvc.controller.base_controller import BaseController
from core.security.session import get_utilisateur
from mvc.models.cours_model import get_cours_recents


class SuiviController(BaseController):

    @staticmethod
    def index(request):
        utilisateur = get_utilisateur(request)
        cours_recents = get_cours_recents(limit=5)
        return BaseController.render(
            "suivi/dashboard.html",
            context={"utilisateur": utilisateur, "cours_recents": cours_recents},
            request=request,
        )
