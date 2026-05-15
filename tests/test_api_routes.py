"""Tests — API-ROUTES-001 : convention mvc/api_routes.py dans Forge."""

import json
import sys
import types

import pytest

from core.api_routes_loader import load_api_routes
from core.http import api_success, api_error
from core.http.router import Router
from core.http.response import Response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_router():
    """Retourne un routeur vide."""
    return Router()


def _make_api_module(register_fn=None):
    """Retourne un faux module mvc.api_routes avec register_api_routes."""
    mod = types.ModuleType("mvc.api_routes")
    if register_fn is not None:
        mod.register_api_routes = register_fn
    return mod


# ---------------------------------------------------------------------------
# load_api_routes — comportement si absent
# ---------------------------------------------------------------------------


class TestAbsent:
    def test_absent_ne_leve_pas(self):
        router = _make_router()
        load_api_routes(router, module_path="mvc._inexistant_api_routes")

    def test_absent_ne_modifie_pas_le_routeur(self):
        router = _make_router()
        router.add("GET", "/web", lambda r: Response(200, "ok"), public=True)
        load_api_routes(router, module_path="mvc._inexistant_api_routes")
        assert router.match("GET", "/web") is not None

    def test_application_sans_api_routes_demarre(self):
        from core.application import Application
        router = _make_router()
        router.add("GET", "/web", lambda r: Response(200, "web"), public=True)
        app = Application(router, middlewares=[], api_routes_module=None)
        from tests.fake_request import FakeRequest
        resp = app.dispatch(FakeRequest("GET", "/web"))
        assert resp.status == 200


# ---------------------------------------------------------------------------
# load_api_routes — comportement si présent
# ---------------------------------------------------------------------------


class TestPresent:
    def test_charge_la_route_api(self, monkeypatch):
        router = _make_router()

        def register(r):
            r.add("GET", "/api/status", lambda req: Response(200, "ok"), public=True)

        mod = _make_api_module(register)
        monkeypatch.setitem(sys.modules, "mvc.api_test_mod", mod)
        load_api_routes(router, module_path="mvc.api_test_mod")

        assert router.match("GET", "/api/status") is not None

    def test_routes_web_preservees(self, monkeypatch):
        router = _make_router()
        router.add("GET", "/web", lambda r: Response(200, "web"), public=True)

        def register(r):
            r.add("GET", "/api/status", lambda req: Response(200, "ok"), public=True)

        mod = _make_api_module(register)
        monkeypatch.setitem(sys.modules, "mvc.api_test_mod2", mod)
        load_api_routes(router, module_path="mvc.api_test_mod2")

        assert router.match("GET", "/web") is not None
        assert router.match("GET", "/api/status") is not None

    def test_sans_register_api_routes_ne_leve_pas(self, monkeypatch):
        router = _make_router()
        mod = _make_api_module()  # pas de register_api_routes
        monkeypatch.setitem(sys.modules, "mvc.api_test_no_fn", mod)
        load_api_routes(router, module_path="mvc.api_test_no_fn")

    def test_erreur_syntax_leve_import_error(self, monkeypatch):
        router = _make_router()

        def bad_import(name):
            raise SyntaxError("mauvaise syntaxe")

        import importlib
        monkeypatch.setattr(importlib, "import_module",
                            lambda name: bad_import(name) if name == "mvc.api_bad" else None)
        with pytest.raises(ImportError, match="Erreur dans mvc.api_bad"):
            load_api_routes(router, module_path="mvc.api_bad")


# ---------------------------------------------------------------------------
# Application — chargement automatique via api_routes_module
# ---------------------------------------------------------------------------


class TestApplicationApiRoutes:
    def test_api_routes_module_none_saute_le_chargement(self):
        from core.application import Application
        router = _make_router()
        router.add("GET", "/web", lambda r: Response(200, "web"), public=True)
        app = Application(router, middlewares=[], api_routes_module=None)
        from tests.fake_request import FakeRequest
        resp = app.dispatch(FakeRequest("GET", "/web"))
        assert resp.status == 200

    def test_api_routes_charge_via_application(self, monkeypatch):
        from core.application import Application
        from tests.fake_request import FakeRequest

        router = _make_router()

        def register(r):
            r.add("GET", "/api/ping",
                  lambda req: api_success({"ping": "pong"}),
                  public=True)

        mod = _make_api_module(register)
        monkeypatch.setitem(sys.modules, "mvc.api_test_app", mod)

        app = Application(router, middlewares=[], api_routes_module="mvc.api_test_app")
        resp = app.dispatch(FakeRequest("GET", "/api/ping"))
        assert resp.status == 200
        assert "application/json" in resp.content_type
        body = json.loads(resp.body)
        assert body["success"] is True
        assert body["data"]["ping"] == "pong"

    def test_application_defaut_tente_mvc_api_routes(self):
        from core.application import Application
        router = _make_router()
        # mvc.api_routes n'existe pas dans ce projet → ne doit pas lever
        Application(router, middlewares=[])


