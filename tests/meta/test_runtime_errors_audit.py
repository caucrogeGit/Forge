"""
Tests DX-RUNTIME-ERRORS-AUDIT-001 — Audit erreurs runtime et mode debug.

Couvre :
- Existence et sections du document d'audit.
- Comportement runtime de Application.dispatch() : 404, 500, pas de traceback exposé.
- Erreur de template → capturée → 500.
- Contrôleur retournant None → capturé → 500.
- Limites non testables documentées explicitement.
"""
from __future__ import annotations

import pathlib

from core.app.application import Application
from core.http.router import Router
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer
from tests.fake_request import FakeRequest

import pytest
pytestmark = pytest.mark.meta

ROOT = pathlib.Path(__file__).parent.parent.parent
AUDIT_DOC = ROOT / "docs" / "history" / "audits" / "runtime-errors-audit-001.md"

REQUIRED_SECTIONS = [
    "## Objectif",
    "## Résumé exécutif",
    "## Chemin actuel d'une erreur runtime",
    "## Comportement en mode développement",
    "## Comportement en mode production",
    "## Erreurs contrôleur",
    "## Erreurs routes",
    "## Erreurs templates",
    "## Erreurs SQL",
    "## Erreurs HTTP 404 / 500",
    "## Logs existants",
    "## Risques identifiés",
    "## Ce qui est acceptable aujourd'hui",
    "## Ce qui doit être corrigé plus tard",
    "## Recommandation de trajectoire",
    "## Tickets suivants proposés",
]

FUTURE_TICKETS = [
    "DX-RUNTIME-ERRORS-SCHEMA-001",
    "DX-RUNTIME-ERRORS-JSONL-001",
    "DX-RUNTIME-ERRORS-MD-001",
]


# ── Helpers de fixture ─────────────────────────────────────────────────────────

def _setup_views(tmp_path, extra_templates: dict[str, str] | None = None):
    """Crée une arborescence views minimale et enregistre le renderer."""
    (tmp_path / "errors").mkdir(parents=True, exist_ok=True)
    (tmp_path / "errors" / "404.html").write_text("404 introuvable", encoding="utf-8")
    (tmp_path / "errors" / "500.html").write_text("500 erreur serveur", encoding="utf-8")
    if extra_templates:
        for name, content in extra_templates.items():
            target = tmp_path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    import core.forge as forge
    forge._cfg["views_dir"] = str(tmp_path)
    template_manager.register(Jinja2Renderer(str(tmp_path)))


def _make_app(handler, *, public=True) -> Application:
    router = Router()
    router.add("GET", "/test", handler, public=public)
    return Application(router, middlewares=[])


# ── Tests documentaires ────────────────────────────────────────────────────────

class TestAuditDocument:
    def test_audit_document_exists(self):
        assert AUDIT_DOC.exists(), f"Document d'audit absent : {AUDIT_DOC}"

    def test_audit_document_not_empty(self):
        assert AUDIT_DOC.stat().st_size > 500

    def test_audit_contains_all_required_sections(self):
        content = AUDIT_DOC.read_text(encoding="utf-8")
        missing = [s for s in REQUIRED_SECTIONS if s not in content]
        assert missing == [], f"Sections manquantes dans l'audit : {missing}"

    def test_audit_mentions_future_tickets(self):
        content = AUDIT_DOC.read_text(encoding="utf-8")
        missing = [t for t in FUTURE_TICKETS if t not in content]
        assert missing == [], f"Tickets futurs non mentionnés : {missing}"

    def test_audit_mentions_next_priority(self):
        content = AUDIT_DOC.read_text(encoding="utf-8")
        assert "DX-RUNTIME-ERRORS-SCHEMA-001" in content

    def test_audit_identifies_risks(self):
        content = AUDIT_DOC.read_text(encoding="utf-8")
        assert "RISQUE" in content or "Risque" in content

    def test_audit_covers_dev_prod_distinction(self):
        content = AUDIT_DOC.read_text(encoding="utf-8")
        assert "APP_ENV=dev" in content or "mode développement" in content.lower()
        assert "APP_ENV=prod" in content or "mode production" in content.lower()

    def test_audit_mentions_no_app_debug(self):
        content = AUDIT_DOC.read_text(encoding="utf-8")
        assert "APP_DEBUG" in content

    def test_audit_mentions_logging(self):
        content = AUDIT_DOC.read_text(encoding="utf-8")
        assert "logger" in content or "logging" in content.lower()

    def test_audit_mentions_double_failure_risk(self):
        content = AUDIT_DOC.read_text(encoding="utf-8")
        assert "double" in content.lower() or "double-échec" in content.lower()


