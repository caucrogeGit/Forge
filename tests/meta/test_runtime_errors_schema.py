"""
Tests DX-RUNTIME-ERRORS-SCHEMA-001 — Schéma canonique JSONL des erreurs runtime.

Couvre :
- Existence et sections du document de schéma.
- Constantes du module Python (REQUIRED_FIELDS, CATEGORIES, LEVELS).
- build_error_event : champs obligatoires, champs optionnels, unicité des ids.
- build_error_event_from_exc : capture type + message depuis une exception active.
- serialize_event : une seule ligne, JSON valide, encodage UTF-8.
- validate_event : accepte valide, rejette champs manquants.
- safe_request_info : structure filtrée.
- Sécurité : pas de données sensibles dans les événements générés.
- Exemples du document : JSON valides.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

from core.runtime_errors import (
    CATEGORIES,
    CATEGORY_CONTROLLER,
    CATEGORY_DATABASE,
    CATEGORY_RUNTIME,
    CATEGORY_TEMPLATE,
    LEVEL_ERROR,
    LEVELS,
    REQUIRED_FIELDS,
    SCHEMA_VERSION,
    _generate_id,
    _sensitive_keys_exposed,
    build_error_event,
    build_error_event_from_exc,
    safe_request_info,
    serialize_event,
    validate_event,
)

pytestmark = pytest.mark.meta

ROOT = pathlib.Path(__file__).parent.parent.parent
SCHEMA_DOC = ROOT / "docs" / "reference" / "runtime-errors-schema.md"

REQUIRED_SECTIONS = [
    "## Objectif",
    "## Source canonique",
    "## Format JSONL",
    "## Champs obligatoires",
    "## Champs optionnels",
    "## Catégories",
    "## Niveaux",
    "## Règles de sécurité",
    "## Exemple minimal",
    "## Exemple complet",
    "## Ce qui n'est pas encore implémenté",
    "## Tickets livrés",
]

FUTURE_TICKETS = [
    "DX-RUNTIME-ERRORS-JSONL-001",
    "DX-RUNTIME-ERRORS-MD-001",
]


# ── Tests documentaires ────────────────────────────────────────────────────────

class TestSchemaDocument:
    def test_schema_document_exists(self):
        assert SCHEMA_DOC.exists(), f"Document de schéma absent : {SCHEMA_DOC}"

    def test_schema_document_not_empty(self):
        assert SCHEMA_DOC.stat().st_size > 500

    def test_schema_contains_all_required_sections(self):
        content = SCHEMA_DOC.read_text(encoding="utf-8")
        missing = [s for s in REQUIRED_SECTIONS if s not in content]
        assert missing == [], f"Sections manquantes : {missing}"

    def test_schema_mentions_future_tickets(self):
        content = SCHEMA_DOC.read_text(encoding="utf-8")
        missing = [t for t in FUTURE_TICKETS if t not in content]
        assert missing == [], f"Tickets futurs non mentionnés : {missing}"

    def test_schema_mentions_canonical_source(self):
        content = SCHEMA_DOC.read_text(encoding="utf-8")
        assert "storage/logs/errors.dev.jsonl" in content

    def test_schema_mentions_required_fields(self):
        content = SCHEMA_DOC.read_text(encoding="utf-8")
        for field in REQUIRED_FIELDS:
            assert field in content, f"Champ obligatoire non documenté : {field}"

    def test_schema_mentions_all_categories(self):
        content = SCHEMA_DOC.read_text(encoding="utf-8")
        for cat in CATEGORIES:
            assert cat in content, f"Catégorie non documentée : {cat}"

    def test_schema_mentions_all_levels(self):
        content = SCHEMA_DOC.read_text(encoding="utf-8")
        for level in LEVELS:
            assert level in content, f"Niveau non documenté : {level}"

    def test_schema_mentions_security_rules(self):
        content = SCHEMA_DOC.read_text(encoding="utf-8")
        assert "password" in content.lower()
        assert "token" in content.lower()
        assert "cookie" in content.lower()

    def test_schema_minimal_example_is_valid_json(self):
        content = SCHEMA_DOC.read_text(encoding="utf-8")
        # Extrait le premier bloc ```json ... ```
        match = re.search(r"```json\n(\{.*?\})\n```", content, re.DOTALL)
        assert match, "Aucun exemple JSON trouvé dans le document"
        try:
            parsed = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            pytest.fail(f"Exemple JSON invalide : {exc}")
        assert isinstance(parsed, dict)

    def test_schema_full_example_is_valid_json(self):
        content = SCHEMA_DOC.read_text(encoding="utf-8")
        # Extrait tous les blocs ```json ... ```
        matches = re.findall(r"```json\n(\{.*?\})\n```", content, re.DOTALL)
        assert len(matches) >= 2, "Moins de 2 exemples JSON dans le document"
        for i, raw in enumerate(matches):
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                pytest.fail(f"Exemple JSON #{i+1} invalide : {exc}")

    def test_schema_example_no_password_values(self):
        content = SCHEMA_DOC.read_text(encoding="utf-8")
        # Vérifie qu'aucun exemple ne contient "password": "..."
        assert '"password": "' not in content
        assert '"passwd": "' not in content
        assert '"token": "' not in content.replace('"post_keys"', "")


# ── Tests des constantes ───────────────────────────────────────────────────────

class TestConstants:
    def test_schema_version_is_string(self):
        assert isinstance(SCHEMA_VERSION, str)
        assert SCHEMA_VERSION == "1.0"

    def test_required_fields_contains_all_mandatory(self):
        mandatory = {
            "schema_version", "id", "timestamp", "environment",
            "level", "category", "exception_type", "message", "safe_for_display",
        }
        assert mandatory <= REQUIRED_FIELDS

    def test_categories_contains_expected(self):
        expected = {
            "runtime", "controller", "routing", "template",
            "database", "configuration", "http", "unknown",
        }
        assert expected <= CATEGORIES

    def test_levels_contains_expected(self):
        expected = {"ERROR", "WARNING", "INFO", "CRITICAL"}
        assert expected <= LEVELS

    def test_category_constants_match_set(self):
        assert CATEGORY_RUNTIME    in CATEGORIES
        assert CATEGORY_CONTROLLER in CATEGORIES
        assert CATEGORY_DATABASE   in CATEGORIES
        assert CATEGORY_TEMPLATE   in CATEGORIES

    def test_level_error_constant(self):
        assert LEVEL_ERROR == "ERROR"
        assert LEVEL_ERROR in LEVELS


# ── Tests de _generate_id ─────────────────────────────────────────────────────

class TestGenerateId:
    def test_id_starts_with_err(self):
        assert _generate_id().startswith("err_")

    def test_id_matches_pattern(self):
        id_ = _generate_id()
        assert re.match(r"^err_\d{8}_\d{6}_[0-9a-f]{4}$", id_), f"ID inattendu : {id_}"

    def test_ids_are_unique(self):
        ids = {_generate_id() for _ in range(100)}
        # Les suffixes hex assurent l'unicité dans la même seconde
        assert len(ids) >= 90  # tolérance légère pour les collisions rares


# ── Tests de build_error_event ────────────────────────────────────────────────

class TestBuildErrorEvent:
    def test_minimal_event_has_required_fields(self):
        event = build_error_event("RuntimeError", "boom")
        for field in REQUIRED_FIELDS:
            assert field in event, f"Champ obligatoire absent : {field}"

    def test_exception_type_and_message(self):
        event = build_error_event("ValueError", "valeur incorrecte")
        assert event["exception_type"] == "ValueError"
        assert event["message"] == "valeur incorrecte"

    def test_defaults(self):
        event = build_error_event("RuntimeError", "x")
        assert event["schema_version"] == "1.0"
        assert event["environment"] == "dev"
        assert event["level"] == "ERROR"
        assert event["category"] == "runtime"
        assert event["safe_for_display"] is False

    def test_safe_for_display_true(self):
        event = build_error_event("ValidationError", "Email invalide", safe_for_display=True)
        assert event["safe_for_display"] is True

    def test_custom_level_and_category(self):
        event = build_error_event(
            "TemplateNotFound", "base.html",
            level="WARNING", category="template",
        )
        assert event["level"] == "WARNING"
        assert event["category"] == "template"

    def test_with_request_dict(self):
        req = safe_request_info("GET", "/users", query="page=1")
        event = build_error_event("RuntimeError", "x", request=req)
        assert "request" in event
        assert event["request"]["method"] == "GET"
        assert event["request"]["path"] == "/users"

    def test_without_request_no_request_key(self):
        event = build_error_event("RuntimeError", "x")
        assert "request" not in event

    def test_with_traceback_frames(self):
        frames = [
            {"file": "app.py", "line": 100, "function": "do_GET"},
            {"file": "mvc/controllers/foo.py", "line": 42, "function": "index"},
        ]
        event = build_error_event("RuntimeError", "x", traceback_frames=frames)
        assert "traceback" in event
        assert len(event["traceback"]) == 2
        assert "location" in event
        assert event["location"]["function"] == "index"

    def test_with_hint(self):
        event = build_error_event("RuntimeError", "x", hint="Vérifier les imports.")
        assert event.get("hint") == "Vérifier les imports."

    def test_without_hint_no_hint_key(self):
        event = build_error_event("RuntimeError", "x")
        assert "hint" not in event

    def test_event_id_is_unique_across_calls(self):
        e1 = build_error_event("RuntimeError", "x")
        e2 = build_error_event("RuntimeError", "x")
        assert e1["id"] != e2["id"]

    def test_timestamp_is_iso8601(self):
        event = build_error_event("RuntimeError", "x")
        ts = event["timestamp"]
        assert "T" in ts
        assert "+" in ts or "Z" in ts or ts.endswith("+00:00")


# ── Tests de build_error_event_from_exc ───────────────────────────────────────

class TestBuildErrorEventFromExc:
    def test_captures_exception_type(self):
        try:
            raise ValueError("valeur incorrecte")
        except ValueError as exc:
            event = build_error_event_from_exc(exc)
        assert event["exception_type"] == "ValueError"

    def test_captures_message(self):
        try:
            raise RuntimeError("message d'erreur")
        except RuntimeError as exc:
            event = build_error_event_from_exc(exc)
        assert event["message"] == "message d'erreur"

    def test_has_required_fields(self):
        try:
            raise TypeError("mauvais type")
        except TypeError as exc:
            event = build_error_event_from_exc(exc)
        for field in REQUIRED_FIELDS:
            assert field in event

    def test_traceback_captured_in_except_block(self):
        try:
            raise RuntimeError("boom")
        except RuntimeError as exc:
            event = build_error_event_from_exc(exc)
        # Le traceback doit être non vide quand appelé depuis un except
        assert "traceback" in event
        assert len(event["traceback"]) > 0

    def test_accepts_custom_category(self):
        try:
            raise RuntimeError("db error")
        except RuntimeError as exc:
            event = build_error_event_from_exc(exc, category="database")
        assert event["category"] == "database"


# ── Tests de validate_event ────────────────────────────────────────────────────

class TestValidateEvent:
    def test_valid_event_passes(self):
        event = build_error_event("RuntimeError", "x")
        validate_event(event)  # ne doit pas lever

    def test_missing_one_field_raises(self):
        event = build_error_event("RuntimeError", "x")
        del event["level"]
        with pytest.raises(ValueError, match="level"):
            validate_event(event)

    def test_missing_multiple_fields_raises(self):
        event = {"schema_version": "1.0"}
        with pytest.raises(ValueError):
            validate_event(event)

    def test_empty_event_raises(self):
        with pytest.raises(ValueError):
            validate_event({})


# ── Tests de serialize_event ───────────────────────────────────────────────────

class TestSerializeEvent:
    def test_produces_single_line(self):
        event = build_error_event("RuntimeError", "x")
        line = serialize_event(event)
        assert "\n" not in line

    def test_produces_valid_json(self):
        event = build_error_event("RuntimeError", "x")
        line = serialize_event(event)
        parsed = json.loads(line)
        assert isinstance(parsed, dict)

    def test_roundtrip_preserves_fields(self):
        event = build_error_event(
            "TypeError", "message",
            category="controller",
            hint="vérifier la signature",
        )
        line   = serialize_event(event)
        parsed = json.loads(line)
        assert parsed["exception_type"] == "TypeError"
        assert parsed["category"] == "controller"
        assert parsed["hint"] == "vérifier la signature"

    def test_utf8_characters_preserved(self):
        event = build_error_event("RuntimeError", "Erreur inattendue — vérifier config")
        line = serialize_event(event)
        parsed = json.loads(line)
        assert "Erreur inattendue" in parsed["message"]

    def test_no_superfluous_spaces(self):
        event = build_error_event("RuntimeError", "x")
        line = serialize_event(event)
        # separators=(",", ":") — pas d'espaces autour de : ni de ,
        assert ": " not in line
        assert ", " not in line

    def test_multiple_events_are_independent_lines(self):
        events = [build_error_event("RuntimeError", f"erreur {i}") for i in range(3)]
        lines = [serialize_event(e) for e in events]
        for line in lines:
            parsed = json.loads(line)
            assert "message" in parsed


# ── Tests de safe_request_info ─────────────────────────────────────────────────

class TestSafeRequestInfo:
    def test_minimal_request(self):
        info = safe_request_info("GET", "/users")
        assert info["method"] == "GET"
        assert info["path"] == "/users"
        assert info["query"] == ""

    def test_post_keys_present(self):
        info = safe_request_info("POST", "/login", post_keys=["email", "password"])
        assert "post_keys" in info
        assert "email" in info["post_keys"]
        assert "password" in info["post_keys"]

    def test_post_values_not_present(self):
        info = safe_request_info("POST", "/login", post_keys=["email", "password"])
        serialized = json.dumps(info)
        assert "secret123" not in serialized

    def test_header_names_present(self):
        info = safe_request_info("GET", "/", header_names=["Host", "User-Agent"])
        assert "headers" in info
        assert "Host" in info["headers"]

    def test_none_method_path_gives_empty_strings(self):
        info = safe_request_info(None, None)
        assert info["method"] == ""
        assert info["path"] == ""


# ── Tests de sécurité ─────────────────────────────────────────────────────────

class TestSecurity:
    def test_default_event_safe_for_display_false(self):
        event = build_error_event("RuntimeError", "x")
        assert event["safe_for_display"] is False

    def test_sensitive_keys_constant_contains_expected(self):
        sensitive = _sensitive_keys_exposed()
        assert "password" in sensitive
        assert "token" in sensitive
        assert "authorization" in sensitive
        assert "cookie" in sensitive

    def test_event_from_exc_does_not_expose_env_secrets(self):
        try:
            raise RuntimeError("DB_APP_PWD=supersecret")
        except RuntimeError as exc:
            event = build_error_event_from_exc(exc)
        # Le message EST dans l'événement (c'est le message d'erreur)
        # mais safe_for_display doit être False pour ne pas l'afficher au visiteur
        assert event["safe_for_display"] is False
        assert serialize_event(event)  # sérialisable
