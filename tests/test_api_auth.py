"""Tests — API-AUTH-001 : auth API minimale par token Bearer."""

import json

from core.security.api_auth import (
    get_api_token_from_request,
    is_valid_api_token,
    require_api_token,
)
from core.http import api_success
from core.http.response import Response
from tests.fake_request import FakeRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _req(auth_header=None):
    headers = {}
    if auth_header is not None:
        headers["Authorization"] = auth_header
    return FakeRequest("GET", "/api/status", headers=headers)


def _protected(request):
    return api_success({"status": "ok"})


_handler = require_api_token(_protected)


# ---------------------------------------------------------------------------
# get_api_token_from_request
# ---------------------------------------------------------------------------


class TestGetApiTokenFromRequest:
    def test_header_absent_retourne_none(self):
        assert get_api_token_from_request(_req()) is None

    def test_bearer_valide_retourne_token(self):
        assert get_api_token_from_request(_req("Bearer abc123")) == "abc123"

    def test_bearer_minuscule_accepte(self):
        assert get_api_token_from_request(_req("bearer abc123")) == "abc123"

    def test_bearer_majuscules_accepte(self):
        assert get_api_token_from_request(_req("BEARER abc123")) == "abc123"

    def test_format_token_invalide_retourne_none(self):
        assert get_api_token_from_request(_req("Token abc123")) is None

    def test_sans_espace_retourne_none(self):
        assert get_api_token_from_request(_req("Bearerabc123")) is None

    def test_juste_bearer_retourne_none(self):
        assert get_api_token_from_request(_req("Bearer")) is None

    def test_token_avec_espaces_interne(self):
        token = get_api_token_from_request(_req("Bearer abc 123"))
        assert token == "abc 123"


# ---------------------------------------------------------------------------
# is_valid_api_token
# ---------------------------------------------------------------------------


class TestIsValidApiToken:
    def test_token_valide(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "secret123")
        assert is_valid_api_token(_req("Bearer secret123")) is True

    def test_token_invalide(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "secret123")
        assert is_valid_api_token(_req("Bearer wrong")) is False

    def test_token_absent(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "secret123")
        assert is_valid_api_token(_req()) is False

    def test_api_token_non_configure(self, monkeypatch):
        monkeypatch.delenv("API_TOKEN", raising=False)
        assert is_valid_api_token(_req("Bearer anything")) is False

    def test_api_token_vide(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "")
        assert is_valid_api_token(_req("Bearer anything")) is False


# ---------------------------------------------------------------------------
# require_api_token — token absent
# ---------------------------------------------------------------------------


class TestTokenAbsent:
    def test_statut_401(self):
        resp = _handler(_req())
        assert resp.status == 401

    def test_content_type_json(self):
        resp = _handler(_req())
        assert resp.content_type == "application/json; charset=utf-8"

    def test_success_false(self):
        body = json.loads(_handler(_req()).body)
        assert body["success"] is False

    def test_code_unauthorized(self):
        body = json.loads(_handler(_req()).body)
        assert body["error"]["code"] == "unauthorized"

    def test_message_present(self):
        body = json.loads(_handler(_req()).body)
        assert body["error"]["message"]

    def test_token_absent_des_erreurs(self):
        body = json.loads(_handler(_req()).body)
        assert "Bearer" not in json.dumps(body)
        assert "API_TOKEN" not in json.dumps(body)


# ---------------------------------------------------------------------------
# require_api_token — header mal formé
# ---------------------------------------------------------------------------


class TestHeaderMalForme:
    def test_statut_401(self):
        resp = _handler(_req("Token abc123"))
        assert resp.status == 401

    def test_code_invalid_authorization_header(self):
        body = json.loads(_handler(_req("Token abc123")).body)
        assert body["error"]["code"] == "invalid_authorization_header"

    def test_basic_auth_refuse(self):
        resp = _handler(_req("Basic dXNlcjpwYXNz"))
        body = json.loads(resp.body)
        assert body["error"]["code"] == "invalid_authorization_header"

    def test_bearer_seul_refuse(self):
        resp = _handler(_req("Bearer"))
        body = json.loads(resp.body)
        assert body["success"] is False


# ---------------------------------------------------------------------------
# require_api_token — token invalide
# ---------------------------------------------------------------------------