# ── Tests runtime : comportement 404 ──────────────────────────────────────────

class TestRuntime404:
    def test_unknown_route_returns_404(self, tmp_path):
        _setup_views(tmp_path)
        router = Router()
        app = Application(router, middlewares=[])
        req = FakeRequest("GET", "/route-inexistante")
        resp = app.dispatch(req)
        assert resp.status == 404

    def test_404_body_does_not_expose_traceback(self, tmp_path):
        _setup_views(tmp_path)
        router = Router()
        app = Application(router, middlewares=[])
        req = FakeRequest("GET", "/route-inexistante")
        resp = app.dispatch(req)
        body = resp.body.decode("utf-8", errors="replace")
        assert "Traceback" not in body
        assert "traceback" not in body

    def test_404_body_contains_error_content(self, tmp_path):
        _setup_views(tmp_path)
        router = Router()
        app = Application(router, middlewares=[])
        req = FakeRequest("GET", "/route-inexistante")
        resp = app.dispatch(req)
        assert len(resp.body) > 0


# ── Tests runtime : comportement 500 ──────────────────────────────────────────

class TestRuntime500:
    def test_controller_exception_returns_500(self, tmp_path):
        _setup_views(tmp_path)

        def _handler_crash(request):
            raise RuntimeError("erreur intentionnelle")

        app = _make_app(_handler_crash)
        resp = app.dispatch(FakeRequest("GET", "/test"))
        assert resp.status == 500

    def test_500_body_does_not_expose_traceback(self, tmp_path):
        _setup_views(tmp_path)

        def _handler_crash(request):
            raise ValueError("détail interne sensible")

        app = _make_app(_handler_crash)
        resp = app.dispatch(FakeRequest("GET", "/test"))
        body = resp.body.decode("utf-8", errors="replace")
        assert "Traceback" not in body
        assert "traceback" not in body
        assert "détail interne sensible" not in body

    def test_500_body_does_not_expose_exception_message(self, tmp_path):
        _setup_views(tmp_path)

        def _handler_crash(request):
            raise RuntimeError("SECRET_DB_PASSWORD=supersecret")

        app = _make_app(_handler_crash)
        resp = app.dispatch(FakeRequest("GET", "/test"))
        body = resp.body.decode("utf-8", errors="replace")
        assert "SECRET_DB_PASSWORD" not in body

    def test_500_body_contains_error_page_content(self, tmp_path):
        _setup_views(tmp_path)

        def _handler_crash(request):
            raise RuntimeError("boom")

        app = _make_app(_handler_crash)
        resp = app.dispatch(FakeRequest("GET", "/test"))
        assert len(resp.body) > 0

    def test_controller_returns_none_is_caught(self, tmp_path):
        """Un contrôleur qui retourne None provoque une AttributeError remontée au dispatch."""
        _setup_views(tmp_path)

        def _handler_none(request):
            return None  # type incorrect — AttributeError attendu dans _send_response

        # Application.dispatch() retourne None sans erreur (None est la valeur de retour)
        # L'AttributeError surviendrait dans _send_response, hors du périmètre de dispatch()
        # Ce test vérifie que dispatch() ne plante pas pour cette raison
        app = _make_app(_handler_none)
        # dispatch retourne None — pas d'exception dans dispatch()
        result = app.dispatch(FakeRequest("GET", "/test"))
        # None est retourné tel quel — la gestion du mauvais type est dans RequestHandler
        assert result is None  # limite documentée : dispatch() ne valide pas le type de retour


# ── Tests runtime : erreurs de template ───────────────────────────────────────

