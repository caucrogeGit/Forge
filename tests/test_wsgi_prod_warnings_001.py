"""Tests — WSGI-PROD-WARNINGS-001.

Vérifie que `core.app.wsgi.create_configured_wsgi_app()` émet les warnings
production (`MemorySessionStore` + rate-limits mémoire en `APP_ENV=prod`)
via `core.app.prod_warnings`, exactement une fois au moment de la
construction de l'application — jamais à chaque requête WSGI.

`create_wsgi_app(application)` (entrée WSGI minimale, ticket
`WSGI-ENTRYPOINT-001`) les émet désormais lui aussi, sous les mêmes règles.
Ce partage a été renversé par `WSGI-UNARMED-APP-GUARD-001` (ADR-092) : le point
d'entrée recommandé étant devenu celui qui sert l'application déjà armée,
laisser l'avertissement dans la seule fabrique générique l'aurait fait
disparaître du chemin que tout le monde suit.
"""
from __future__ import annotations

import logging
from io import BytesIO

import pytest

import core.forge as forge
from core.app.application import Application
from core.http.response import Response
from core.http.router import Router
from core.templating.manager import template_manager
from core.app.wsgi import create_configured_wsgi_app, create_wsgi_app


WARNING_TOKEN = "AVERTISSEMENT-PROD"


class _StubRenderer:
    def render(self, template, context):
        return f"[{template}]"


class _FakePersistentStore:
    """Stub minimal — distinct de MemorySessionStore pour les tests prod."""


@pytest.fixture(autouse=True)
def _restore_state():
    """Restaure renderer Jinja, app_env entre tests, force reset du store.

    Le store est explicitement remis à `None` au teardown plutôt que restauré
    à `prev_store` : si un test précédent (ex. `test_configurable_session_store_001`)
    a laissé `forge._cfg["session_store"]` désynchronisé du manager, le
    « restaurer » réinstallerait l'état corrompu via `forge.configure(...)`.
    Forcer `None` garantit un état neutre pour les tests suivants.
    """
    prev_renderer = template_manager._renderer
    prev_env = forge.get("app_env")
    template_manager.register(_StubRenderer())
    yield
    template_manager._renderer = prev_renderer
    forge.configure(session_store=None)
    forge.configure(app_env=prev_env)


@pytest.fixture
def freeze_forge_config(monkeypatch):
    """Empêche `build_application()` de relire `config.py` pendant le test.

    Sans ce gel, `apply_forge_config()` écrase `app_env` et `session_store`
    qu'on a fixés manuellement, et le warning n'est jamais déclenché.
    """
    monkeypatch.setattr("core.app.app_factory.apply_forge_config", lambda: None)


# ── Helpers WSGI ────────────────────────────────────────────────────────────


def _capture():
    captured = {"status": None, "headers": None}

    def start_response(status, headers, exc_info=None):
        captured["status"] = status
        captured["headers"] = headers
        return lambda chunk: None

    return start_response, captured


def _environ(method="GET", path="/"):
    return {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "SERVER_NAME": "test",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": "127.0.0.1",
        "wsgi.input": BytesIO(b""),
        "wsgi.errors": BytesIO(),
        "wsgi.url_scheme": "http",
    }


def _build_dummy_app() -> Application:
    router = Router()
    router.add("GET", "/", lambda r: Response(200, b"ok"), public=True, csrf=False)
    return Application(router, middlewares=[], api_routes_module=None)


def _warning_records(caplog):
    return [
        r for r in caplog.records
        if r.levelno >= logging.WARNING and WARNING_TOKEN in r.getMessage()
    ]


# ── Comportement dev / prod / store persistant ──────────────────────────────


class TestWsgiFactoryEmitsWarningInProdOnly:
    def test_dev_emits_no_warning(self, caplog, monkeypatch):
        caplog.set_level(logging.WARNING)
        monkeypatch.setenv("APP_ENV", "dev")
        # config.py est lu par build_application() via app_factory ; on force
        # app_env directement après la construction pour éviter le reload.
        forge.configure(app_env="dev", session_store=None)
        create_configured_wsgi_app()
        assert _warning_records(caplog) == []

    def test_prod_with_memory_store_emits_warning(self, caplog, freeze_forge_config):
        caplog.set_level(logging.WARNING)
        forge.configure(app_env="prod", session_store=None)
        create_configured_wsgi_app()
        records = _warning_records(caplog)
        assert len(records) == 1
        msg = records[0].getMessage()
        for token in ("prod", "mémoire", "Sessions", "Rate-limit"):
            assert token in msg, f"`{token}` absent du warning : {msg!r}"

    def test_prod_with_persistent_store_does_not_warn(self, caplog, freeze_forge_config, monkeypatch):
        caplog.set_level(logging.WARNING)
        forge.configure(app_env="prod")
        # Le store stub ne satisfait pas le contrat SessionStore complet —
        # on contourne la validation de forge.configure() en posant la clé
        # directement dans _cfg. Ce qui compte ici : `is_memory_session_store`
        # doit renvoyer False, et c'est le seul appel sur la valeur.
        monkeypatch.setitem(forge._cfg, "session_store", _FakePersistentStore())
        create_configured_wsgi_app()
        assert _warning_records(caplog) == []


