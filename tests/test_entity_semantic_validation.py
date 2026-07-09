"""Garde-fou ENTITY-CONTRACT-008.

Vérifie la validation sémantique Forge des entités et relations canoniques :

Entités :
- doublon de champ dans une entité ;
- champ nommé avec mot réservé Python ;
- deux entités avec la même table ;
- index pointant vers un champ inexistant ;
- projet valide (entités + relations) → aucune erreur.

Relations many_to_one :
- from vers entité inconnue ;
- to vers entité inconnue ;
- foreign_key collisionnant un champ métier ;
- nullable=false + on_delete=set_null.

Relations many_to_many :
- from vers entité inconnue ;
- to vers entité inconnue ;
- self-relation (from == to) ;
- pivot.table collisionnant une table d'entité ;
- pivot.from_key == pivot.to_key ;
- pivot.fields redéclarant from_key ;
- pivot.fields redéclarant to_key ;
- pivot.fields redéclarant id ;
- relation many_to_many déclarée deux fois en sens inverse.

Intégration CLI :
- les erreurs sémantiques apparaissent dans la sortie de forge entity:validate ;
- la sortie mentionne "Validation sémantique" ou équivalent.

Les tests unitaires appellent validate_semantic() directement.
Les tests d'intégration CLI utilisent des projets temporaires (tmp_path).
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


def _reasons(entities, relations=None) -> list[str]:
    return [e.message for e in _errors(entities, relations)]


ARTICLE = ("article.json", _entity("Article", "articles"))
CATEGORY = ("category.json", _entity("Category", "categories"))


# ── Tests entités ─────────────────────────────────────────────────────────────

class TestEntityDuplicateField:
    def test_duplicate_field_produces_error(self):
        entity = _entity("Article", "articles", fields=[
            {"name": "title", "type": "string"},
            {"name": "title", "type": "text"},
        ])
        errors = _errors([("article.json", entity)])
        assert any("déclaré deux fois" in r for r in [e.message for e in errors])

    def test_duplicate_field_path_correct(self):
        entity = _entity("Article", "articles", fields=[
            {"name": "title", "type": "string"},
            {"name": "title", "type": "text"},
        ])
        errors = _errors([("article.json", entity)])
        assert any("fields[1].name" in e.path for e in errors)  # path inchangé

    def test_no_duplicate_no_error(self):
        entity = _entity("Article", "articles", fields=[
            {"name": "title", "type": "string"},
            {"name": "body", "type": "text"},
        ])
        assert not _errors([("article.json", entity)])


class TestPythonReservedWords:
    @pytest.mark.parametrize("reserved", ["class", "def", "return", "for", "while", "import", "from"])
    def test_reserved_word_produces_error(self, reserved):
        entity = _entity("Article", "articles", fields=[{"name": reserved, "type": "string"}])
        errors = _errors([("article.json", entity)])
        assert any("réservé Python" in r for r in [e.message for e in errors])

    def test_normal_name_no_error(self):
        entity = _entity("Article", "articles", fields=[{"name": "title", "type": "string"}])
        assert not _errors([("article.json", entity)])


class TestDuplicateTable:
    def test_duplicate_table_produces_error(self):
        a = ("article.json", _entity("Article", "articles"))
        b = ("news.json", _entity("News", "articles"))
        errors = _errors([a, b])
        assert any("articles" in e.message and "déjà utilisée" in e.message for e in errors)

    def test_unique_tables_no_error(self):
        a = ("article.json", _entity("Article", "articles"))
        b = ("category.json", _entity("Category", "categories"))
        assert not _errors([a, b])


class TestIndexNonExistentField:
    def test_index_pointing_to_missing_field(self):
        entity = _entity("Article", "articles", indexes=[
            {"name": "idx_articles_slug", "fields": ["slug"]}
        ])
        errors = _errors([("article.json", entity)])
        assert any("slug" in e.message and "index" in e.message for e in errors)

    def test_index_pointing_to_existing_field(self):
        entity = _entity("Article", "articles",
                         fields=[{"name": "title", "type": "string"}],
                         indexes=[{"name": "idx_articles_title", "fields": ["title"]}])
        assert not _errors([("article.json", entity)])


# ── Tests many_to_one ─────────────────────────────────────────────────────────

class TestManyToOneUnknownEntity:
    def test_unknown_from_entity(self):
        rel = _relations([_m2o("Ghost", "Category", "category")])
        errors = _errors([CATEGORY], rel)
        assert any("Ghost" in e.message and "source" in e.message for e in errors)

    def test_unknown_to_entity(self):
        rel = _relations([_m2o("Article", "Ghost", "category")])
        errors = _errors([ARTICLE], rel)
        assert any("Ghost" in e.message and "cible" in e.message for e in errors)

    def test_known_entities_no_error(self):
        rel = _relations([_m2o("Article", "Category", "category")])
        errors = _errors([ARTICLE, CATEGORY], rel)
        assert not errors


class TestForeignKeyCollision:
    def test_fk_collides_with_field(self):
        entity = ("article.json", _entity("Article", "articles",
                                          fields=[{"name": "category_id", "type": "integer"}]))
        rel = _relations([_m2o("Article", "Category", "category")])
        errors = _errors([entity, CATEGORY], rel)
        assert any("category_id" in e.message and "collision" in e.message.lower() for e in errors)

    def test_explicit_fk_different_name_no_error(self):
        rel = _relations([_m2o("Article", "Category", "category", foreign_key="cat_id")])
        errors = _errors([ARTICLE, CATEGORY], rel)
        assert not errors


class TestSetNullNullableFalse:
    def test_set_null_with_not_nullable_is_error(self):
        rel = _relations([_m2o("Article", "Category", "category", nullable=False, on_delete="set_null")])
        errors = _errors([ARTICLE, CATEGORY], rel)
        assert any("set_null" in e.message and "nullable=false" in e.message for e in errors)

    def test_set_null_with_nullable_true_ok(self):
        rel = _relations([_m2o("Article", "Category", "category", nullable=True, on_delete="set_null")])
        errors = _errors([ARTICLE, CATEGORY], rel)
        assert not errors

    def test_cascade_with_not_nullable_ok(self):
        rel = _relations([_m2o("Article", "Category", "category", nullable=False, on_delete="cascade")])
        errors = _errors([ARTICLE, CATEGORY], rel)
        assert not errors


# ── Tests many_to_many ────────────────────────────────────────────────────────

TAG = ("tag.json", _entity("Tag", "tags"))


class TestManyToManyUnknownEntity:
    def test_unknown_from(self):
        rel = _relations([_m2m("Ghost", "Tag", "tags", _pivot("article_tags", "ghost_id", "tag_id"))])
        errors = _errors([TAG], rel)
        assert any("Ghost" in e.message for e in errors)

    def test_unknown_to(self):
        rel = _relations([_m2m("Article", "Ghost", "tags", _pivot("article_tags", "article_id", "ghost_id"))])
        errors = _errors([ARTICLE], rel)
        assert any("Ghost" in e.message for e in errors)


class TestManyToManySelfRelation:
    def test_self_relation_is_error(self):
        rel = _relations([_m2m("Article", "Article", "related", _pivot("article_related", "article_id", "related_id"))])
        errors = _errors([ARTICLE], rel)
        assert any("elle-même" in e.message for e in errors)


class TestPivotTableCollision:
    def test_pivot_table_same_as_entity_table(self):
        rel = _relations([_m2m("Article", "Tag", "tags", _pivot("articles", "article_id", "tag_id"))])
        errors = _errors([ARTICLE, TAG], rel)
        assert any("articles" in e.message and "Article" in e.message for e in errors)

    def test_distinct_pivot_table_no_error(self):
        rel = _relations([_m2m("Article", "Tag", "tags", _pivot("article_tags", "article_id", "tag_id"))])
        errors = _errors([ARTICLE, TAG], rel)
        assert not errors


class TestPivotKeyCollision:
    def test_from_key_equals_to_key(self):
        rel = _relations([_m2m("Article", "Tag", "tags", _pivot("article_tags", "entity_id", "entity_id"))])
        errors = _errors([ARTICLE, TAG], rel)
        assert any("from_key" in e.message and "to_key" in e.message for e in errors)

    def test_distinct_keys_no_error(self):
        rel = _relations([_m2m("Article", "Tag", "tags", _pivot("article_tags", "article_id", "tag_id"))])
        errors = _errors([ARTICLE, TAG], rel)
        assert not errors


class TestPivotFieldsReserved:
    def test_pivot_field_redeclares_from_key(self):
        pivot = _pivot("article_tags", "article_id", "tag_id",
                       fields=[{"name": "article_id", "type": "integer"}])
        rel = _relations([_m2m("Article", "Tag", "tags", pivot)])
        errors = _errors([ARTICLE, TAG], rel)
        assert any("article_id" in e.message and "réservé" in e.message for e in errors)

    def test_pivot_field_redeclares_to_key(self):
        pivot = _pivot("article_tags", "article_id", "tag_id",
                       fields=[{"name": "tag_id", "type": "integer"}])
        rel = _relations([_m2m("Article", "Tag", "tags", pivot)])
        errors = _errors([ARTICLE, TAG], rel)
        assert any("tag_id" in e.message and "réservé" in e.message for e in errors)

    def test_pivot_field_redeclares_id(self):
        pivot = _pivot("article_tags", "article_id", "tag_id",
                       fields=[{"name": "id", "type": "integer"}])
        rel = _relations([_m2m("Article", "Tag", "tags", pivot)])
        errors = _errors([ARTICLE, TAG], rel)
        assert any('"id"' in e.message and "réservé" in e.message for e in errors)

    def test_pivot_field_other_name_ok(self):
        pivot = _pivot("article_tags", "article_id", "tag_id",
                       fields=[{"name": "position", "type": "integer"}])
        rel = _relations([_m2m("Article", "Tag", "tags", pivot)])
        errors = _errors([ARTICLE, TAG], rel)
        assert not errors


class TestManyToManyDuplicateInverse:
    def test_inverse_declaration_is_error(self):
        pivot_ab = _pivot("article_tags", "article_id", "tag_id")
        pivot_ba = _pivot("tag_articles", "tag_id", "article_id")
        rel = _relations([
            _m2m("Article", "Tag", "tags", pivot_ab),
            _m2m("Tag", "Article", "articles", pivot_ba),
        ])
        errors = _errors([ARTICLE, TAG], rel)
        assert any("deux fois" in e.message for e in errors)

    def test_single_direction_ok(self):
        pivot = _pivot("article_tags", "article_id", "tag_id")
        rel = _relations([_m2m("Article", "Tag", "tags", pivot)])
        errors = _errors([ARTICLE, TAG], rel)
        assert not errors


# ── Tests de projet complet valide ────────────────────────────────────────────

class TestValidProject:
    def test_full_valid_project_no_errors(self):
        entities = [
            ("article.json", _entity("Article", "articles",
                                     fields=[
                                         {"name": "title", "type": "string"},
                                         {"name": "body", "type": "text"},
                                     ])),
            ("category.json", _entity("Category", "categories",
                                      fields=[{"name": "label", "type": "string"}])),
            ("tag.json", _entity("Tag", "tags",
                                 fields=[{"name": "name", "type": "string"}])),
        ]
        pivot = _pivot("article_tags", "article_id", "tag_id",
                       fields=[{"name": "position", "type": "integer"}])
        relations = _relations([
            _m2o("Article", "Category", "category"),
            _m2m("Article", "Tag", "tags", pivot),
        ])
        errors = validate_semantic(entities, relations)
        assert not errors, f"Erreurs inattendues : {[e.message for e in errors]}"


# ── Tests d'intégration CLI ───────────────────────────────────────────────────

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


_VALID_ENTITY = {
    "schema_version": "1.0",
    "name": "Article",
    "table": "articles",
    "fields": [{"name": "title", "type": "string"}],
}


class TestCLISemanticOutput:
    def test_duplicate_field_returns_nonzero(self, tmp_path):
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
        assert result.returncode != 0

    def test_semantic_error_mentioned_in_output(self, tmp_path):
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
        assert "sémantique" in result.stdout.lower() or "Validation" in result.stdout

    def test_reserved_word_returns_nonzero(self, tmp_path):
        entity = {
            "schema_version": "1.0",
            "name": "Article",
            "table": "articles",
            "fields": [{"name": "class", "type": "string"}],
        }
        proj = _make_project(tmp_path, {"article.json": entity})
        result = _run(proj)
        assert result.returncode != 0

    def test_legacy_files_fail_structurally_no_semantic_crash(self, tmp_path):
        legacy = {
            "format_version": 1,
            "entity": "Media",
            "table": "media",
            "fields": [{"name": "id", "column": "id", "python_type": "int", "sql_type": "INT"}],
        }
        proj = _make_project(tmp_path, {"media.json": legacy})
        result = _run(proj)
        assert result.returncode != 0
        assert "Raison" in result.stdout or "invalide" in result.stdout.lower()
