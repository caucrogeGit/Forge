from core.mvc.controller import BaseController
from mvc.models.ville_model import get_villes


class VilleController(BaseController):
    @staticmethod
    def index(request):
        villes = get_villes()
        return BaseController.render(
            "ville/index.html",
            context={"villes": villes},
            request=request,
        )
