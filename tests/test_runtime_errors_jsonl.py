"""
Tests DX-RUNTIME-ERRORS-JSONL-001 — Écriture des erreurs runtime dans errors.dev.jsonl.

Couvre :
- Création de storage/logs/errors.dev.jsonl en mode dev.
- Chaque erreur écrit une seule ligne JSONL valide.
- Champs obligatoires présents et corrects.
- Traceback présent.
- Informations de requête filtrées (post_keys, pas de valeurs sensibles).
- Aucune écriture en mode prod.
- Création du dossier si nécessaire.
- Défaillance d'écriture silencieuse (ne plante pas l'app).
- Absence de fichier Markdown dans ce ticket.
- Intégration via Application.dispatch().
"""
from __future__ import annotations

import json
import pathlib

import pytest

from core.application import Application
from core.http.router import Router
from core.runtime_error_logger import (
    _JSONL_FILENAME,
    _detect_category,
    log_runtime_error,
    set_jsonl_dir,
)
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer
from tests.fake_request import FakeRequest


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture()
def jsonl_dir(tmp_path):
    """Dossier JSONL temporaire, réinitialisé après chaque test."""
    log_dir = tmp_path / "storage" / "logs"
    set_jsonl_dir(log_dir)
    yield log_dir
    set_jsonl_dir(None)


@pytest.fixture()
def views(tmp_path):
    """Arborescence de vues minimale avec templates d'erreur."""
    (tmp_path / "errors").mkdir(parents=True, exist_ok=True)
    (tmp_path / "errors" / "404.html").write_text("404", encoding="utf-8")
    (tmp_path / "errors" / "500.html").write_text("500", encoding="utf-8")
    import core.forge as forge
    forge._cfg["views_dir"] = str(tmp_path)
    template_manager.register(Jinja2Renderer(str(tmp_path)))
    return tmp_path


def _read_jsonl_lines(log_dir: pathlib.Path) -> list[dict]:
    path = log_dir / _JSONL_FILENAME
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _make_app(handler, *, public=True) -> Application:
    router = Router()
    router.add("GET", "/test", handler, public=public)
    return Application(router, middlewares=[])


# ── Tests de création du fichier ───────────────────────────────────────────────

