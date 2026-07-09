"""Garde-fou ENTITY-CONTRACT-018-MANY-TO-MANY-PIVOT-INTEGRATION-TESTS.

Tests d'intégration du flux complet :
  relations.json → entity:validate → build:model → SQL pivot généré.

Couvre : pivot minimal, pivot avec champs métier, collisions interdites,
non-régression many_to_one et legacy.
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


# ── Helpers ────────────────────────────────────────────────────────────────────

def _write_entity(entities_root: Path, snake_name: str, data: dict) -> None:
    entity_dir = entities_root / snake_name
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{snake_name}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def _write_relations(entities_root: Path, data: dict) -> None:
    (entities_root / "relations.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def _entities_root(tmp_path: Path) -> Path:
    return tmp_path / "mvc" / "entities"


def _canonical_article() -> dict:
    return {
        "schema_version": "1.0",
        "name": "Article",
        "table": "article",
        "fields": [
            {"name": "title", "type": "string", "max_length": 255, "required": True},
        ],
        "options": {"timestamps": False, "soft_delete": False},
    }


def _canonical_tag() -> dict:
    return {
        "schema_version": "1.0",
        "name": "Tag",
        "table": "tag",
        "fields": [
            {"name": "name", "type": "string", "max_length": 100, "required": True},
        ],
        "options": {"timestamps": False, "soft_delete": False},
    }


def _canonical_category() -> dict:
    return {
        "schema_version": "1.0",
        "name": "Category",
        "table": "category",
        "fields": [
            {"name": "label", "type": "string", "max_length": 100},
        ],
        "options": {"timestamps": False, "soft_delete": False},
    }


def _minimal_pivot_relations() -> dict:
    return {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_many",
                "from": "Article",
                "to": "Tag",
                "name": "tags",
                "pivot": {
                    "table": "article_tag",
                    "from_key": "article_id",
                    "to_key": "tag_id",
                    "id": True,
                    "unique_pair": True,
                    "on_delete": "cascade",
                    "fields": [],
                },
            }
        ],
    }


def _pivot_with_fields_relations() -> dict:
    return {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_many",
                "from": "Article",
                "to": "Tag",
                "name": "tags",
                "pivot": {
                    "table": "article_tag",
                    "from_key": "article_id",
                    "to_key": "tag_id",
                    "id": True,
                    "unique_pair": True,
                    "on_delete": "cascade",
                    "fields": [
                        {"name": "role", "type": "string", "max_length": 50, "required": True},
                        {"name": "joined_at", "type": "datetime", "nullable": True},
                    ],
                },
            }
        ],
    }


def _setup_article_tag(tmp_path: Path) -> Path:
    root = _entities_root(tmp_path)
    _write_entity(root, "article", _canonical_article())
    _write_entity(root, "tag", _canonical_tag())
    return root


def _run_validate(tmp_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FORGE_PY), "entity:validate"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )


def _sync_and_read_sql(entities_root: Path, relations: dict) -> str:
    """Valide relations.json et retourne le SQL pivot généré."""
    from forge_mvc_entities.relations import generate_relations_sql, validate_relations_definition
    validated = validate_relations_definition(
        relations, source="test", entities_root=entities_root
    )
    return generate_relations_sql(validated)


# ── Pivot minimal — flux Python API ───────────────────────────────────────────

class TestMinimalPivotSQL:
    def test_create_table_present(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _minimal_pivot_relations())
        assert "CREATE TABLE IF NOT EXISTS article_tag" in sql

    def test_id_technique_present(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _minimal_pivot_relations())
        assert "id INT NOT NULL AUTO_INCREMENT" in sql

    def test_primary_key_is_id(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _minimal_pivot_relations())
        assert "PRIMARY KEY (id)" in sql

    def test_from_key_column_present(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _minimal_pivot_relations())
        assert "article_id INT NOT NULL" in sql

    def test_to_key_column_present(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _minimal_pivot_relations())
        assert "tag_id INT NOT NULL" in sql

    def test_unique_key_on_pair(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _minimal_pivot_relations())
        assert "UNIQUE KEY uq_article_tag (article_id, tag_id)" in sql

    def test_foreign_key_source(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _minimal_pivot_relations())
        assert "FOREIGN KEY (article_id)" in sql
        assert "REFERENCES article (id)" in sql

    def test_foreign_key_target(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _minimal_pivot_relations())
        assert "FOREIGN KEY (tag_id)" in sql
        assert "REFERENCES tag (id)" in sql

    def test_on_delete_cascade(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _minimal_pivot_relations())
        assert "ON DELETE CASCADE" in sql

    def test_no_primary_key_composite(self, tmp_path):
        """La PK pivot est id, pas (article_id, tag_id)."""
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _minimal_pivot_relations())
        assert "PRIMARY KEY (article_id" not in sql


# ── Pivot avec champs métier — flux Python API ────────────────────────────────

class TestPivotWithFieldsSQL:
    def test_role_varchar_not_null(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _pivot_with_fields_relations())
        assert "role VARCHAR(50) NOT NULL" in sql

    def test_joined_at_datetime_null(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _pivot_with_fields_relations())
        assert "joined_at DATETIME NULL" in sql

    def test_unique_pair_still_present(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _pivot_with_fields_relations())
        assert "UNIQUE KEY uq_article_tag (article_id, tag_id)" in sql

    def test_foreign_keys_still_present(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _pivot_with_fields_relations())
        assert "FOREIGN KEY (article_id)" in sql
        assert "FOREIGN KEY (tag_id)" in sql

    def test_id_still_auto_increment(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _pivot_with_fields_relations())
        assert "AUTO_INCREMENT" in sql

    def test_fields_appear_before_primary_key(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _pivot_with_fields_relations())
        role_pos = sql.index("role")
        pk_pos = sql.index("PRIMARY KEY")
        assert role_pos < pk_pos

    def test_create_table_still_present(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _pivot_with_fields_relations())
        assert "CREATE TABLE IF NOT EXISTS article_tag" in sql


# ── Collisions interdites — flux Python API ───────────────────────────────────

class TestPivotCollisionsRejected:
    def _collision_doc(self, reserved_name: str) -> dict:
        return {
            "schema_version": "1.0",
            "relations": [
                {
                    "type": "many_to_many",
                    "from": "Article",
                    "to": "Tag",
                    "name": "tags",
                    "pivot": {
                        "table": "article_tag",
                        "from_key": "article_id",
                        "to_key": "tag_id",
                        "id": True,
                        "unique_pair": True,
                        "on_delete": "cascade",
                        "fields": [{"name": reserved_name, "type": "integer"}],
                    },
                }
            ],
        }

    def test_id_collision_raises(self, tmp_path):
        from forge_mvc_entities.relations import EntityRelationsError
        root = _setup_article_tag(tmp_path)
        with pytest.raises(EntityRelationsError) as exc_info:
            _sync_and_read_sql(root, self._collision_doc("id"))
        assert "nom reserve interdit" in str(exc_info.value)

    def test_from_key_collision_raises(self, tmp_path):
        from forge_mvc_entities.relations import EntityRelationsError
        root = _setup_article_tag(tmp_path)
        with pytest.raises(EntityRelationsError) as exc_info:
            _sync_and_read_sql(root, self._collision_doc("article_id"))
        assert "nom reserve interdit" in str(exc_info.value)

    def test_to_key_collision_raises(self, tmp_path):
        from forge_mvc_entities.relations import EntityRelationsError
        root = _setup_article_tag(tmp_path)
        with pytest.raises(EntityRelationsError) as exc_info:
            _sync_and_read_sql(root, self._collision_doc("tag_id"))
        assert "nom reserve interdit" in str(exc_info.value)

    def test_error_message_stable(self, tmp_path):
        """Le message d'erreur est stable et ne contient pas de trace Python."""
        from forge_mvc_entities.relations import EntityRelationsError
        root = _setup_article_tag(tmp_path)
        with pytest.raises(EntityRelationsError) as exc_info:
            _sync_and_read_sql(root, self._collision_doc("id"))
        err = str(exc_info.value)
        assert "Traceback" not in err
        assert "nom reserve interdit" in err

    def test_error_mentions_source(self, tmp_path):
        from forge_mvc_entities.relations import EntityRelationsError
        root = _setup_article_tag(tmp_path)
        with pytest.raises(EntityRelationsError) as exc_info:
            _sync_and_read_sql(root, self._collision_doc("id"))
        assert "test" in str(exc_info.value)


