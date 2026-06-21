"""Tests DX-DEV-500-ERROR-001 — la page 500 affiche la cause en APP_ENV=dev.

En mode dev, la page d'erreur 500 affiche le type, le message et la trace de
l'exception qui l'a provoquee, pour aider le developpeur. En prod, rien de tout
cela n'est expose (aucune fuite de trace).
"""
from __future__ import annotations

import pytest

import core.forge as forge
from core.app.application import Application
from core.errors.runtime_error_logger import build_dev_error_context
from core.http.router import Router
from core.security import session as _sessions  # noqa: F401 (parite setup)
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer
from forge_mvc_testing import FakeRequest


_500_WITH_BLOCK = (
    "<!DOCTYPE html><html><body>"
    "<p>500</p>"
    "{% if error %}"
    "<div><p>{{ error.type }}</p><p>{{ error.message }}</p>"
    "<pre>{{ error.traceback }}</pre></div>"
    "{% endif %}"
    "</body></html>"
)


@pytest.fixture
def restore_app_env():
    original = forge._cfg.get("app_env")
    yield
    forge._cfg["app_env"] = original


def _boom(request):
    raise RuntimeError("boom intentionnel")


def _setup_app(tmp_path):
    (tmp_path / "errors").mkdir(exist_ok=True)
    (tmp_path / "errors" / "500.html").write_text(_500_WITH_BLOCK, encoding="utf-8")
    forge._cfg["views_dir"] = str(tmp_path)
    template_manager.register(Jinja2Renderer(str(tmp_path)))
    router = Router()
    router.add("GET", "/boom", _boom, public=True)
    return Application(router, middlewares=[])


# --- build_dev_error_context (unite) ------------------------------------------


def test_context_en_dev_contient_type_message_et_trace(restore_app_env):
    forge._cfg["app_env"] = "dev"
    try:
        raise ValueError("quelque chose a casse")
    except ValueError as exc:
        ctx = build_dev_error_context(exc)
    assert ctx is not None
    assert ctx["error"]["type"] == "ValueError"
    assert ctx["error"]["message"] == "quelque chose a casse"
    assert "ValueError" in ctx["error"]["traceback"]
    assert "Traceback" in ctx["error"]["traceback"]


def test_context_en_prod_retourne_none(restore_app_env):
    forge._cfg["app_env"] = "prod"
    try:
        raise ValueError("secret interne")
    except ValueError as exc:
        ctx = build_dev_error_context(exc)
    assert ctx is None


def test_context_none_si_environnement_indeterminable(restore_app_env, monkeypatch):
    # forge.get casse ET APP_ENV absent -> on n'expose rien (securise par defaut).
    monkeypatch.setattr(forge, "get", lambda *_a, **_k: (_ for _ in ()).throw(KeyError()))
    monkeypatch.delenv("APP_ENV", raising=False)
    try:
        raise ValueError("x")
    except ValueError as exc:
        assert build_dev_error_context(exc) is None


# --- Integration via le dispatcher --------------------------------------------


def test_page_500_affiche_l_erreur_en_dev(tmp_path, restore_app_env):
    forge._cfg["app_env"] = "dev"
    app = _setup_app(tmp_path)
    resp = app.dispatch(FakeRequest("GET", "/boom"))
    body = resp.body.decode("utf-8")
    assert resp.status == 500
    assert "RuntimeError" in body
    assert "boom intentionnel" in body


def test_page_500_n_expose_rien_en_prod(tmp_path, restore_app_env):
    forge._cfg["app_env"] = "prod"
    app = _setup_app(tmp_path)
    resp = app.dispatch(FakeRequest("GET", "/boom"))
    body = resp.body.decode("utf-8")
    assert resp.status == 500
    assert "boom intentionnel" not in body
    assert "RuntimeError" not in body


def test_trace_html_est_echappee_en_dev(tmp_path, restore_app_env):
    # Le message d'erreur contenant du HTML doit etre echappe (pas d'injection).
    def _boom_html(request):
        raise RuntimeError("<script>alert(1)</script>")

    forge._cfg["app_env"] = "dev"
    (tmp_path / "errors").mkdir(exist_ok=True)
    (tmp_path / "errors" / "500.html").write_text(_500_WITH_BLOCK, encoding="utf-8")
    forge._cfg["views_dir"] = str(tmp_path)
    template_manager.register(Jinja2Renderer(str(tmp_path)))
    router = Router()
    router.add("GET", "/boom", _boom_html, public=True)
    app = Application(router, middlewares=[])

    resp = app.dispatch(FakeRequest("GET", "/boom"))
    body = resp.body.decode("utf-8")
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;" in body