# ── Une seule émission — pas par requête ────────────────────────────────────


class TestWarningEmittedOnceNotPerRequest:
    def test_no_extra_warning_after_many_requests(self, caplog, freeze_forge_config):
        caplog.set_level(logging.WARNING)
        forge.configure(app_env="prod", session_store=None)
        app = create_configured_wsgi_app()
        before = len(_warning_records(caplog))
        assert before == 1, f"warning attendu à la construction, vu {before} fois"
        for _ in range(5):
            start_response, _ = _capture()
            list(app(_environ(), start_response))
        after = len(_warning_records(caplog))
        assert after == before, (
            f"warning émis à chaque requête ({after - before} ré-émissions)"
        )


# ── opt-out + logger injecté ────────────────────────────────────────────────


class TestOptOutAndCustomLogger:
    def test_emit_prod_warnings_false_silences_everything(self, caplog):
        caplog.set_level(logging.WARNING)
        create_configured_wsgi_app(emit_prod_warnings=False)
        forge.configure(app_env="prod", session_store=None)
        create_configured_wsgi_app(emit_prod_warnings=False)
        assert _warning_records(caplog) == []

    def test_custom_logger_receives_warning(self, freeze_forge_config):
        seen: list[str] = []
        custom = logging.getLogger("forge.test.wsgi_prod_warnings")
        handler = logging.Handler()
        handler.emit = lambda r: seen.append(r.getMessage())
        custom.addHandler(handler)
        custom.setLevel(logging.WARNING)
        try:
            forge.configure(app_env="prod", session_store=None)
            create_configured_wsgi_app(logger=custom)
        finally:
            custom.removeHandler(handler)
        assert any(WARNING_TOKEN in m for m in seen)


# ── Cohérence avec create_wsgi_app (entrée minimale) ────────────────────────


class TestMinimalEntrypointWarnsToo:
    """Contrat renversé par WSGI-UNARMED-APP-GUARD-001 (ADR-092).

    `create_wsgi_app` se taisait, la responsabilité revenant à
    `create_configured_wsgi_app`. Ce partage a cessé d'avoir un sens le jour où
    le point d'entrée recommandé est devenu celui qui sert l'application déjà
    armée : l'avertissement aurait disparu du chemin que tout le monde suit,
    sans que personne le remarque.

    Ce qui comptait vraiment dans l'ancien test est conservé : l'émission a lieu
    UNE fois, à la construction, et jamais par requête.
    """

    def test_create_wsgi_app_emet_a_la_construction(self, caplog):
        caplog.set_level(logging.WARNING)
        forge.configure(app_env="prod", session_store=None)

        create_wsgi_app(_build_dummy_app())

        assert len(_warning_records(caplog)) == 1

    def test_aucune_emission_par_requete(self, caplog):
        """Le point qui comptait dans l'ancien contrat, et qui tient toujours."""
        forge.configure(app_env="prod", session_store=None)
        app = create_wsgi_app(_build_dummy_app())

        caplog.clear()
        caplog.set_level(logging.WARNING)
        for _ in range(3):
            start_response, _ = _capture()
            list(app(_environ(), start_response))

        assert _warning_records(caplog) == []

    def test_emission_desactivable_pour_les_tests(self, caplog):
        caplog.set_level(logging.WARNING)
        forge.configure(app_env="prod", session_store=None)

        create_wsgi_app(_build_dummy_app(), emit_prod_warnings=False)

        assert _warning_records(caplog) == []

    def test_pas_de_double_emission_par_la_fabrique(self, caplog, freeze_forge_config):
        """`create_configured_wsgi_app` délègue : une émission, pas deux."""
        caplog.set_level(logging.WARNING)
        forge.configure(app_env="prod", session_store=None)

        create_configured_wsgi_app()

        assert len(_warning_records(caplog)) == 1


# ── App reste fonctionnelle après émission ──────────────────────────────────


class TestAppStillFunctional:
    def test_callable_responds_after_warning(self, freeze_forge_config):
        forge.configure(app_env="prod", session_store=None)
        app = create_configured_wsgi_app()
        start_response, captured = _capture()
        body = b"".join(app(_environ(), start_response))
        assert captured["status"] is not None
        assert isinstance(body, bytes)
@pytest.fixture(autouse=True)
def _fixture_app_project(monkeypatch):
    """ADR-044 : expose la fixture d'application (tests/fixtures/app) comme
    projet importable (config, mvc.routes) pour les tests core factory/WSGI."""
    import sys
    from pathlib import Path as _P

    _app = _P(__file__).resolve().parent / "fixtures" / "app"
    monkeypatch.syspath_prepend(str(_app))
    monkeypatch.setenv("VIEWS_DIR", str(_app / "mvc" / "views"))
    monkeypatch.setenv("APP_ROUTES_MODULE", "mvc.routes")
    yield
    for _m in [m for m in list(sys.modules) if m == "config" or m == "mvc" or m.startswith("mvc.")]:
        sys.modules.pop(_m, None)