class TestTokenInvalide:
    def test_statut_401(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "correct-token")
        resp = _handler(_req("Bearer wrong-token"))
        assert resp.status == 401

    def test_code_invalid_token(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "correct-token")
        body = json.loads(_handler(_req("Bearer wrong-token")).body)
        assert body["error"]["code"] == "invalid_token"

    def test_token_vide_refuse(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "correct-token")
        resp = _handler(_req("Bearer "))
        assert resp.status == 401

    def test_api_token_non_configure_refuse_tout(self, monkeypatch):
        monkeypatch.delenv("API_TOKEN", raising=False)
        resp = _handler(_req("Bearer anything"))
        assert resp.status == 401

    def test_token_invalide_ne_contient_pas_le_token(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "correct-token")
        body = json.loads(_handler(_req("Bearer wrong-token")).body)
        assert "wrong-token" not in json.dumps(body)
        assert "correct-token" not in json.dumps(body)


# ---------------------------------------------------------------------------
# require_api_token — token valide
# ---------------------------------------------------------------------------


class TestTokenValide:
    def test_statut_200(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "my-secret")
        resp = _handler(_req("Bearer my-secret"))
        assert resp.status == 200

    def test_succes_true(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "my-secret")
        body = json.loads(_handler(_req("Bearer my-secret")).body)
        assert body["success"] is True

    def test_data_present(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "my-secret")
        body = json.loads(_handler(_req("Bearer my-secret")).body)
        assert "data" in body

    def test_content_type_json(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "my-secret")
        resp = _handler(_req("Bearer my-secret"))
        assert resp.content_type == "application/json; charset=utf-8"

    def test_token_valide_bearer_casse_insensible(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "my-secret")
        resp = _handler(_req("BEARER my-secret"))
        assert resp.status == 200


# ---------------------------------------------------------------------------
# Sécurité — token absent des réponses et des traces
# ---------------------------------------------------------------------------


class TestSecurite:
    def test_token_absent_des_reponses_succes(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "super-secret-token")
        body = json.loads(_handler(_req("Bearer super-secret-token")).body)
        raw = json.dumps(body)
        assert "super-secret-token" not in raw

    def test_api_token_env_absent_des_reponses(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "env-secret")
        body = json.loads(_handler(_req("Bearer wrong")).body)
        assert "env-secret" not in json.dumps(body)

    def test_reponse_erreur_generique(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "secret")
        body = json.loads(_handler(_req("Bearer bad")).body)
        assert body["error"]["code"] in ("unauthorized", "invalid_token",
                                          "invalid_authorization_header")


# ---------------------------------------------------------------------------
# Routes HTML non impactées
# ---------------------------------------------------------------------------


class TestRoutesHTMLNonImpactees:
    def test_route_html_normale(self):
        from core.app.application import Application
        from core.http.router import Router

        router = Router()
        router.add("GET", "/", lambda r: Response(200, "<h1>ok</h1>"), public=True)

        app = Application(router, middlewares=[], api_routes_module=None)
        resp = app.dispatch(FakeRequest("GET", "/"))
        assert resp.status == 200
        assert "text/html" in resp.content_type

    def test_route_html_non_protegee_par_require_api_token(self):
        def home(request):
            return Response(200, "Accueil")

        resp = home(FakeRequest("GET", "/"))
        assert resp.status == 200


# ---------------------------------------------------------------------------
# Intégration avec Application.dispatch()
# ---------------------------------------------------------------------------


class TestIntegrationDispatch:
    def test_dispatch_route_protegee_sans_token(self, monkeypatch):
        from core.app.application import Application
        from core.http.router import Router

        monkeypatch.setenv("API_TOKEN", "secret")
        router = Router()

        @require_api_token
        def api_handler(request):
            return api_success({"ok": True})

        router.add("GET", "/api/test", api_handler, public=True)
        app = Application(router, middlewares=[], api_routes_module=None)

        resp = app.dispatch(FakeRequest("GET", "/api/test"))
        assert resp.status == 401
        body = json.loads(resp.body)
        assert body["success"] is False

    def test_dispatch_route_protegee_token_valide(self, monkeypatch):
        from core.app.application import Application
        from core.http.router import Router

        monkeypatch.setenv("API_TOKEN", "secret")
        router = Router()

        @require_api_token
        def api_handler(request):
            return api_success({"ok": True})

        router.add("GET", "/api/test", api_handler, public=True)
        app = Application(router, middlewares=[], api_routes_module=None)

        resp = app.dispatch(FakeRequest(
            "GET", "/api/test",
            headers={"Authorization": "Bearer secret"}
        ))
        assert resp.status == 200
        body = json.loads(resp.body)
        assert body["success"] is True