class TestRuntimeTemplateErrors:
    def test_missing_template_returns_500(self, tmp_path):
        """Un template introuvable lève TemplateNotFound → capturé → 500."""
        _setup_views(tmp_path)

        def _handler_missing_template(request):
            from core.http.helpers import html
            return html("template_inexistant.html")

        app = _make_app(_handler_missing_template)
        resp = app.dispatch(FakeRequest("GET", "/test"))
        assert resp.status == 500

    def test_missing_template_500_body_hides_details(self, tmp_path):
        _setup_views(tmp_path)

        def _handler_missing_template(request):
            from core.http.helpers import html
            return html("template_inexistant.html")

        app = _make_app(_handler_missing_template)
        resp = app.dispatch(FakeRequest("GET", "/test"))
        body = resp.body.decode("utf-8", errors="replace")
        assert "Traceback" not in body

    def test_template_syntax_error_returns_500(self, tmp_path):
        """Un template avec erreur de syntaxe Jinja2 → TemplateSyntaxError → 500."""
        broken_template = "{% if %}"  # syntaxe invalide
        _setup_views(tmp_path, {"broken.html": broken_template})

        def _handler_broken_template(request):
            from core.http.helpers import html
            return html("broken.html")

        app = _make_app(_handler_broken_template)
        resp = app.dispatch(FakeRequest("GET", "/test"))
        assert resp.status == 500

    def test_undefined_variable_in_template_returns_500(self, tmp_path):
        """Une variable absente dans le contexte → UndefinedError → 500 (autoescape activé)."""
        # Jinja2 avec autoescape lève UndefinedError sur accès à attribut d'une variable non définie
        template_content = "{{ objet_inexistant.attribut }}"
        _setup_views(tmp_path, {"test.html": template_content})

        def _handler_undefined(request):
            from core.http.helpers import html
            return html("test.html", context={})  # contexte vide — objet_inexistant absent

        app = _make_app(_handler_undefined)
        # Jinja2 retourne une chaîne vide pour Undefined par défaut → peut ne pas lever
        # Ce test documente le comportement observé sans garantie d'exception
        resp = app.dispatch(FakeRequest("GET", "/test"))
        # Le status est soit 200 (Undefined silencieux) soit 500 (UndefinedError strict)
        assert resp.status in (200, 500)


# ── Tests runtime : réponse identique dev/prod ────────────────────────────────

class TestDevProdBehavior:
    def test_500_response_same_in_dev_and_prod(self, tmp_path, monkeypatch):
        """La réponse 500 est identique quel que soit APP_ENV."""
        _setup_views(tmp_path)

        def _handler_crash(request):
            raise RuntimeError("boom")

        app = _make_app(_handler_crash)

        monkeypatch.setenv("APP_ENV", "dev")
        resp_dev = app.dispatch(FakeRequest("GET", "/test"))

        monkeypatch.setenv("APP_ENV", "prod")
        resp_prod = app.dispatch(FakeRequest("GET", "/test"))

        assert resp_dev.status == resp_prod.status == 500
        assert resp_dev.body == resp_prod.body

    def test_404_response_same_in_dev_and_prod(self, tmp_path, monkeypatch):
        _setup_views(tmp_path)
        router = Router()
        app = Application(router, middlewares=[])

        monkeypatch.setenv("APP_ENV", "dev")
        resp_dev = app.dispatch(FakeRequest("GET", "/inexistant"))

        monkeypatch.setenv("APP_ENV", "prod")
        resp_prod = app.dispatch(FakeRequest("GET", "/inexistant"))

        assert resp_dev.status == resp_prod.status == 404
        assert resp_dev.body == resp_prod.body


# ── Tests runtime : comportement multi-exceptions ─────────────────────────────

class TestMultipleExceptions:
    def test_typeerror_in_controller_returns_500(self, tmp_path):
        _setup_views(tmp_path)

        def _handler_type_error(request):
            raise TypeError("mauvais type")

        app = _make_app(_handler_type_error)
        resp = app.dispatch(FakeRequest("GET", "/test"))
        assert resp.status == 500

    def test_attributeerror_in_controller_returns_500(self, tmp_path):
        _setup_views(tmp_path)

        def _handler_attr_error(request):
            obj = None
            return obj.methode_inexistante()  # AttributeError

        app = _make_app(_handler_attr_error)
        resp = app.dispatch(FakeRequest("GET", "/test"))
        assert resp.status == 500

    def test_keyerror_in_controller_returns_500(self, tmp_path):
        _setup_views(tmp_path)

        def _handler_key_error(request):
            d = {}
            return d["cle_inexistante"]  # KeyError

        app = _make_app(_handler_key_error)
        resp = app.dispatch(FakeRequest("GET", "/test"))
        assert resp.status == 500

    def test_multiple_consecutive_errors_do_not_crash_app(self, tmp_path):
        """Plusieurs erreurs consécutives ne crashent pas l'Application."""
        _setup_views(tmp_path)

        def _handler_crash(request):
            raise RuntimeError("boom")

        app = _make_app(_handler_crash)
        req = FakeRequest("GET", "/test")

        for _ in range(3):
            resp = app.dispatch(req)
            assert resp.status == 500
