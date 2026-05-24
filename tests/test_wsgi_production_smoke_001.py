"""Tests — WSGI-PRODUCTION-SMOKE-TESTS-001.

Smoke tests transversaux qui exercent ensemble :

  - `core.wsgi.create_configured_wsgi_app()` (factory configurée) ;
  - `core.app_factory.build_application()` (config + routes + Application) ;
  - `core.http.request.Request` + `resolve_client_ip()` (X-Real-IP) ;
  - `core.prod_warnings.emit_memory_store_warning_if_needed()` (warnings prod).

Les tests individuels existent déjà ; ce fichier sert de garde-fou
d'intégration : si une brique change et casse la cohérence WSGI
production, ce fichier le révèle immédiatement.

Aucun socket réseau, aucune dépendance externe (Gunicorn, etc.).
"""
from __future__ import annotations

import logging
from io import BytesIO

import pytest

import core.forge as forge
from core.application import Application
from core.http.response import Response
from core.http.router import Router
from core.templating.manager import template_manager
from core.wsgi import (
    _WsgiHeaders,
    create_configured_wsgi_app,
    create_wsgi_app,
)


WARNING_TOKEN = "AVERTISSEMENT-PROD"


# ── Fixtures partagées ──────────────────────────────────────────────────────


class _StubRenderer:
    def render(self, template, context):
        return f"[{template}]"


class _FakePersistentStore:
    """Stub minimal — pour le scénario prod + store non mémoire."""


@pytest.fixture(autouse=True)
def _restore_state(monkeypatch):
    """Isole les tests : renderer Jinja, app_env, trusted_proxies, store.

    Le session_store est explicitement remis à `None` au teardown (force
    reset, pas restauration) — voir note dans `test_wsgi_prod_warnings_001`.
    Évite la contamination si un test antérieur a laissé `forge._cfg`
    désynchronisé du `set_session_store()` du manager.
    """
    prev_renderer = template_manager._renderer
    prev_env = forge.get("app_env")
    prev_proxies = forge.get("trusted_proxies")
    template_manager.register(_StubRenderer())
    # Empêche `build_application()` de relire `config.py` et d'écraser les
    # valeurs posées dans les tests prod.
    monkeypatch.setattr("core.app_factory.apply_forge_config", lambda: None)
    yield
    template_manager._renderer = prev_renderer
    forge.configure(app_env=prev_env)
    forge.configure(trusted_proxies=prev_proxies)
    forge.configure(session_store=None)


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


def _build_echo_ip_app() -> Application:
    """Application stub qui renvoie l'IP perçue par la requête."""
    router = Router()

    def echo_ip(request):
        return Response(200, request.ip, content_type="text/plain; charset=utf-8")

    def index(request):
        return Response(200, b"ok")

    router.add("GET", "/", index, public=True, csrf=False)
    router.add("GET", "/whoami", echo_ip, public=True, csrf=False)
    return Application(router, middlewares=[], api_routes_module=None)


def _warning_records(caplog):
    return [
        r for r in caplog.records
        if r.levelno >= logging.WARNING and WARNING_TOKEN in r.getMessage()
    ]


# ── 1. Factory WSGI production callable ─────────────────────────────────────


class TestFactoryReturnsCallable:
    def test_create_configured_wsgi_app_is_callable(self):
        forge.configure(app_env="dev")
        app = create_configured_wsgi_app(emit_prod_warnings=False)
        assert callable(app)


# ── 2. Requête GET minimale ─────────────────────────────────────────────────


class TestMinimalGetRequest:
    def test_status_set_and_body_is_bytes(self):
        forge.configure(app_env="dev")
        app = create_configured_wsgi_app(emit_prod_warnings=False)
        start_response, captured = _capture()
        body = b"".join(app(_environ("GET", "/"), start_response))
        assert captured["status"] is not None
        # Format WSGI : "200 OK", "404 Not Found", …
        assert captured["status"].split(" ", 1)[0].isdigit()
        assert isinstance(body, bytes)


# ── 3-5. Résolution X-Real-IP via la pile WSGI complète ─────────────────────


