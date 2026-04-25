import pytest
from core.application import Application
from core.http.router import Router
from core.http.response import Response
from core.security import session as _sessions
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer
from tests.fake_request import FakeRequest


def _handler_ok(request):
    return Response(200, "ok")


def _handler_method(request):
    return Response(200, f"{request.original_method}->{request.method}")


def _handler_boom(request):
    raise RuntimeError("boom intentionnel")


def _prepare_error_template(tmp_path, name="403.html", body="erreur"):
    (tmp_path / "errors").mkdir(exist_ok=True)
    (tmp_path / "errors" / name).write_text(body, encoding="utf-8")
    import core.forge as forge
    forge._cfg["views_dir"] = str(tmp_path)
    template_manager.register(Jinja2Renderer(str(tmp_path)))


class _AllowMiddleware:
    def check(self, request):
        return None  # laisse passer


class _BlockMiddleware:
    def check(self, request):
        return Response(403, "interdit")


class TestDispatchExceptions:
    def test_exception_retourne_500(self, tmp_path):
        """Une exception dans un contrôleur produit un 500 sans lever."""
        (tmp_path / "errors").mkdir()
        (tmp_path / "errors" / "500.html").write_text("erreur")
        import core.forge as forge
        forge._cfg["views_dir"] = str(tmp_path)
        template_manager.register(Jinja2Renderer(str(tmp_path)))

        router = Router()
        router.add("GET", "/boom", _handler_boom, public=True)
        app = Application(router, middlewares=[])
        req = FakeRequest("GET", "/boom")
        resp = app.dispatch(req)
        assert resp.status == 500

    def test_route_inconnue_retourne_404(self, tmp_path):
        (tmp_path / "errors").mkdir()
        (tmp_path / "errors" / "404.html").write_text("introuvable")
        import core.forge as forge
        forge._cfg["views_dir"] = str(tmp_path)
        template_manager.register(Jinja2Renderer(str(tmp_path)))

        router = Router()
        app = Application(router, middlewares=[])
        req = FakeRequest("GET", "/introuvable")
        resp = app.dispatch(req)
        assert resp.status == 404


class TestMiddlewarePipeline:
    def test_middleware_bloquant_court_circuite(self):
        router = Router()
        router.add("GET", "/prive", _handler_ok)
        app = Application(router, middlewares=[_BlockMiddleware()])
        req = FakeRequest("GET", "/prive")
        resp = app.dispatch(req)
        assert resp.status == 403

    def test_middleware_passant_atteint_controleur(self, tmp_path):
        router = Router()
        router.add("GET", "/prive", _handler_ok)
        app = Application(router, middlewares=[_AllowMiddleware()])
        req = FakeRequest("GET", "/prive")
        resp = app.dispatch(req)
        assert resp.status == 200

    def test_route_publique_bypasse_middlewares(self):
        router = Router()
        router.add("GET", "/public", _handler_ok, public=True)
        app = Application(router, middlewares=[_BlockMiddleware()])
        req = FakeRequest("GET", "/public")
        resp = app.dispatch(req)
        assert resp.status == 200

    def test_middlewares_vides_passe(self):
        router = Router()
        router.add("GET", "/prive", _handler_ok)
        app = Application(router, middlewares=[])
        req = FakeRequest("GET", "/prive")
        resp = app.dispatch(req)
        assert resp.status == 200

    def test_plusieurs_middlewares_ordre(self):
        router = Router()
        router.add("GET", "/prive", _handler_ok)
        app = Application(router, middlewares=[_AllowMiddleware(), _BlockMiddleware()])
        req = FakeRequest("GET", "/prive")
        resp = app.dispatch(req)
        # AllowMiddleware passe (None), BlockMiddleware bloque (403)
        assert resp.status == 403


class TestAutomaticCsrf:
    def test_post_public_requiert_csrf(self, tmp_path):
        _prepare_error_template(tmp_path, "403.html", "csrf")

        router = Router()
        router.add("POST", "/login", _handler_ok, public=True)
        app = Application(router, middlewares=[])
        resp = app.dispatch(FakeRequest("POST", "/login"))
        assert resp.status == 403

    def test_post_public_accepte_csrf_valide(self, tmp_path):
        _prepare_error_template(tmp_path, "403.html", "csrf")
        sid = _sessions.creer_session()
        token = _sessions.get_session(sid)["csrf_token"]

        router = Router()
        router.add("POST", "/login", _handler_ok, public=True)
        app = Application(router, middlewares=[])
        req = FakeRequest("POST", "/login",
                          body={"csrf_token": token},
                          session_id=sid)
        resp = app.dispatch(req)
        assert resp.status == 200

    def test_route_api_exemptee_explicitement(self, tmp_path):
        _prepare_error_template(tmp_path, "403.html", "csrf")

        router = Router()
        router.add("POST", "/api/webhook", _handler_ok,
                   public=True, csrf=False, api=True)
        app = Application(router, middlewares=[])
        resp = app.dispatch(FakeRequest("POST", "/api/webhook"))
        assert resp.status == 200

    def test_put_requiert_csrf(self, tmp_path):
        _prepare_error_template(tmp_path, "403.html", "csrf")

        router = Router()
        router.add("PUT", "/contacts/1", _handler_ok, public=True)
        app = Application(router, middlewares=[])
        resp = app.dispatch(FakeRequest("PUT", "/contacts/1"))
        assert resp.status == 403

    def test_method_override_route_avant_csrf(self, tmp_path):
        _prepare_error_template(tmp_path, "403.html", "csrf")
        sid = _sessions.creer_session()
        token = _sessions.get_session(sid)["csrf_token"]

        router = Router()
        router.add("DELETE", "/contacts/1", _handler_method, public=True)
        app = Application(router, middlewares=[])
        req = FakeRequest(
            "POST",
            "/contacts/1",
            body={"_method": "DELETE", "csrf_token": token},
            session_id=sid,
        )

        resp = app.dispatch(req)

        assert resp.status == 200
        assert resp.body == b"POST->DELETE"

    def test_csrf_invalide_route_non_publique_rejete_avant_middleware(self, tmp_path):
        """CSRF invalide sur route protégée → 403 sans appeler le middleware."""
        _prepare_error_template(tmp_path, "403.html", "csrf")
        appele = []

        class _MiddlewareEspion:
            def check(self, request):
                appele.append(True)
                return None

        router = Router()
        router.add("POST", "/protege", _handler_ok)  # non-public, csrf=True
        app = Application(router, middlewares=[_MiddlewareEspion()])
        resp = app.dispatch(FakeRequest("POST", "/protege"))

        assert resp.status == 403
        assert not appele, "Le middleware ne doit pas être appelé si CSRF invalide"

    def test_csrf_invalide_route_publique_rejete_avant_middleware(self, tmp_path):
        """CSRF invalide sur route publique → 403 (public=True ne désactive pas CSRF)."""
        _prepare_error_template(tmp_path, "403.html", "csrf")
        appele = []

        class _MiddlewareEspion:
            def check(self, request):
                appele.append(True)
                return None

        router = Router()
        router.add("POST", "/action", _handler_ok, public=True)
        app = Application(router, middlewares=[_MiddlewareEspion()])
        resp = app.dispatch(FakeRequest("POST", "/action"))

        assert resp.status == 403
        assert not appele
