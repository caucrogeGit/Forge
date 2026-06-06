"""
Tests DX-RUNTIME-ERRORS-MD-001 — Génération de errors.dev.md depuis errors.dev.jsonl.

Couvre :
- load_error_events_from_jsonl : fichier absent, vide, valide, invalide, mixte.
- render_error_event_markdown : événement minimal, complet, ligne invalide.
- render_errors_markdown : titre, source canonique, résumé, séparateurs.
- write_errors_markdown : création du fichier MD, JSONL non modifié.
- Sécurité : pas de valeurs POST sensibles dans le Markdown.
- Intégration : une erreur runtime produit JSONL + MD en mode dev.
- Pas de génération MD en mode prod.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from core.errors.runtime_error_markdown import (
    _MD_FILENAME,
    load_error_events_from_jsonl,
    render_error_event_markdown,
    render_errors_markdown,
    write_errors_markdown,
)
from core.errors.runtime_error_logger import (
    _JSONL_FILENAME,
    log_runtime_error,
    set_jsonl_dir,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

@pytest.fixture()
def jsonl_dir(tmp_path):
    log_dir = tmp_path / "storage" / "logs"
    set_jsonl_dir(log_dir)
    yield log_dir
    set_jsonl_dir(None)


def _minimal_event(**kwargs) -> dict:
    base = {
        "schema_version": "1.0",
        "id": "err_20260509_094200_8f3a",
        "timestamp": "2026-05-09T07:42:00+00:00",
        "environment": "dev",
        "level": "ERROR",
        "category": "runtime",
        "exception_type": "RuntimeError",
        "message": "boom",
        "safe_for_display": False,
    }
    base.update(kwargs)
    return base


def _full_event() -> dict:
    return {
        **_minimal_event(exception_type="TypeError", message="index() missing argument",
                         category="controller"),
        "request": {
            "method": "GET",
            "path": "/users",
            "query": "page=1",
            "post_keys": [],
            "headers": ["Host", "User-Agent"],
        },
        "location": {
            "file": "mvc/controllers/user_controller.py",
            "line": 42,
            "function": "index",
        },
        "traceback": [
            {"file": "app.py", "line": 88, "function": "dispatch"},
            {"file": "mvc/controllers/user_controller.py", "line": 42, "function": "index"},
        ],
        "hint": "Vérifier la signature de la méthode.",
    }


def _write_jsonl(path: pathlib.Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")


# ── Tests de load_error_events_from_jsonl ─────────────────────────────────────

class TestLoadErrorEvents:
    def test_absent_file_returns_empty_list(self, tmp_path):
        path = tmp_path / "missing.jsonl"
        assert load_error_events_from_jsonl(path) == []

    def test_empty_file_returns_empty_list(self, tmp_path):
        path = tmp_path / "empty.jsonl"
        path.write_text("", encoding="utf-8")
        assert load_error_events_from_jsonl(path) == []

    def test_blank_lines_ignored(self, tmp_path):
        path = tmp_path / "blanks.jsonl"
        path.write_text('\n\n{"id":"x"}\n\n', encoding="utf-8")
        events = load_error_events_from_jsonl(path)
        assert len(events) == 1
        assert events[0]["id"] == "x"

    def test_valid_lines_loaded(self, tmp_path):
        path = tmp_path / "valid.jsonl"
        _write_jsonl(path, [_minimal_event(), _minimal_event(id="err_b")])
        events = load_error_events_from_jsonl(path)
        assert len(events) == 2

    def test_invalid_json_line_marked(self, tmp_path):
        path = tmp_path / "invalid.jsonl"
        path.write_text('not json\n', encoding="utf-8")
        events = load_error_events_from_jsonl(path)
        assert len(events) == 1
        assert "_invalid_line" in events[0]
        assert events[0]["_invalid_line"] == 1

    def test_mixed_valid_invalid(self, tmp_path):
        path = tmp_path / "mixed.jsonl"
        path.write_text(
            json.dumps({"id": "ok"}) + "\n"
            + "not-json\n"
            + json.dumps({"id": "ok2"}) + "\n",
            encoding="utf-8",
        )
        events = load_error_events_from_jsonl(path)
        assert len(events) == 3
        assert "_invalid_line" in events[1]
        assert events[0]["id"] == "ok"
        assert events[2]["id"] == "ok2"

    def test_jsonl_not_modified(self, tmp_path):
        path = tmp_path / "data.jsonl"
        original = json.dumps({"id": "x"}) + "\n"
        path.write_text(original, encoding="utf-8")
        load_error_events_from_jsonl(path)
        assert path.read_text(encoding="utf-8") == original


# ── Tests de render_error_event_markdown ──────────────────────────────────────

class TestRenderErrorEvent:
    def test_invalid_line_renders_warning(self):
        event = {"_invalid_line": 5, "_raw": "garbage"}
        md = render_error_event_markdown(event)
        assert "invalide" in md.lower() or "⚠" in md
        assert "5" in md

    def test_minimal_event_contains_id(self):
        md = render_error_event_markdown(_minimal_event())
        assert "err_20260509_094200_8f3a" in md

    def test_minimal_event_contains_exception_type(self):
        md = render_error_event_markdown(_minimal_event())
        assert "RuntimeError" in md

    def test_minimal_event_contains_timestamp(self):
        md = render_error_event_markdown(_minimal_event())
        assert "2026-05-09" in md

    def test_minimal_event_contains_message(self):
        md = render_error_event_markdown(_minimal_event())
        assert "boom" in md

    def test_full_event_contains_request_section(self):
        md = render_error_event_markdown(_full_event())
        assert "Requête" in md or "requête" in md.lower()
        assert "/users" in md

    def test_full_event_contains_location(self):
        md = render_error_event_markdown(_full_event())
        assert "mvc/controllers/user_controller.py" in md
        assert "42" in md

    def test_full_event_contains_traceback(self):
        md = render_error_event_markdown(_full_event())
        assert "Traceback" in md or "traceback" in md.lower()
        assert "app.py" in md

    def test_full_event_contains_hint(self):
        md = render_error_event_markdown(_full_event())
        assert "Vérifier la signature" in md

    def test_post_keys_listed_not_values(self):
        event = _minimal_event()
        event["request"] = {
            "method": "POST",
            "path": "/login",
            "query": "",
            "post_keys": ["email", "password"],
        }
        md = render_error_event_markdown(event)
        assert "email" in md
        assert "password" in md  # nom du champ — attendu
        # les valeurs ne sont pas dans l'event, donc pas dans le MD
        assert "secret123" not in md

    def test_safe_for_display_false_shown(self):
        md = render_error_event_markdown(_minimal_event(safe_for_display=False))
        assert "false" in md

    def test_safe_for_display_true_shown(self):
        md = render_error_event_markdown(_minimal_event(safe_for_display=True))
        assert "true" in md

    def test_no_hint_section_when_absent(self):
        md = render_error_event_markdown(_minimal_event())
        assert "Piste" not in md or "hint" not in md.lower()

    def test_no_request_section_when_absent(self):
        md = render_error_event_markdown(_minimal_event())
        assert "Requête" not in md


# ── Tests de render_errors_markdown ───────────────────────────────────────────

class TestRenderErrorsMarkdown:
    def test_contains_title(self):
        md = render_errors_markdown([_minimal_event()])
        assert "# Erreurs runtime Forge" in md

    def test_contains_canonical_source_reference(self):
        md = render_errors_markdown([_minimal_event()])
        assert "errors.dev.jsonl" in md

    def test_contains_do_not_edit_notice(self):
        md = render_errors_markdown([_minimal_event()])
        assert "Ne pas modifier" in md or "ne pas modifier" in md.lower()

    def test_contains_error_count(self):
        events = [_minimal_event(), _minimal_event(id="err_2")]
        md = render_errors_markdown(events)
        assert "2" in md

    def test_error_count_excludes_invalid_lines(self):
        events = [_minimal_event(), {"_invalid_line": 2, "_raw": "bad"}]
        md = render_errors_markdown(events)
        assert "Erreurs listées : 1" in md

    def test_last_error_timestamp_present(self):
        events = [_minimal_event(timestamp="2026-05-09T08:00:00+00:00")]
        md = render_errors_markdown(events)
        assert "2026-05-09" in md

    def test_multiple_events_all_rendered(self):
        events = [_minimal_event(id="err_a"), _minimal_event(id="err_b")]
        md = render_errors_markdown(events)
        assert "err_a" in md
        assert "err_b" in md

    def test_invalid_line_warning_present_in_output(self):
        events = [_minimal_event(), {"_invalid_line": 3, "_raw": "not-json"}]
        md = render_errors_markdown(events)
        assert "invalide" in md.lower() or "⚠" in md

    def test_no_sensitive_values_in_output(self):
        event = _minimal_event()
        event["request"] = {
            "method": "POST",
            "path": "/api",
            "query": "",
            "post_keys": ["api_key", "token"],
        }
        md = render_errors_markdown([event])
        assert "sk-secret" not in md
        assert "eyJhbGci" not in md


# ── Tests de write_errors_markdown ────────────────────────────────────────────

class TestWriteErrorsMarkdown:
    def test_creates_markdown_file(self, tmp_path):
        jsonl = tmp_path / "errors.dev.jsonl"
        md    = tmp_path / "errors.dev.md"
        _write_jsonl(jsonl, [_minimal_event()])
        write_errors_markdown(jsonl, md)
        assert md.exists()

    def test_markdown_file_is_utf8(self, tmp_path):
        jsonl = tmp_path / "errors.dev.jsonl"
        md    = tmp_path / "errors.dev.md"
        _write_jsonl(jsonl, [_minimal_event(message="Erreur — spéciale")])
        write_errors_markdown(jsonl, md)
        content = md.read_text(encoding="utf-8")
        assert "Erreur — spéciale" in content

    def test_empty_jsonl_no_markdown_created(self, tmp_path):
        jsonl = tmp_path / "empty.jsonl"
        jsonl.write_text("", encoding="utf-8")
        md = tmp_path / "errors.dev.md"
        write_errors_markdown(jsonl, md)
        assert not md.exists()

    def test_absent_jsonl_no_markdown_created(self, tmp_path):
        jsonl = tmp_path / "missing.jsonl"
        md    = tmp_path / "errors.dev.md"
        write_errors_markdown(jsonl, md)
        assert not md.exists()

    def test_jsonl_not_modified_after_write_md(self, tmp_path):
        jsonl = tmp_path / "data.jsonl"
        _write_jsonl(jsonl, [_minimal_event()])
        original = jsonl.read_text(encoding="utf-8")
        md = tmp_path / "errors.dev.md"
        write_errors_markdown(jsonl, md)
        assert jsonl.read_text(encoding="utf-8") == original

    def test_creates_parent_dir_if_missing(self, tmp_path):
        jsonl = tmp_path / "data.jsonl"
        md    = tmp_path / "deep" / "nested" / "errors.dev.md"
        _write_jsonl(jsonl, [_minimal_event()])
        write_errors_markdown(jsonl, md)
        assert md.exists()

    def test_overwrites_existing_markdown(self, tmp_path):
        jsonl = tmp_path / "data.jsonl"
        md    = tmp_path / "errors.dev.md"
        md.write_text("ancien contenu", encoding="utf-8")
        _write_jsonl(jsonl, [_minimal_event(message="nouveau message")])
        write_errors_markdown(jsonl, md)
        content = md.read_text(encoding="utf-8")
        assert "nouveau message" in content
        assert "ancien contenu" not in content


# ── Tests d'intégration via log_runtime_error ─────────────────────────────────

class TestIntegrationMarkdown:
    def test_runtime_error_creates_both_files(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("erreur intégration")
        except RuntimeError as exc:
            log_runtime_error(exc)
        assert (jsonl_dir / _JSONL_FILENAME).exists()
        assert (jsonl_dir / _MD_FILENAME).exists()

    def test_md_contains_exception_type(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise TypeError("type invalide")
        except TypeError as exc:
            log_runtime_error(exc)
        md_content = (jsonl_dir / _MD_FILENAME).read_text(encoding="utf-8")
        assert "TypeError" in md_content

    def test_md_is_valid_utf8(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("Erreur — avec accents et é")
        except RuntimeError as exc:
            log_runtime_error(exc)
        content = (jsonl_dir / _MD_FILENAME).read_text(encoding="utf-8")
        assert "Erreur" in content

    def test_prod_mode_no_md_file(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "prod")
        try:
            raise RuntimeError("prod error")
        except RuntimeError as exc:
            log_runtime_error(exc)
        assert not (jsonl_dir / _MD_FILENAME).exists()

    def test_md_rebuilt_on_each_error(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("première erreur")
        except RuntimeError as exc:
            log_runtime_error(exc)
        try:
            raise ValueError("deuxième erreur")
        except ValueError as exc:
            log_runtime_error(exc)
        md = (jsonl_dir / _MD_FILENAME).read_text(encoding="utf-8")
        assert "première erreur" in md
        assert "deuxième erreur" in md
        assert "Erreurs listées : 2" in md

    def test_jsonl_still_canonical_after_md_generated(self, jsonl_dir, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")
        try:
            raise RuntimeError("test source canonique")
        except RuntimeError as exc:
            log_runtime_error(exc)
        jsonl_lines = (jsonl_dir / _JSONL_FILENAME).read_text(encoding="utf-8").strip().splitlines()
        assert len(jsonl_lines) == 1
        event = json.loads(jsonl_lines[0])
        assert event["message"] == "test source canonique"