# ── entity:validate CLI — flux subprocess ────────────────────────────────────

class TestEntityValidateCLI:
    def test_minimal_pivot_returns_zero(self, tmp_path):
        """entity:validate retourne 0 pour un pivot minimal valide."""
        root = _entities_root(tmp_path)
        _write_entity(root, "article", _canonical_article())
        _write_entity(root, "tag", _canonical_tag())
        _write_relations(root, _minimal_pivot_relations())
        result = _run_validate(tmp_path)
        assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"

    def test_pivot_with_fields_returns_zero(self, tmp_path):
        """entity:validate retourne 0 pour un pivot avec champs métier valides."""
        root = _entities_root(tmp_path)
        _write_entity(root, "article", _canonical_article())
        _write_entity(root, "tag", _canonical_tag())
        _write_relations(root, _pivot_with_fields_relations())
        result = _run_validate(tmp_path)
        assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"

    def test_collision_id_returns_nonzero(self, tmp_path):
        """entity:validate retourne non nul si pivot.fields redéclare 'id'."""
        root = _entities_root(tmp_path)
        _write_entity(root, "article", _canonical_article())
        _write_entity(root, "tag", _canonical_tag())
        _write_relations(root, {
            "schema_version": "1.0",
            "relations": [{
                "type": "many_to_many",
                "from": "Article",
                "to": "Tag",
                "name": "tags",
                "pivot": {
                    "table": "article_tag",
                    "from_key": "article_id",
                    "to_key": "tag_id",
                    "id": True,
                    "unique_pair": True,
                    "on_delete": "cascade",
                    "fields": [{"name": "id", "type": "integer"}],
                },
            }],
        })
        result = _run_validate(tmp_path)
        assert result.returncode != 0, "entity:validate aurait dû échouer"

    def test_collision_from_key_returns_nonzero(self, tmp_path):
        root = _entities_root(tmp_path)
        _write_entity(root, "article", _canonical_article())
        _write_entity(root, "tag", _canonical_tag())
        _write_relations(root, {
            "schema_version": "1.0",
            "relations": [{
                "type": "many_to_many",
                "from": "Article",
                "to": "Tag",
                "name": "tags",
                "pivot": {
                    "table": "article_tag",
                    "from_key": "article_id",
                    "to_key": "tag_id",
                    "id": True,
                    "unique_pair": True,
                    "on_delete": "cascade",
                    "fields": [{"name": "article_id", "type": "integer"}],
                },
            }],
        })
        result = _run_validate(tmp_path)
        assert result.returncode != 0

    def test_valid_output_shows_ok(self, tmp_path):
        root = _entities_root(tmp_path)
        _write_entity(root, "article", _canonical_article())
        _write_entity(root, "tag", _canonical_tag())
        _write_relations(root, _minimal_pivot_relations())
        result = _run_validate(tmp_path)
        assert "[OK]" in result.stdout

    def test_no_traceback_on_collision(self, tmp_path):
        """En cas de collision, entity:validate ne produit pas de traceback Python."""
        root = _entities_root(tmp_path)
        _write_entity(root, "article", _canonical_article())
        _write_entity(root, "tag", _canonical_tag())
        _write_relations(root, {
            "schema_version": "1.0",
            "relations": [{
                "type": "many_to_many",
                "from": "Article",
                "to": "Tag",
                "name": "tags",
                "pivot": {
                    "table": "article_tag",
                    "from_key": "article_id",
                    "to_key": "tag_id",
                    "id": True,
                    "unique_pair": True,
                    "on_delete": "cascade",
                    "fields": [{"name": "id", "type": "integer"}],
                },
            }],
        })
        result = _run_validate(tmp_path)
        combined = result.stdout + result.stderr
        assert "Traceback" not in combined


