from core.mvc.controller.base_controller import BaseController
from mvc.models.cours_model import get_cours, get_cours_by_id
from mvc.models.observation_cours_model import get_observations_by_cours


class CoursController(BaseController):

    @staticmethod
    def index(request):
        cours = get_cours()
        return BaseController.render(
            "cours/index.html",
            context={"cours": cours},
            request=request,
        )

    @staticmethod
    def show(request):
        cours_id = int(request.route_params["id"])
        cours = get_cours_by_id(cours_id)
        if cours is None:
            return BaseController.not_found()
        observations = get_observations_by_cours(cours_id)
        return BaseController.render(
            "cours/show.html",
            context={"cours": cours, "observations": observations},
            request=request,
        )
