from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from mvc.models.cours_model import get_cours, get_cours_by_id
from mvc.models.observation_cours_model import get_observations_by_cours


def _parse_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class CoursController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        cours = get_cours()
        return BaseController.render(
            "cours/index.html",
            context={"cours": cours},
            request=request,
        )

    @staticmethod
    def show(request: Request) -> Response:
        cours_id = _parse_id(request.route_params.get("id"))
        if cours_id is None:
            return BaseController.not_found()
        cours = get_cours_by_id(cours_id)
        if cours is None:
            return BaseController.not_found()
        observations = get_observations_by_cours(cours_id)
        return BaseController.render(
            "cours/show.html",
            context={"cours": cours, "observations": observations},
            request=request,
        )