# ── build:model — flux Python API ─────────────────────────────────────────────

class TestBuildModel:
    def test_sync_relations_writes_sql_file(self, tmp_path):
        """sync_relations() écrit le fichier relations.sql."""
        from forge_mvc_entities.model import sync_relations
        root = _setup_article_tag(tmp_path)
        _write_relations(root, _minimal_pivot_relations())
        output = sync_relations(root)
        assert output.exists()
        assert output.name == "relations.sql"

    def test_sql_file_contains_create_table(self, tmp_path):
        from forge_mvc_entities.model import sync_relations
        root = _setup_article_tag(tmp_path)
        _write_relations(root, _minimal_pivot_relations())
        output = sync_relations(root)
        sql = output.read_text(encoding="utf-8")
        assert "CREATE TABLE IF NOT EXISTS article_tag" in sql

    def test_sql_file_contains_pivot_fields(self, tmp_path):
        from forge_mvc_entities.model import sync_relations
        root = _setup_article_tag(tmp_path)
        _write_relations(root, _pivot_with_fields_relations())
        output = sync_relations(root)
        sql = output.read_text(encoding="utf-8")
        assert "role VARCHAR(50) NOT NULL" in sql
        assert "joined_at DATETIME NULL" in sql

    def test_build_model_does_not_raise_with_pivot(self, tmp_path):
        """build_model() ne lève pas d'exception avec un pivot canonique."""
        from forge_mvc_entities.model import build_model
        root = _setup_article_tag(tmp_path)
        _write_relations(root, _minimal_pivot_relations())
        result = build_model(root)
        assert result is not None

    def test_build_model_generates_entity_sql(self, tmp_path):
        """build_model() génère le SQL des entités Article et Tag."""
        from forge_mvc_entities.model import build_model
        root = _setup_article_tag(tmp_path)
        _write_relations(root, _minimal_pivot_relations())
        build_model(root)
        assert (root / "article" / "article.sql").exists()
        assert (root / "tag" / "tag.sql").exists()


