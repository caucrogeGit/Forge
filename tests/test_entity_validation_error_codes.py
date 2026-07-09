"""Garde-fou ENTITY-CONTRACT-009.

Vérifie les codes d'erreur stables de la validation Forge :

Liste centrale :
- tous les codes attendus existent dans entity_validation_errors.ALL_CODES ;
- tous les codes commencent par FORGE_ ;
- les codes sont uniques.

Codes sémantiques (via validate_semantic) :
- doublon de champ → FORGE_ENTITY_DUPLICATE_FIELD ;
- mot réservé Python → FORGE_ENTITY_RESERVED_PYTHON_NAME ;
- table dupliquée → FORGE_ENTITY_DUPLICATE_TABLE ;
- index invalide → FORGE_ENTITY_INVALID_INDEX ;
- relation vers entité inconnue → FORGE_RELATION_UNKNOWN_ENTITY ;
- FK collision → FORGE_RELATION_FK_COLLISION ;
- set_null / nullable=false → FORGE_RELATION_INVALID_ON_DELETE ;
- pivot.table collision → FORGE_PIVOT_TABLE_COLLISION ;
- pivot key collision → FORGE_PIVOT_KEY_COLLISION ;
- champ pivot réservé → FORGE_PIVOT_RESERVED_FIELD ;
- relation M2M inverse dupliquée → FORGE_RELATION_DUPLICATE.

Codes CLI (via subprocess forge entity:validate) :
- erreur JSON Schema entité → FORGE_ENTITY_SCHEMA_INVALID ;
- erreur JSON Schema relations → FORGE_RELATION_SCHEMA_INVALID ;
- JSON cassé → FORGE_ENTITY_JSON_INVALID ;
- la sortie humaine contient "Code :".
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

import forge_mvc_entities.entity_validation_errors as _err_module  # noqa: E402
from forge_mvc_entities.entity_validation_errors import ALL_CODES  # noqa: E402
from forge_mvc_entities.entity_semantic_validate import SemanticError, validate_semantic  # noqa: E402


# ── Fixtures communes ─────────────────────────────────────────────────────────

def _entity(name: str, table: str, fields: list | None = None, **kwargs) -> dict:
    return {
        "schema_version": "1.0",
        "name": name,
        "table": table,
        "fields": fields or [{"name": "title", "type": "string"}],
        **kwargs,
    }


def _m2o(from_: str, to: str, name: str, **kwargs) -> dict:
    return {"type": "many_to_one", "from": from_, "to": to, "name": name, **kwargs}


def _m2m(from_: str, to: str, name: str, pivot: dict, **kwargs) -> dict:
    return {"type": "many_to_many", "from": from_, "to": to, "name": name, "pivot": pivot, **kwargs}


def _pivot(table: str, from_key: str, to_key: str, **kwargs) -> dict:
    return {"table": table, "from_key": from_key, "to_key": to_key, "id": True, "unique_pair": True, **kwargs}


def _relations(rels: list) -> dict:
    return {"schema_version": "1.0", "relations": rels}


def _errors(entities, relations=None) -> list[SemanticError]:
    return validate_semantic(entities, relations)


def _codes(entities, relations=None) -> list[str]:
    return [e.code for e in _errors(entities, relations)]


ARTICLE = ("article.json", _entity("Article", "articles"))
CATEGORY = ("category.json", _entity("Category", "categories"))
TAG = ("tag.json", _entity("Tag", "tags"))

_EXPECTED_CODES = [
    "FORGE_ENTITY_JSON_INVALID",
    "FORGE_ENTITY_SCHEMA_MISSING",
    "FORGE_ENTITY_SCHEMA_INVALID",
    "FORGE_ENTITY_DUPLICATE_FIELD",
    "FORGE_ENTITY_RESERVED_PYTHON_NAME",
    "FORGE_ENTITY_DUPLICATE_TABLE",
    "FORGE_ENTITY_INVALID_INDEX",
    "FORGE_RELATION_SCHEMA_INVALID",
    "FORGE_RELATION_UNKNOWN_ENTITY",
    "FORGE_RELATION_DUPLICATE",
    "FORGE_RELATION_INVALID_ON_DELETE",
    "FORGE_RELATION_FK_COLLISION",
    "FORGE_PIVOT_SCHEMA_INVALID",
    "FORGE_PIVOT_TABLE_COLLISION",
    "FORGE_PIVOT_RESERVED_FIELD",
    "FORGE_PIVOT_KEY_COLLISION",
    "FORGE_PIVOT_UNIQUE_PAIR_REQUIRED",
]


# ── Tests liste centrale ──────────────────────────────────────────────────────

class TestAllCodesRegistry:
    @pytest.mark.parametrize("code", _EXPECTED_CODES)
    def test_expected_code_in_all_codes(self, code):
        assert code in ALL_CODES, f"{code} absent de entity_validation_errors.ALL_CODES"

    @pytest.mark.parametrize("code", _EXPECTED_CODES)
    def test_expected_code_as_module_attribute(self, code):
        assert hasattr(_err_module, code), f"{code} absent comme attribut du module"

    def test_all_codes_start_with_forge_prefix(self):
        for code in ALL_CODES:
            assert code.startswith("FORGE_"), f"{code} ne commence pas par FORGE_"

    def test_all_codes_are_unique(self):
        assert len(ALL_CODES) == len(set(ALL_CODES)), "Des codes sont en doublon dans ALL_CODES"

    def test_all_codes_are_uppercase(self):
        for code in ALL_CODES:
            assert code == code.upper(), f"{code} n'est pas entièrement en majuscules"


# ── Tests codes sémantiques ───────────────────────────────────────────────────

class TestSemanticErrorCodes:
    def test_duplicate_field_code(self):
        entity = _entity("Article", "articles", fields=[
            {"name": "title", "type": "string"},
            {"name": "title", "type": "text"},
        ])
        codes = _codes([("article.json", entity)])
        assert "FORGE_ENTITY_DUPLICATE_FIELD" in codes

    def test_reserved_python_name_code(self):
        entity = _entity("Article", "articles", fields=[{"name": "class", "type": "string"}])
        codes = _codes([("article.json", entity)])
        assert "FORGE_ENTITY_RESERVED_PYTHON_NAME" in codes

    def test_duplicate_table_code(self):
        a = ("article.json", _entity("Article", "articles"))
        b = ("news.json", _entity("News", "articles"))
        codes = _codes([a, b])
        assert "FORGE_ENTITY_DUPLICATE_TABLE" in codes

    def test_invalid_index_code(self):
        entity = _entity("Article", "articles", indexes=[
            {"name": "idx_slug", "fields": ["slug"]}
        ])
        codes = _codes([("article.json", entity)])
        assert "FORGE_ENTITY_INVALID_INDEX" in codes

    def test_unknown_entity_m2o_code(self):
        rel = _relations([_m2o("Ghost", "Category", "category")])
        codes = _codes([CATEGORY], rel)
        assert "FORGE_RELATION_UNKNOWN_ENTITY" in codes

    def test_fk_collision_code(self):
        entity = ("article.json", _entity("Article", "articles",
                                          fields=[{"name": "category_id", "type": "integer"}]))
        rel = _relations([_m2o("Article", "Category", "category")])
        codes = _codes([entity, CATEGORY], rel)
        assert "FORGE_RELATION_FK_COLLISION" in codes

    def test_set_null_nullable_false_code(self):
        rel = _relations([_m2o("Article", "Category", "category", nullable=False, on_delete="set_null")])
        codes = _codes([ARTICLE, CATEGORY], rel)
        assert "FORGE_RELATION_INVALID_ON_DELETE" in codes

    def test_pivot_table_collision_code(self):
        rel = _relations([_m2m("Article", "Tag", "tags", _pivot("articles", "article_id", "tag_id"))])
        codes = _codes([ARTICLE, TAG], rel)
        assert "FORGE_PIVOT_TABLE_COLLISION" in codes

    def test_pivot_key_collision_code(self):
        rel = _relations([_m2m("Article", "Tag", "tags", _pivot("article_tags", "entity_id", "entity_id"))])
        codes = _codes([ARTICLE, TAG], rel)
        assert "FORGE_PIVOT_KEY_COLLISION" in codes

    def test_pivot_reserved_field_code(self):
        pivot = _pivot("article_tags", "article_id", "tag_id",
                       fields=[{"name": "article_id", "type": "integer"}])
        rel = _relations([_m2m("Article", "Tag", "tags", pivot)])
        codes = _codes([ARTICLE, TAG], rel)
        assert "FORGE_PIVOT_RESERVED_FIELD" in codes

    def test_m2m_inverse_duplicate_code(self):
        pivot_ab = _pivot("article_tags", "article_id", "tag_id")
        pivot_ba = _pivot("tag_articles", "tag_id", "article_id")
        rel = _relations([
            _m2m("Article", "Tag", "tags", pivot_ab),
            _m2m("Tag", "Article", "articles", pivot_ba),
        ])
        codes = _codes([ARTICLE, TAG], rel)
        assert "FORGE_RELATION_DUPLICATE" in codes

    def test_unknown_entity_m2m_code(self):
        rel = _relations([_m2m("Ghost", "Tag", "tags", _pivot("ghost_tags", "ghost_id", "tag_id"))])
        codes = _codes([TAG], rel)
        assert "FORGE_RELATION_UNKNOWN_ENTITY" in codes

    def test_semantic_error_has_code_attribute(self):
        entity = _entity("Article", "articles", fields=[
            {"name": "title", "type": "string"},
            {"name": "title", "type": "text"},
        ])
        errors = _errors([("article.json", entity)])
        assert errors
        assert hasattr(errors[0], "code")
        assert errors[0].code.startswith("FORGE_")

    def test_semantic_error_has_file_attribute(self):
        entity = _entity("Article", "articles", fields=[
            {"name": "title", "type": "string"},
            {"name": "title", "type": "text"},
        ])
        errors = _errors([("article.json", entity)])
        assert errors
        assert hasattr(errors[0], "file")

    def test_semantic_error_has_message_attribute(self):
        entity = _entity("Article", "articles", fields=[
            {"name": "title", "type": "string"},
            {"name": "title", "type": "text"},
        ])
        errors = _errors([("article.json", entity)])
        assert errors
        assert hasattr(errors[0], "message")


# ── Tests CLI codes ───────────────────────────────────────────────────────────

def _make_project(tmp_path: Path, entities: dict[str, dict], relations: dict | None = None) -> Path:
    entities_dir = tmp_path / "mvc" / "entities"
    entities_dir.mkdir(parents=True)
    for filename, data in entities.items():
        (entities_dir / filename).write_text(json.dumps(data), encoding="utf-8")
    if relations is not None:
        (entities_dir / "relations.json").write_text(json.dumps(relations), encoding="utf-8")
    return tmp_path


def _run(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE_PY), "entity:validate"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


class TestCLIErrorCodes:
    def test_schema_invalid_entity_shows_code(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        result = _run(proj)
        assert "FORGE_ENTITY_SCHEMA_INVALID" in result.stdout

    def test_json_invalid_shows_code(self, tmp_path):
        entities_dir = tmp_path / "mvc" / "entities"
        entities_dir.mkdir(parents=True)
        (entities_dir / "broken.json").write_text("{invalid json}", encoding="utf-8")
        result = _run(tmp_path)
        assert "FORGE_ENTITY_JSON_INVALID" in result.stdout

    def test_schema_invalid_relations_shows_code(self, tmp_path):
        valid_entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "title", "type": "string"}],
        }
        relations = {
            "schema_version": "1.0",
            "relations": [
                {"type": "one_to_one", "from": "A", "to": "B", "name": "ab"}
            ],
        }
        proj = _make_project(tmp_path, {"article.json": valid_entity}, relations=relations)
        result = _run(proj)
        assert "FORGE_RELATION_SCHEMA_INVALID" in result.stdout

    def test_semantic_error_shows_code_label(self, tmp_path):
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
        result = _run(proj)
        assert "Code :" in result.stdout

    def test_semantic_error_shows_forge_prefix_code(self, tmp_path):
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
        result = _run(proj)
        assert "FORGE_ENTITY_DUPLICATE_FIELD" in result.stdout

    def test_schema_error_shows_code_label(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "id", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        result = _run(proj)
        assert "Code :" in result.stdout