class TestJsonlCreation:
    def test_dev_mode_creates_jsonl_file(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("test error")
        except RuntimeError as exc:
            log_runtime_error(exc)
        assert (jsonl_dir / _JSONL_FILENAME).exists()

    def test_dev_mode_creates_log_dir_if_missing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        deep_dir = tmp_path / "a" / "b" / "c"
        set_jsonl_dir(deep_dir)
        try:
            try:
                raise RuntimeError("test")
            except RuntimeError as exc:
                log_runtime_error(exc)
            assert deep_dir.exists()
        finally:
            set_jsonl_dir(None)

    def test_prod_mode_does_not_create_jsonl_file(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "prod")
        try:
            raise RuntimeError("prod error")
        except RuntimeError as exc:
            log_runtime_error(exc)
        assert not (jsonl_dir / _JSONL_FILENAME).exists()

    def test_markdown_file_created_alongside_jsonl(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("test")
        except RuntimeError as exc:
            log_runtime_error(exc)
        assert (jsonl_dir / "errors.dev.md").exists()


# ── Tests de contenu de la ligne JSONL ────────────────────────────────────────

class TestJsonlContent:
    def test_writes_valid_json_line(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("boom")
        except RuntimeError as exc:
            log_runtime_error(exc)
        lines = _read_jsonl_lines(jsonl_dir)
        assert len(lines) == 1
        assert isinstance(lines[0], dict)

    def test_schema_version_is_1_0(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("x")
        except RuntimeError as exc:
            log_runtime_error(exc)
        event = _read_jsonl_lines(jsonl_dir)[0]
        assert event["schema_version"] == "1.0"

    def test_environment_is_dev(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("x")
        except RuntimeError as exc:
            log_runtime_error(exc)
        event = _read_jsonl_lines(jsonl_dir)[0]
        assert event["environment"] == "dev"

    def test_exception_type_matches(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise TypeError("type incorrect")
        except TypeError as exc:
            log_runtime_error(exc)
        event = _read_jsonl_lines(jsonl_dir)[0]
        assert event["exception_type"] == "TypeError"

    def test_message_matches(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("message d'erreur")
        except RuntimeError as exc:
            log_runtime_error(exc)
        event = _read_jsonl_lines(jsonl_dir)[0]
        assert event["message"] == "message d'erreur"

    def test_safe_for_display_is_false(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("x")
        except RuntimeError as exc:
            log_runtime_error(exc)
        event = _read_jsonl_lines(jsonl_dir)[0]
        assert event["safe_for_display"] is False

    def test_level_is_error(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("x")
        except RuntimeError as exc:
            log_runtime_error(exc)
        event = _read_jsonl_lines(jsonl_dir)[0]
        assert event["level"] == "ERROR"

    def test_required_fields_present(self, jsonl_dir, monkeypatch):
        from core.runtime_errors import REQUIRED_FIELDS
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("x")
        except RuntimeError as exc:
            log_runtime_error(exc)
        event = _read_jsonl_lines(jsonl_dir)[0]
        missing = REQUIRED_FIELDS - set(event.keys())
        assert missing == set(), f"Champs manquants : {missing}"

    def test_traceback_is_present_and_non_empty(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("boom")
        except RuntimeError as exc:
            log_runtime_error(exc)
        event = _read_jsonl_lines(jsonl_dir)[0]
        assert "traceback" in event
        assert isinstance(event["traceback"], list)
        assert len(event["traceback"]) > 0

    def test_location_is_present(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("x")
        except RuntimeError as exc:
            log_runtime_error(exc)
        event = _read_jsonl_lines(jsonl_dir)[0]
        assert "location" in event
        assert "file" in event["location"]
        assert "line" in event["location"]

    def test_line_has_no_newline_inside(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("x")
        except RuntimeError as exc:
            log_runtime_error(exc)
        raw = (jsonl_dir / _JSONL_FILENAME).read_text(encoding="utf-8")
        lines = raw.strip().splitlines()
        assert len(lines) == 1
        assert "\n" not in lines[0]


# ── Tests de la requête filtrée ────────────────────────────────────────────────

class TestRequestFiltering:
    def test_request_info_is_included(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        req = FakeRequest("GET", "/users")
        try:
            raise RuntimeError("x")
        except RuntimeError as exc:
            log_runtime_error(exc, request=req)
        event = _read_jsonl_lines(jsonl_dir)[0]
        assert "request" in event
        assert event["request"]["method"] == "GET"
        assert event["request"]["path"] == "/users"

    def test_post_keys_present_not_values(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        req = FakeRequest("POST", "/login", body={"email": "user@example.com", "password": "secret"})
        try:
            raise RuntimeError("x")
        except RuntimeError as exc:
            log_runtime_error(exc, request=req)
        event = _read_jsonl_lines(jsonl_dir)[0]
        request_info = event.get("request", {})
        post_keys = request_info.get("post_keys", [])
        assert "email" in post_keys
        assert "password" in post_keys
        # Les valeurs ne doivent jamais apparaître
        serialized = json.dumps(event)
        assert "user@example.com" not in serialized
        assert "secret" not in serialized

    def test_sensitive_values_not_written(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        req = FakeRequest("POST", "/api/token", body={
            "api_key": "sk-prod-supersecret",
            "username": "admin",
        })
        try:
            raise RuntimeError("x")
        except RuntimeError as exc:
            log_runtime_error(exc, request=req)
        event = _read_jsonl_lines(jsonl_dir)[0]
        serialized = json.dumps(event)
        assert "sk-prod-supersecret" not in serialized

    def test_no_request_if_none(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("x")
        except RuntimeError as exc:
            log_runtime_error(exc, request=None)
        event = _read_jsonl_lines(jsonl_dir)[0]
        # request peut être absent si non fourni
        if "request" in event:
            assert event["request"]["method"] == ""


# ── Tests des erreurs multiples ────────────────────────────────────────────────

class TestMultipleErrors:
    def test_multiple_errors_produce_multiple_lines(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        for i in range(3):
            try:
                raise RuntimeError(f"erreur {i}")
            except RuntimeError as exc:
                log_runtime_error(exc)
        lines = _read_jsonl_lines(jsonl_dir)
        assert len(lines) == 3

    def test_each_line_is_valid_json(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        for msg in ["alpha", "bêta", "gamma — spécial"]:
            try:
                raise ValueError(msg)
            except ValueError as exc:
                log_runtime_error(exc)
        lines = _read_jsonl_lines(jsonl_dir)
        assert len(lines) == 3
        messages = {e["message"] for e in lines}
        assert "alpha" in messages
        assert "bêta" in messages

    def test_ids_are_unique(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        for _ in range(5):
            try:
                raise RuntimeError("x")
            except RuntimeError as exc:
                log_runtime_error(exc)
        events = _read_jsonl_lines(jsonl_dir)
        ids = [e["id"] for e in events]
        assert len(set(ids)) == len(ids)


# ── Tests de la détection de catégorie ────────────────────────────────────────

class TestCategoryDetection:
    def test_runtime_error_is_runtime_category(self):
        assert _detect_category(RuntimeError("x")) == "runtime"

    def test_value_error_is_runtime_category(self):
        assert _detect_category(ValueError("x")) == "runtime"

    def test_renderer_message_is_configuration(self):
        exc = RuntimeError("Aucun renderer enregistré")
        assert _detect_category(exc) == "configuration"

    def test_routeur_message_is_configuration(self):
        exc = RuntimeError("Aucun routeur actif")
        assert _detect_category(exc) == "configuration"

    def test_jinja2_template_not_found_is_template(self):
        from jinja2 import TemplateNotFound
        exc = TemplateNotFound("base.html")
        assert _detect_category(exc) == "template"

    def test_jinja2_template_syntax_error_is_template(self):
        from jinja2 import TemplateSyntaxError
        exc = TemplateSyntaxError("syntax error", lineno=1)
        assert _detect_category(exc) == "template"


# ── Tests de la résistance aux pannes ─────────────────────────────────────────

class TestFaultTolerance:
    def test_write_failure_does_not_crash_app(self, tmp_path, monkeypatch):
        """Si le dossier est un fichier (non inscriptible), log_runtime_error reste silencieux."""
        monkeypatch.setenv("APP_ENV", "dev")
        # Crée un fichier là où on attend un dossier
        conflict = tmp_path / "storage"
        conflict.write_text("je suis un fichier", encoding="utf-8")
        set_jsonl_dir(conflict / "logs")
        try:
            try:
                raise RuntimeError("écriture impossible")
            except RuntimeError as exc:
                log_runtime_error(exc)  # ne doit pas lever
            # Si on arrive ici, le test passe
        finally:
            set_jsonl_dir(None)

    def test_no_exception_propagated_from_logger(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        raised = False
        try:
            try:
                raise RuntimeError("test")
            except RuntimeError as exc:
                log_runtime_error(exc)
        except Exception:
            raised = True
        assert not raised


# ── Tests d'intégration via Application.dispatch ──────────────────────────────

class TestIntegrationDispatch:
    def test_dispatch_exception_writes_to_jsonl(self, jsonl_dir, views, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")

        def _handler_crash(request):
            raise RuntimeError("erreur contrôleur")

        app = _make_app(_handler_crash)
        resp = app.dispatch(FakeRequest("GET", "/test"))
        assert resp.status == 500

        lines = _read_jsonl_lines(jsonl_dir)
        assert len(lines) == 1
        assert lines[0]["exception_type"] == "RuntimeError"
        assert lines[0]["message"] == "erreur contrôleur"

    def test_dispatch_exception_single_line_per_error(self, jsonl_dir, views, monkeypatch):
        """Une seule ligne JSONL par erreur — pas de doublons."""
        monkeypatch.setenv("APP_ENV", "dev")

        def _handler_crash(request):
            raise ValueError("une seule fois")

        app = _make_app(_handler_crash)
        app.dispatch(FakeRequest("GET", "/test"))
        app.dispatch(FakeRequest("GET", "/test"))

        lines = _read_jsonl_lines(jsonl_dir)
        assert len(lines) == 2  # deux appels → deux lignes, pas quatre

    def test_dispatch_no_write_in_prod(self, jsonl_dir, views, monkeypatch):
        monkeypatch.setenv("APP_ENV", "prod")

        def _handler_crash(request):
            raise RuntimeError("prod error")

        app = _make_app(_handler_crash)
        resp = app.dispatch(FakeRequest("GET", "/test"))
        assert resp.status == 500
        assert not (jsonl_dir / _JSONL_FILENAME).exists()

    def test_dispatch_with_request_info(self, jsonl_dir, views, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")

        def _handler_crash(request):
            raise RuntimeError("x")

        app = _make_app(_handler_crash)
        app.dispatch(FakeRequest("GET", "/test", params={"page": "2"}))

        events = _read_jsonl_lines(jsonl_dir)
        assert len(events) == 1
        assert "request" in events[0]
        assert events[0]["request"]["path"] == "/test"

    def test_dispatch_post_request_keys_filtered(self, jsonl_dir, views, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")

        def _handler_crash(request):
            raise RuntimeError("x")

        router = Router()
        router.add("POST", "/form", _handler_crash, public=True)
        app = Application(router, middlewares=[])
        req = FakeRequest("POST", "/form", body={"username": "alice", "password": "secret123"})

        app.dispatch(req)

        events = _read_jsonl_lines(jsonl_dir)
        assert len(events) == 1
        serialized = json.dumps(events[0])
        assert "secret123" not in serialized
        assert "alice" not in serialized

    def test_404_does_not_write_to_jsonl(self, jsonl_dir, views, monkeypatch):
        """Une 404 n'est pas une erreur runtime — aucune écriture attendue."""
        monkeypatch.setenv("APP_ENV", "dev")
        router = Router()
        app = Application(router, middlewares=[])
        resp = app.dispatch(FakeRequest("GET", "/route-inconnue"))
        assert resp.status == 404
        lines = _read_jsonl_lines(jsonl_dir)
        assert lines == []

    def test_template_not_found_writes_to_jsonl(self, jsonl_dir, views, monkeypatch):
        """Un template introuvable produit une ligne JSONL avec catégorie template."""
        monkeypatch.setenv("APP_ENV", "dev")

        def _handler_missing_tpl(request):
            from core.http.helpers import html
            return html("template_inexistant.html")

        app = _make_app(_handler_missing_tpl)
        resp = app.dispatch(FakeRequest("GET", "/test"))
        assert resp.status == 500

        events = _read_jsonl_lines(jsonl_dir)
        assert len(events) == 1
        assert events[0]["category"] == "template"
