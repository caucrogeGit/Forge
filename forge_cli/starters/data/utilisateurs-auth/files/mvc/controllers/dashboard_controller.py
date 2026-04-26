from core.mvc.controller.base_controller import BaseController
from core.security.session import get_utilisateur


class DashboardController(BaseController):
    """Pages protégées du starter Utilisateurs / authentification."""

    @staticmethod
    def index(request):
        utilisateur = get_utilisateur(request)
        return BaseController.render(
            "dashboard/index.html",
            context={"utilisateur": utilisateur},
            request=request,
        )

    @staticmethod
    def profile(request):
        utilisateur = get_utilisateur(request)
        return BaseController.render(
            "dashboard/profil.html",
            context={"utilisateur": utilisateur},
            request=request,
        )
