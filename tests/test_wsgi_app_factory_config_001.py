"""Tests — WSGI-APP-FACTORY-CONFIG-001.

Verrouille la cohérence d'initialisation entre `python app.py` et
`core.wsgi.create_configured_wsgi_app()` :

  - la factory expose un callable WSGI conforme ;
  - elle applique `forge.configure(...)` AVANT que la première requête
    ne soit dispatched (donc `trusted_proxies` est honoré en contexte
    WSGI) ;
  - les kwargs de configuration de `core.app_factory` sont alignés sur
    le `forge.configure(...)` central de `app.py` ;
  - les API antérieures (`create_wsgi_app(application)`) restent
    compatibles ;
  - `app.py` n'a pas été cassé structurellement.
"""
from __future__ import annotations

import ast
import re
from io import BytesIO
from pathlib import Path

import pytest

import core.forge as forge
from core.app_factory import _forge_config_kwargs, build_application
from core.application import Application
from core.http.response import Response
from core.http.router import Router
from core.templating.manager import template_manager
from core.wsgi import create_configured_wsgi_app, create_wsgi_app


PROJECT_ROOT = Path(__file__).parent.parent
APP_PY = PROJECT_ROOT / "app.py"


# ── Helpers WSGI ────────────────────────────────────────────────────────────


def _capture():
    captured = {"status": None, "headers": None}

    def start_response(status, headers, exc_info=None):
        captured["status"] = status
        captured["headers"] = headers
        return lambda chunk: None

    return start_response, captured


def _environ(method="GET", path="/", remote="127.0.0.1", extra=None):
    env = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "SERVER_NAME": "test",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": remote,
        "wsgi.input": BytesIO(b""),
        "wsgi.errors": BytesIO(),
        "wsgi.url_scheme": "http",
    }
    if extra:
        env.update(extra)
    return env


@pytest.fixture(autouse=True)
def _restore_renderer_and_proxies():
    """Isole les tests : restaure le renderer Jinja et trusted_proxies."""
    prev_renderer = template_manager._renderer
    prev_proxies = forge.get("trusted_proxies")
    yield
    template_manager._renderer = prev_renderer
    forge.configure(trusted_proxies=prev_proxies)


class _StubRenderer:
    def render(self, template, context):
        return f"[{template}]"


# ── Factory : forme et invocation ───────────────────────────────────────────


class TestFactoryShape:
    def test_returns_callable(self):
        template_manager.register(_StubRenderer())
        app = create_configured_wsgi_app()
        assert callable(app)

    def test_callable_responds_to_minimal_get(self):
        template_manager.register(_StubRenderer())
        app = create_configured_wsgi_app()
        start_response, captured = _capture()
        body_iter = app(_environ("GET", "/"), start_response)
        body = b"".join(body_iter)
        assert captured["status"] is not None
        assert isinstance(body, bytes)


# ── trusted_proxies appliqué AVANT dispatch ─────────────────────────────────


def _build_echo_ip_app() -> Application:
    """Application stub qui renvoie l'IP perçue par la requête."""
    router = Router()

    def echo_ip(request):
        return Response(200, request.ip, content_type="text/plain; charset=utf-8")

    router.add("GET", "/whoami", echo_ip, public=True, csrf=False)
    return Application(router, middlewares=[], api_routes_module=None)


