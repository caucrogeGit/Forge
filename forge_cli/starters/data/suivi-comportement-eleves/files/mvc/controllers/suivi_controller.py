from core.auth.session import get_authenticated_user_id
from core.mvc.controller.base_controller import BaseController
from mvc.models.auth_model import get_user_by_id
from mvc.models.cours_model import get_cours_recents


class SuiviController(BaseController):

    @staticmethod
    def index(request):
        user_id = get_authenticated_user_id(request)
        utilisateur = get_user_by_id(user_id) if user_id else None
        cours_recents = get_cours_recents(limit=5)
        return BaseController.render(
            "suivi/dashboard.html",
            context={"utilisateur": utilisateur, "cours_recents": cours_recents},
            request=request,
        )