class TestTrustedProxyResolutionThroughWsgi:
    """Pile complète : create_wsgi_app → Request → resolve_client_ip."""

    def test_real_ip_used_behind_trusted_proxy(self):
        forge.configure(trusted_proxies=frozenset({"127.0.0.1"}))
        app = create_wsgi_app(_build_echo_ip_app())
        start_response, _ = _capture()
        body = b"".join(app(
            _environ("GET", "/whoami", remote="127.0.0.1",
                     extra={"HTTP_X_REAL_IP": "203.0.113.42"}),
            start_response,
        ))
        assert body == b"203.0.113.42"

    def test_real_ip_ignored_without_trusted_proxy(self):
        forge.configure(trusted_proxies=frozenset())
        app = create_wsgi_app(_build_echo_ip_app())
        start_response, _ = _capture()
        body = b"".join(app(
            _environ("GET", "/whoami", remote="127.0.0.1",
                     extra={"HTTP_X_REAL_IP": "203.0.113.42"}),
            start_response,
        ))
        assert body == b"127.0.0.1"

    def test_invalid_real_ip_falls_back_to_remote(self):
        forge.configure(trusted_proxies=frozenset({"127.0.0.1"}))
        app = create_wsgi_app(_build_echo_ip_app())
        start_response, _ = _capture()
        body = b"".join(app(
            _environ("GET", "/whoami", remote="127.0.0.1",
                     extra={"HTTP_X_REAL_IP": "not-an-ip"}),
            start_response,
        ))
        assert body == b"127.0.0.1"


# ── 6-7. Warnings production : émis à la création, pas par requête ──────────


class TestProdWarningsLifecycle:
    def test_warning_emitted_at_factory_call_in_prod(self, caplog):
        caplog.set_level(logging.WARNING)
        forge.configure(app_env="prod", session_store=None)
        create_configured_wsgi_app()
        records = _warning_records(caplog)
        assert len(records) == 1
        msg = records[0].getMessage()
        for token in ("prod", "mémoire", "Sessions"):
            assert token in msg

    def test_no_warning_per_request_after_factory(self, caplog):
        caplog.set_level(logging.WARNING)
        forge.configure(app_env="prod", session_store=None)
        app = create_configured_wsgi_app()
        baseline = len(_warning_records(caplog))
        for _ in range(5):
            start_response, _ = _capture()
            list(app(_environ(), start_response))
        assert len(_warning_records(caplog)) == baseline


# ── 8. create_wsgi_app(application) reste silencieux ────────────────────────


class TestMinimalEntrypointIsSilent:
    def test_create_wsgi_app_does_not_warn_in_prod(self, caplog):
        caplog.set_level(logging.WARNING)
        forge.configure(app_env="prod", session_store=None)
        app = create_wsgi_app(_build_echo_ip_app())
        start_response, _ = _capture()
        list(app(_environ(), start_response))
        assert _warning_records(caplog) == [], (
            "create_wsgi_app(application) ne doit pas émettre de warnings : "
            "l'orchestration revient à create_configured_wsgi_app()."
        )


# ── 9. Cohérence headers WSGI (_WsgiHeaders) ────────────────────────────────


class TestWsgiHeadersAdapter:
    def test_http_prefix_headers_become_dashes_lowercase(self):
        env = {
            "HTTP_X_REAL_IP": "203.0.113.42",
            "HTTP_AUTHORIZATION": "Bearer abc",
            "CONTENT_TYPE": "text/plain",
        }
        headers = _WsgiHeaders(env)
        # Insensible à la casse — interface compatible Request.headers.get
        assert headers.get("X-Real-IP") == "203.0.113.42"
        assert headers.get("x-real-ip") == "203.0.113.42"
        assert headers.get("Authorization") == "Bearer abc"
        assert headers.get("Content-Type") == "text/plain"

    def test_missing_header_returns_default(self):
        headers = _WsgiHeaders({})
        assert headers.get("X-Real-IP") == ""
        assert headers.get("X-Real-IP", "default") == "default"


# ── 10. Non-régression API existante ────────────────────────────────────────


class TestLegacyApiNonRegression:
    """Sanity : les imports publics WSGI restent disponibles."""

    def test_public_callables_importable(self):
        from core.wsgi import (  # noqa: F401
            create_configured_wsgi_app,
            create_wsgi_app,
        )
        from core.app_factory import (  # noqa: F401
            apply_forge_config,
            build_application,
        )
        from core.prod_warnings import (  # noqa: F401
            emit_memory_store_warning_if_needed,
            format_memory_store_warning,
            should_warn_memory_store_in_prod,
        )

    def test_create_configured_wsgi_app_accepts_opt_out(self):
        # Confirme la signature stable : kwargs-only, défauts inchangés.
        forge.configure(app_env="dev")
        app = create_configured_wsgi_app(emit_prod_warnings=False, logger=None)
        assert callable(app)
