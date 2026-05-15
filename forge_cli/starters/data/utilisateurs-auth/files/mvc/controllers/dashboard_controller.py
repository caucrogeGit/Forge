from core.auth import get_authenticated_user_id, login_required
from core.mvc.controller.base_controller import BaseController
from mvc.models.auth_model import get_user_by_id


class DashboardController(BaseController):
    """Pages protégées du starter Utilisateurs / authentification."""

    @staticmethod
    @login_required(redirect_to="/login")
    def index(request):
        user_id = get_authenticated_user_id(request)
        utilisateur = get_user_by_id(user_id)
        return BaseController.render(
            "dashboard/index.html",
            context={"utilisateur": utilisateur},
            request=request,
        )

    @staticmethod
    @login_required(redirect_to="/login")
    def profile(request):
        user_id = get_authenticated_user_id(request)
        utilisateur = get_user_by_id(user_id)
        return BaseController.render(
            "dashboard/profil.html",
            context={"utilisateur": utilisateur},
            request=request,
        )