class TestTrustedProxiesAppliedInWsgi:
    def test_x_real_ip_ignored_without_trusted_proxy(self):
        forge.configure(trusted_proxies=frozenset())
        app = create_wsgi_app(_build_echo_ip_app())
        start_response, _ = _capture()
        body = b"".join(app(
            _environ("GET", "/whoami", remote="127.0.0.1",
                     extra={"HTTP_X_REAL_IP": "203.0.113.42"}),
            start_response,
        ))
        assert body == b"127.0.0.1"

    def test_x_real_ip_used_behind_trusted_proxy(self):
        forge.configure(trusted_proxies=frozenset({"127.0.0.1"}))
        app = create_wsgi_app(_build_echo_ip_app())
        start_response, _ = _capture()
        body = b"".join(app(
            _environ("GET", "/whoami", remote="127.0.0.1",
                     extra={"HTTP_X_REAL_IP": "203.0.113.42"}),
            start_response,
        ))
        assert body == b"203.0.113.42"

    def test_invalid_x_real_ip_falls_back(self):
        forge.configure(trusted_proxies=frozenset({"127.0.0.1"}))
        app = create_wsgi_app(_build_echo_ip_app())
        start_response, _ = _capture()
        body = b"".join(app(
            _environ("GET", "/whoami", remote="127.0.0.1",
                     extra={"HTTP_X_REAL_IP": "not-an-ip"}),
            start_response,
        ))
        assert body == b"127.0.0.1"

    def test_configured_factory_propagates_trusted_proxies(self, monkeypatch):
        """create_configured_wsgi_app() doit pousser APP_TRUSTED_PROXIES dans forge."""
        monkeypatch.setenv("APP_TRUSTED_PROXIES", "127.0.0.1, 10.0.0.1")
        # Recharge config.py pour que la factory voie la nouvelle valeur.
        import importlib
        import config
        importlib.reload(config)
        template_manager.register(_StubRenderer())
        create_configured_wsgi_app()
        assert forge.get("trusted_proxies") == frozenset({"127.0.0.1", "10.0.0.1"})


# ── Cohérence config app.py ↔ app_factory ──────────────────────────────────


class TestConfigParity:
    """Les kwargs `forge.configure(...)` de app.py et app_factory sont identiques."""

    @staticmethod
    def _extract_configure_kwargs(source: str) -> set[str]:
        """Liste les kwargs passés à `forge.configure(...)` dans le source."""
        keys: set[str] = set()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = node.func
            name_match = (
                isinstance(target, ast.Attribute)
                and target.attr == "configure"
                and isinstance(target.value, ast.Name)
                and target.value.id == "forge"
            )
            if not name_match:
                continue
            for kw in node.keywords:
                if kw.arg:
                    keys.add(kw.arg)
        return keys

    def test_app_py_and_factory_kwargs_match(self):
        app_keys = self._extract_configure_kwargs(APP_PY.read_text(encoding="utf-8"))
        # On retire `router` : il est posé en seconde passe via une seule
        # ligne dédiée des deux côtés (après chargement des routes).
        app_keys.discard("router")
        factory_keys = set(_forge_config_kwargs())
        missing_in_factory = app_keys - factory_keys
        extra_in_factory = factory_keys - app_keys
        assert not missing_in_factory and not extra_in_factory, (
            f"Divergence forge.configure() app.py ↔ app_factory :\n"
            f"  manquant côté factory : {sorted(missing_in_factory)}\n"
            f"  en trop côté factory  : {sorted(extra_in_factory)}"
        )


# ── Compatibilité API antérieure ────────────────────────────────────────────


class TestLegacyApi:
    def test_create_wsgi_app_still_accepts_application(self):
        app = create_wsgi_app(_build_echo_ip_app())
        assert callable(app)
        start_response, _ = _capture()
        body = b"".join(app(_environ("GET", "/whoami"), start_response))
        assert body  # echo IP non-vide

    def test_app_py_module_still_imports(self):
        import importlib
        mod = importlib.import_module("app")
        assert mod is not None

    def test_app_py_still_calls_forge_configure(self):
        # Sanity : la ligne d'appel n'a pas disparu d'app.py.
        text = APP_PY.read_text(encoding="utf-8")
        assert re.search(r"forge\.configure\s*\(", text), (
            "app.py doit conserver son appel à forge.configure(...)"
        )


# ── build_application : construit bien une Application Forge ────────────────


class TestBuildApplication:
    def test_returns_forge_application(self):
        template_manager.register(_StubRenderer())
        app = build_application()
        assert isinstance(app, Application)

    def test_router_is_registered_in_forge(self):
        template_manager.register(_StubRenderer())
        build_application()
        # Le routeur doit être présent dans forge après build (utile pour url_for).
        assert forge.get("router") is not None
