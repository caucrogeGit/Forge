import json
import pytest
import core.forge as forge
from core.http.router import Router
from core.mvc.controller.base_controller import BaseController
from tests.fake_request import FakeRequest


def _handler(_request):
    return None


class TestBaseControllerJson:
    def test_json_status_200(self):
        resp = BaseController.json({"ok": True})
        assert resp.status == 200

    def test_json_content_type(self):
        resp = BaseController.json({"ok": True})
        assert "application/json" in resp.content_type

    def test_json_body_serialise(self):
        data = {"id": 1, "nom": "Dupont"}
        resp = BaseController.json(data)
        assert json.loads(resp.body) == data

    def test_json_status_personnalise(self):
        resp = BaseController.json({"erreur": "non trouvé"}, status=404)
        assert resp.status == 404

    def test_json_unicode(self):
        resp = BaseController.json({"msg": "héros"})
        assert "héros" in resp.body.decode("utf-8")

    def test_json_body_request_vide_sur_get(self):
        req = FakeRequest("GET", "/api")
        assert BaseController.json_body(req) == {}

    def test_json_body_request_retourne_json_body(self):
        req = FakeRequest("POST", "/api", json_body={"ids": [1, 2]})
        assert BaseController.json_body(req) == {"ids": [1, 2]}


class TestBaseControllerNavigation:
    def test_redirect_to_route(self):
        router = Router()
        router.add("GET", "/contacts/{id}", _handler, name="contacts_show")
        forge._cfg["router"] = router

        resp = BaseController.redirect_to_route("contacts_show", id=42)

        assert resp.status == 302
        assert resp.headers["Location"] == "/contacts/42"

    def test_http_errors_standardises(self, tmp_path):
        (tmp_path / "errors").mkdir()
        (tmp_path / "errors" / "400.html").write_text("400", encoding="utf-8")
        (tmp_path / "errors" / "403.html").write_text("403", encoding="utf-8")
        (tmp_path / "errors" / "422.html").write_text("422", encoding="utf-8")
        (tmp_path / "errors" / "500.html").write_text("500", encoding="utf-8")
        from core.templating.manager import template_manager
        from integrations.jinja2.renderer import Jinja2Renderer
        template_manager.register(Jinja2Renderer(str(tmp_path)))
        forge._cfg["views_dir"] = str(tmp_path)

        assert BaseController.bad_request().status == 400
        assert BaseController.forbidden().status == 403
        assert BaseController.validation_error().status == 422
        assert BaseController.server_error().status == 500


class TestFakeRequest:
    def test_method_normalise(self):
        req = FakeRequest("get", "/")
        assert req.method == "GET"

    def test_body_format_parse_qs(self):
        req = FakeRequest("POST", "/form", body={"Nom": "Alice"})
        assert req.body == {"Nom": ["Alice"]}

    def test_json_body_vide_par_defaut(self):
        req = FakeRequest("POST", "/form", body={"x": "1"})
        assert req.json_body == {}

    def test_session_id_dans_cookie(self):
        req = FakeRequest("GET", "/", session_id="abc123")
        cookie = req.headers.get("Cookie", "")
        assert "session_id=abc123" in cookie

    def test_sans_session_cookie_vide(self):
        req = FakeRequest("GET", "/")
        assert req.headers.get("Cookie", "") == ""

    def test_params(self):
        req = FakeRequest("GET", "/clients", params={"page": "2"})
        assert req.params == {"page": ["2"]}

    def test_route_params_vide_par_defaut(self):
        req = FakeRequest("GET", "/clients/42")
        assert req.route_params == {}

    def test_method_override_post_vers_delete(self):
        req = FakeRequest("POST", "/contacts/1", body={"_method": "DELETE"})

        assert req.original_method == "POST"
        assert req.method == "DELETE"

    def test_method_override_ignore_get(self):
        req = FakeRequest("GET", "/contacts/1", body={"_method": "DELETE"})

        assert req.original_method == "GET"
        assert req.method == "GET"
