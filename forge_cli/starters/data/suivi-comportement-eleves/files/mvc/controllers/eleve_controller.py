from core.mvc.controller.base_controller import BaseController
from mvc.models.eleve_model import get_eleve_by_id, get_eleves
from mvc.models.observation_cours_model import get_observations_by_eleve


def _parse_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class EleveController(BaseController):

    @staticmethod
    def index(request):
        eleves = get_eleves()
        return BaseController.render(
            "eleve/index.html",
            context={"eleves": eleves},
            request=request,
        )

    @staticmethod
    def show(request):
        eleve_id = _parse_id(request.route_params.get("id"))
        if eleve_id is None:
            return BaseController.not_found()
        eleve = get_eleve_by_id(eleve_id)
        if eleve is None:
            return BaseController.not_found()
        observations = get_observations_by_eleve(eleve_id)
        return BaseController.render(
            "eleve/show.html",
            context={"eleve": eleve, "observations": observations},
            request=request,
        )
