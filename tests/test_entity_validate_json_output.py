"""Garde-fou ENTITY-CONTRACT-010.

Vérifie la sortie JSON de forge entity:validate --json :

Reconnaissance :
- --json est accepté sans erreur de parsing.

Format JSON :
- stdout est du JSON valide ;
- les champs valid, files_checked, files_valid, errors_count, warnings_count,
  errors, warnings sont toujours présents ;
- errors et warnings sont toujours des listes ;
- warnings_count correspond à len(warnings) ;
- errors_count correspond à len(errors).

Champs d'erreur :
- chaque erreur contient code, file, path, message, hint, phase ;
- les codes commencent par FORGE_ ;
- phase vaut "json", "schema" ou "semantic".

Cas nominaux :
- projet valide → valid true, errors_count 0 ;
- projet invalide → valid false, errors_count > 0 ;
- JSON syntaxique cassé → phase "json" ;
- entité invalide contre JSON Schema → phase "schema", code FORGE_ENTITY_SCHEMA_INVALID ;
- relations.json invalide → phase "schema", code FORGE_RELATION_SCHEMA_INVALID ;
- erreur sémantique → phase "semantic" ;
- relations.json absent → warning cohérent.

Isolation :
- sortie JSON sans ligne humaine ([OK], [ERREUR], Avertissement) ;
- sortie humaine sans --json inchangée ;
- code retour 0 si valid true, non nul si valid false.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"

pytest.importorskip("jsonschema", reason="jsonschema non installé")

_VALID_ENTITY = {
    "schema_version": "1.0",
    "name": "Article",
    "table": "articles",
    "fields": [{"name": "title", "type": "string"}],
}

_VALID_RELATIONS = {
    "schema_version": "1.0",
    "relations": [],
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_project(tmp_path: Path, entities: dict[str, dict], relations: dict | None = None) -> Path:
    entities_dir = tmp_path / "mvc" / "entities"
    entities_dir.mkdir(parents=True)
    for filename, data in entities.items():
        (entities_dir / filename).write_text(json.dumps(data), encoding="utf-8")
    if relations is not None:
        (entities_dir / "relations.json").write_text(json.dumps(relations), encoding="utf-8")
    return tmp_path


def _run(cwd: Path, *extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE_PY), "entity:validate", *extra_args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def _json(cwd: Path) -> tuple[subprocess.CompletedProcess, dict]:
    result = _run(cwd, "--json")
    data = json.loads(result.stdout)
    return result, data


# ── Tests de reconnaissance ────────────────────────────────────────────────────

class TestJsonFlagRecognized:
    def test_json_flag_accepted(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        result = _run(proj, "--json")
        assert result.returncode == 0

    def test_json_output_is_valid_json(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        result = _run(proj, "--json")
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, dict)

    def test_json_stdout_contains_no_human_lines(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        result = _run(proj, "--json")
        for forbidden in ("[OK]", "[ERREUR]", "Avertissement", "Validation terminée"):
            assert forbidden not in result.stdout, f"{forbidden!r} found in JSON stdout"


# ── Tests de structure JSON ────────────────────────────────────────────────────

class TestJsonStructure:
    @pytest.mark.parametrize("field", [
        "valid", "files_checked", "files_valid",
        "errors_count", "warnings_count", "errors", "warnings",
    ])
    def test_required_field_present(self, tmp_path, field):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        _, data = _json(proj)
        assert field in data, f"Champ manquant : {field!r}"

    def test_errors_is_list(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        _, data = _json(proj)
        assert isinstance(data["errors"], list)

    def test_warnings_is_list(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        _, data = _json(proj)
        assert isinstance(data["warnings"], list)

    def test_errors_count_matches_errors_length(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        _, data = _json(proj)
        assert data["errors_count"] == len(data["errors"])

    def test_warnings_count_matches_warnings_length(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        _, data = _json(proj)
        assert data["warnings_count"] == len(data["warnings"])

    def test_valid_is_boolean(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        _, data = _json(proj)
        assert isinstance(data["valid"], bool)


# ── Tests cas valide ──────────────────────────────────────────────────────────

class TestJsonValidProject:
    def test_valid_project_valid_true(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        _, data = _json(proj)
        assert data["valid"] is True

    def test_valid_project_errors_count_zero(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        _, data = _json(proj)
        assert data["errors_count"] == 0

    def test_valid_project_errors_empty(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        _, data = _json(proj)
        assert data["errors"] == []

    def test_valid_project_return_zero(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        result = _run(proj, "--json")
        assert result.returncode == 0

    def test_valid_project_files_valid_correct(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY}, relations=_VALID_RELATIONS)
        _, data = _json(proj)
        assert data["files_valid"] == 2
        assert data["files_checked"] == 2

    def test_valid_project_with_relations_no_errors(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY}, relations=_VALID_RELATIONS)
        _, data = _json(proj)
        assert data["valid"] is True
        assert data["errors_count"] == 0


# ── Tests cas invalide ────────────────────────────────────────────────────────

class TestJsonInvalidProject:
    def test_invalid_project_valid_false(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        _, data = _json(proj)
        assert data["valid"] is False

    def test_invalid_project_errors_count_positive(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        _, data = _json(proj)
        assert data["errors_count"] > 0

    def test_invalid_project_return_nonzero(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        result = _run(proj, "--json")
        assert result.returncode != 0


# ── Tests champs d'erreur ─────────────────────────────────────────────────────

class TestJsonErrorFields:
    @pytest.mark.parametrize("field", ["code", "file", "path", "message", "hint", "phase"])
    def test_error_has_required_field(self, tmp_path, field):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        _, data = _json(proj)
        assert data["errors"], "Aucune erreur collectée"
        for err in data["errors"]:
            assert field in err, f"Champ manquant dans l'erreur : {field!r}"

    def test_error_codes_start_with_forge(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        _, data = _json(proj)
        for err in data["errors"]:
            assert err["code"].startswith("FORGE_"), f"Code sans préfixe FORGE_ : {err['code']}"

    @pytest.mark.parametrize("phase", ["json", "schema", "semantic"])
    def test_phase_values_are_valid(self, tmp_path, phase):
        # Juste vérifie que la valeur est dans la liste des phases valides
        valid_phases = {"json", "schema", "semantic", "runtime"}
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        _, data = _json(proj)
        for err in data["errors"]:
            assert err["phase"] in valid_phases, f"Phase inconnue : {err['phase']}"


# ── Tests phase par type d'erreur ─────────────────────────────────────────────

class TestJsonPhases:
    def test_json_parse_error_has_phase_json(self, tmp_path):
        entities_dir = tmp_path / "mvc" / "entities"
        entities_dir.mkdir(parents=True)
        (entities_dir / "broken.json").write_text("{invalid json}", encoding="utf-8")
        _, data = _json(tmp_path)
        assert data["errors"]
        assert any(e["phase"] == "json" for e in data["errors"])

    def test_json_parse_error_has_code_json_invalid(self, tmp_path):
        entities_dir = tmp_path / "mvc" / "entities"
        entities_dir.mkdir(parents=True)
        (entities_dir / "broken.json").write_text("{invalid json}", encoding="utf-8")
        _, data = _json(tmp_path)
        assert any(e["code"] == "FORGE_ENTITY_JSON_INVALID" for e in data["errors"])

    def test_schema_error_entity_has_phase_schema(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        _, data = _json(proj)
        assert any(e["phase"] == "schema" for e in data["errors"])

    def test_schema_error_entity_has_code_schema_invalid(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        _, data = _json(proj)
        assert any(e["code"] == "FORGE_ENTITY_SCHEMA_INVALID" for e in data["errors"])

    def test_schema_error_relations_has_phase_schema(self, tmp_path):
        relations = {
            "schema_version": "1.0",
            "relations": [{"type": "one_to_one", "from": "A", "to": "B", "name": "ab"}],
        }
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY}, relations=relations)
        _, data = _json(proj)
        assert any(e["phase"] == "schema" for e in data["errors"])

    def test_schema_error_relations_has_code_relation_schema_invalid(self, tmp_path):
        relations = {
            "schema_version": "1.0",
            "relations": [{"type": "one_to_one", "from": "A", "to": "B", "name": "ab"}],
        }
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY}, relations=relations)
        _, data = _json(proj)
        assert any(e["code"] == "FORGE_RELATION_SCHEMA_INVALID" for e in data["errors"])

    def test_semantic_error_has_phase_semantic(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [
                {"name": "title", "type": "string"},
                {"name": "title", "type": "text"},
            ],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        _, data = _json(proj)
        assert any(e["phase"] == "semantic" for e in data["errors"])

    def test_semantic_error_has_forge_code(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [
                {"name": "title", "type": "string"},
                {"name": "title", "type": "text"},
            ],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        _, data = _json(proj)
        assert any(e["code"] == "FORGE_ENTITY_DUPLICATE_FIELD" for e in data["errors"])


# ── Tests warnings ────────────────────────────────────────────────────────────

class TestJsonWarnings:
    def test_relations_absent_produces_warning(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        _, data = _json(proj)
        assert data["warnings_count"] > 0

    def test_warnings_count_consistent(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        _, data = _json(proj)
        assert data["warnings_count"] == len(data["warnings"])

    def test_warnings_always_present(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY}, relations=_VALID_RELATIONS)
        _, data = _json(proj)
        assert "warnings" in data
        assert isinstance(data["warnings"], list)


# ── Tests compatibilité sortie humaine ────────────────────────────────────────

class TestHumanOutputUnchanged:
    def test_human_output_still_works(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        result = _run(proj)
        assert result.returncode == 0
        assert "[OK]" in result.stdout
        assert "Validation terminée" in result.stdout

    def test_human_output_no_json_machine(self, tmp_path):
        proj = _make_project(tmp_path, {"article.json": _VALID_ENTITY})
        result = _run(proj)
        try:
            json.loads(result.stdout)
            assert False, "La sortie humaine ne doit pas être du JSON."
        except json.JSONDecodeError:
            pass

    def test_json_stdout_no_human_text_on_error(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        result = _run(proj, "--json")
        for forbidden in ("[OK]", "[ERREUR]", "Validation terminée", "Avertissement"):
            assert forbidden not in result.stdout