# ---------------------------------------------------------------------------
# Route API — Content-Type et convention
# ---------------------------------------------------------------------------


class TestRouteApiConvention:
    def test_route_api_retourne_json_success(self, monkeypatch):
        from core.application import Application
        from tests.fake_request import FakeRequest

        router = _make_router()

        def register(r):
            r.add("GET", "/api/status",
                  lambda req: api_success({"status": "ok"}),
                  public=True)

        mod = _make_api_module(register)
        monkeypatch.setitem(sys.modules, "mvc.api_conv1", mod)
        app = Application(router, middlewares=[], api_routes_module="mvc.api_conv1")

        resp = app.dispatch(FakeRequest("GET", "/api/status"))
        assert resp.status == 200
        assert resp.content_type == "application/json; charset=utf-8"
        body = json.loads(resp.body)
        assert body["success"] is True

    def test_route_api_retourne_api_error(self, monkeypatch):
        from core.application import Application
        from tests.fake_request import FakeRequest

        router = _make_router()

        def register(r):
            r.add("GET", "/api/missing",
                  lambda req: api_error("Introuvable", status=404, code="not_found"),
                  public=True)

        mod = _make_api_module(register)
        monkeypatch.setitem(sys.modules, "mvc.api_conv2", mod)
        app = Application(router, middlewares=[], api_routes_module="mvc.api_conv2")

        resp = app.dispatch(FakeRequest("GET", "/api/missing"))
        assert resp.status == 404
        body = json.loads(resp.body)
        assert body["success"] is False
        assert body["error"]["code"] == "not_found"

    def test_statut_201_creation(self, monkeypatch):
        from core.application import Application
        from tests.fake_request import FakeRequest

        router = _make_router()

        def register(r):
            r.add("POST", "/api/items",
                  lambda req: api_success({"id": 1}, status=201),
                  public=True, csrf=False)

        mod = _make_api_module(register)
        monkeypatch.setitem(sys.modules, "mvc.api_conv3", mod)
        app = Application(router, middlewares=[], api_routes_module="mvc.api_conv3")

        resp = app.dispatch(FakeRequest("POST", "/api/items"))
        assert resp.status == 201

    def test_web_route_inchangee(self, monkeypatch):
        from core.application import Application
        from tests.fake_request import FakeRequest

        router = _make_router()
        router.add("GET", "/", lambda r: Response(200, "<h1>Accueil</h1>"), public=True)

        def register(r):
            r.add("GET", "/api/status",
                  lambda req: api_success({"ok": True}),
                  public=True)

        mod = _make_api_module(register)
        monkeypatch.setitem(sys.modules, "mvc.api_conv4", mod)
        app = Application(router, middlewares=[], api_routes_module="mvc.api_conv4")

        web_resp = app.dispatch(FakeRequest("GET", "/"))
        api_resp = app.dispatch(FakeRequest("GET", "/api/status"))

        assert web_resp.status == 200
        assert "text/html" in web_resp.content_type
        assert api_resp.status == 200
        assert "application/json" in api_resp.content_type


# ---------------------------------------------------------------------------
# Convention register_api_routes
# ---------------------------------------------------------------------------


class TestConventionRegisterApiRoutes:
    def test_signature_register_api_routes(self, monkeypatch):
        """register_api_routes reçoit le routeur et ajoute des routes."""
        router = _make_router()
        routes_added = []

        def register(r):
            routes_added.append("added")
            r.add("GET", "/api/test", lambda req: Response(200, "ok"), public=True)

        mod = _make_api_module(register)
        monkeypatch.setitem(sys.modules, "mvc.api_sig", mod)
        load_api_routes(router, module_path="mvc.api_sig")

        assert "added" in routes_added
        assert router.match("GET", "/api/test") is not None

    def test_api_true_flag_conserve(self, monkeypatch):
        """Les routes déclarées avec api=True conservent ce flag."""
        router = _make_router()

        def register(r):
            r.add("GET", "/api/flagged",
                  lambda req: Response(200, "ok"),
                  public=True, api=True)

        mod = _make_api_module(register)
        monkeypatch.setitem(sys.modules, "mvc.api_flag", mod)
        load_api_routes(router, module_path="mvc.api_flag")

        result = router.match("GET", "/api/flagged")
        assert result is not None
        entry, _ = result
        assert entry.api is True

    def test_group_api_prefix(self, monkeypatch):
        """Un groupe /api/ avec api=True enregistre plusieurs routes."""
        router = _make_router()

        def register(r):
            with r.group("/api", public=True, api=True) as g:
                g.add("GET", "/items", lambda req: api_success([]), name="api_items")
                g.add("GET", "/items/{id}", lambda req: api_success({}), name="api_item_show")

        mod = _make_api_module(register)
        monkeypatch.setitem(sys.modules, "mvc.api_group", mod)
        load_api_routes(router, module_path="mvc.api_group")

        assert router.match("GET", "/api/items") is not None
        assert router.match("GET", "/api/items/42") is not None
