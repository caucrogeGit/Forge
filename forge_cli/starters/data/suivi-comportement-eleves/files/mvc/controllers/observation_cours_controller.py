from core.mvc.controller.base_controller import BaseController
from core.security.session import get_session, get_session_id
from mvc.models.cours_model import get_cours
from mvc.models.eleve_model import get_eleves
from mvc.models.observation_cours_model import (
    add_observation,
    get_observation_by_id,
    update_observation,
)

_BOOL_FIELDS = (
    "ne_travaille_pas",
    "bavarde",
    "dort",
    "telephone",
    "perturbe",
    "refuse_consigne",
)


def _parse_body(body: dict) -> dict:
    data = {k: k in body for k in _BOOL_FIELDS}
    data["remarque"] = body.get("remarque", [""])[0].strip() or None
    return data


def _csrf_ok(request) -> bool:
    session_id = get_session_id(request)
    session = get_session(session_id)
    token = request.body.get("csrf_token", [None])[0]
    return bool(session and token == session.get("csrf_token"))


class ObservationCoursController(BaseController):

    @staticmethod
    def new(request):
        eleves = get_eleves()
        cours = get_cours()
        return BaseController.render(
            "observations/new.html",
            context={
                "eleves": eleves,
                "cours": cours,
                "csrf_token": BaseController.csrf_token(request),
                "bool_fields": _BOOL_FIELDS,
            },
            request=request,
        )

    @staticmethod
    def create(request):
        if not _csrf_ok(request):
            return BaseController.render("errors/403.html", 403, base=None)

        eleve_id_raw = request.body.get("eleve_id", [""])[0]
        cours_id_raw = request.body.get("cours_id", [""])[0]
        if not eleve_id_raw or not cours_id_raw:
            return BaseController.redirect("/observations/new")

        obs_id = add_observation(int(eleve_id_raw), int(cours_id_raw), _parse_body(request.body))
        return BaseController.redirect(f"/observations/{obs_id}")

    @staticmethod
    def show(request):
        obs_id = int(request.route_params["id"])
        obs = get_observation_by_id(obs_id)
        if obs is None:
            return BaseController.not_found()
        return BaseController.render(
            "observations/show.html",
            context={"obs": obs, "bool_fields": _BOOL_FIELDS},
            request=request,
        )

    @staticmethod
    def edit(request):
        obs_id = int(request.route_params["id"])
        obs = get_observation_by_id(obs_id)
        if obs is None:
            return BaseController.not_found()
        return BaseController.render(
            "observations/edit.html",
            context={
                "obs": obs,
                "eleves": get_eleves(),
                "cours": get_cours(),
                "csrf_token": BaseController.csrf_token(request),
                "bool_fields": _BOOL_FIELDS,
            },
            request=request,
        )

    @staticmethod
    def update(request):
        obs_id = int(request.route_params["id"])
        if get_observation_by_id(obs_id) is None:
            return BaseController.not_found()
        if not _csrf_ok(request):
            return BaseController.render("errors/403.html", 403, base=None)

        update_observation(obs_id, _parse_body(request.body))
        return BaseController.redirect(f"/observations/{obs_id}")