# ── Non-régression sans pivot.fields ─────────────────────────────────────────

class TestEmptyFieldsNonRegression:
    def test_empty_fields_list_is_valid(self, tmp_path):
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _minimal_pivot_relations())
        assert "article_tag" in sql

    def test_empty_fields_no_extra_columns(self, tmp_path):
        """Un pivot sans champs métier contient exactement id, article_id, tag_id comme colonnes."""
        root = _setup_article_tag(tmp_path)
        sql = _sync_and_read_sql(root, _minimal_pivot_relations())
        assert "id INT NOT NULL AUTO_INCREMENT," in sql
        assert "article_id INT NOT NULL," in sql
        assert "tag_id INT NOT NULL," in sql
        # Pas de colonne métier supplémentaire
        assert sql.count("INT NOT NULL") == 3  # id, article_id, tag_id


# ── Non-régression many_to_one ────────────────────────────────────────────────

class TestManyToOneNonRegression:
    def test_m2o_canonical_not_broken(self, tmp_path):
        """many_to_one canonique continue de fonctionner après les tickets 016/017."""
        from forge_mvc_entities.relations import ValidatedRelation, validate_relations_definition
        root = _entities_root(tmp_path)
        _write_entity(root, "article", _canonical_article())
        _write_entity(root, "category", _canonical_category())
        doc = {
            "schema_version": "1.0",
            "relations": [{
                "type": "many_to_one",
                "from": "Article",
                "to": "Category",
                "name": "category",
                "foreign_key": "category_id",
                "on_delete": "restrict",
            }],
        }
        result = validate_relations_definition(doc, source="test", entities_root=root)
        assert len(result) == 1
        assert isinstance(result[0], ValidatedRelation)
        assert result[0].relation_type == "many_to_one"

    def test_m2o_sql_is_alter_table(self, tmp_path):
        root = _entities_root(tmp_path)
        _write_entity(root, "article", _canonical_article())
        _write_entity(root, "category", _canonical_category())
        doc = {
            "schema_version": "1.0",
            "relations": [{
                "type": "many_to_one",
                "from": "Article",
                "to": "Category",
                "name": "category",
                "foreign_key": "category_id",
                "on_delete": "restrict",
            }],
        }
        sql = _sync_and_read_sql(root, doc)
        assert "ALTER TABLE" in sql
        assert "FOREIGN KEY (category_id)" in sql
        assert "REFERENCES category" in sql

    def test_m2o_validate_cli_returns_zero(self, tmp_path):
        root = _entities_root(tmp_path)
        _write_entity(root, "article", _canonical_article())
        _write_entity(root, "category", _canonical_category())
        _write_relations(root, {
            "schema_version": "1.0",
            "relations": [{
                "type": "many_to_one",
                "from": "Article",
                "to": "Category",
                "name": "category",
                "foreign_key": "category_id",
                "on_delete": "restrict",
            }],
        })
        result = _run_validate(tmp_path)
        assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"


# ── Rejet du format legacy M2M ────────────────────────────────────────────────

class TestLegacyManyToManyNonRegression:
    def test_legacy_m2m_still_validates(self, tmp_path):
        """Le format legacy many_to_many (format_version: 1) est désormais refusé."""
        from forge_mvc_entities.relations import EntityRelationsError, validate_relations_definition
        root = _entities_root(tmp_path)
        _write_entity(root, "article", _canonical_article())
        _write_entity(root, "tag", _canonical_tag())
        doc = {
            "format_version": 1,
            "relations": [{
                "type": "many_to_many",
                "source": "article",
                "target": "tag",
                "pivot_table": "article_tag",
                "source_key": "article_id",
                "target_key": "tag_id",
            }],
        }
        with pytest.raises(EntityRelationsError) as exc_info:
            validate_relations_definition(doc, source="test", entities_root=root)
        assert "format_version" in str(exc_info.value)

    def test_legacy_m2m_sql_composite_pk(self, tmp_path):
        """Le format legacy (format_version: 1) est refusé avant génération SQL."""
        from forge_mvc_entities.relations import EntityRelationsError, validate_relations_definition
        root = _entities_root(tmp_path)
        _write_entity(root, "article", _canonical_article())
        _write_entity(root, "tag", _canonical_tag())
        doc = {
            "format_version": 1,
            "relations": [{
                "type": "many_to_many",
                "source": "article",
                "target": "tag",
                "pivot_table": "article_tag",
                "source_key": "article_id",
                "target_key": "tag_id",
            }],
        }
        with pytest.raises(EntityRelationsError):
            validate_relations_definition(doc, source="test", entities_root=root)

    def test_legacy_and_canonical_m2o_coexist(self, tmp_path):
        """Legacy M2M et M2O canonique peuvent coexister dans le même projet."""
        from forge_mvc_entities.relations import validate_relations_definition
        root = _entities_root(tmp_path)
        _write_entity(root, "article", _canonical_article())
        _write_entity(root, "tag", _canonical_tag())
        _write_entity(root, "category", _canonical_category())
        doc = {
            "schema_version": "1.0",
            "relations": [
                {
                    "type": "many_to_one",
                    "from": "Article",
                    "to": "Category",
                    "name": "category",
                    "foreign_key": "category_id",
                    "on_delete": "restrict",
                },
                {
                    "type": "many_to_many",
                    "from": "Article",
                    "to": "Tag",
                    "name": "tags",
                    "pivot": {
                        "table": "article_tag",
                        "from_key": "article_id",
                        "to_key": "tag_id",
                        "id": True,
                        "unique_pair": True,
                        "on_delete": "cascade",
                        "fields": [],
                    },
                },
            ],
        }
        result = validate_relations_definition(doc, source="test", entities_root=root)
        assert len(result) == 2
