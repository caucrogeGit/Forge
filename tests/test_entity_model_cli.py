import json
from pathlib import Path

import pytest

from forge_cli.entities.model import BuildModelResult, ModelValidationError, build_model, check_model, sync_relations


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_entity(root: Path, folder: str, data: dict) -> None:
    entity_dir = root / folder
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{folder}.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_relations(root: Path, data: dict) -> None:
    (root / "relations.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


# ── Fixtures canoniques ────────────────────────────────────────────────────────

def _article() -> dict:
    return {
        "schema_version": "1.0",
        "name": "Article",
        "table": "articles",
        "fields": [
            {"name": "title", "type": "string", "max_length": 255, "required": True},
        ],
    }


def _commande() -> dict:
    return {
        "schema_version": "1.0",
        "name": "Commande",
        "table": "commandes",
        "fields": [
            {"name": "reference", "type": "string", "max_length": 50},
        ],
    }


def _relations_vides() -> dict:
    # relations.json reste en legacy en attente de ENTITY-CONTRACT-011F
    return {"format_version": 1, "relations": []}


# ── Fixtures legacy (conservées pour les tests non migrés et la non-régression) ──

def _legacy_contact() -> dict:
    return {
        "format_version": 1,
        "entity": "Contact",
        "table": "contact",
        "description": "",
        "fields": [
            {
                "name": "id",
                "column": "Id",
                "python_type": "int",
                "sql_type": "INT",
                "nullable": False,
                "primary_key": True,
                "auto_increment": True,
                "constraints": {},
            }
        ],
    }


def _legacy_commande() -> dict:
    return {
        "format_version": 1,
        "entity": "Commande",
        "table": "commande",
        "description": "",
        "fields": [
            {
                "name": "id",
                "column": "Id",
                "python_type": "int",
                "sql_type": "INT",
                "nullable": False,
                "primary_key": True,
                "auto_increment": True,
                "constraints": {},
            },
            {
                "name": "contact_id",
                "column": "ContactId",
                "python_type": "int",
                "sql_type": "INT",
                "nullable": False,
                "primary_key": False,
                "auto_increment": False,
                "constraints": {},
            },
        ],
    }


def _legacy_relations() -> dict:
    return {
        "format_version": 1,
        "relations": [
            {
                "name": "commande_contact",
                "type": "many_to_one",
                "from_entity": "Commande",
                "to_entity": "Contact",
                "from_field": "contact_id",
                "to_field": "id",
                "foreign_key_name": "fk_commande_contact",
                "on_delete": "RESTRICT",
                "on_update": "CASCADE",
            }
        ],
    }


# ── sync:relations ────────────────────────────────────────────────────────────

def test_sync_relations_writes_only_relations_sql(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _legacy_contact())
    _write_entity(entities_root, "commande", _legacy_commande())
    _write_relations(entities_root, _legacy_relations())

    output = sync_relations(entities_root)

    assert output == entities_root / "relations.sql"
    assert output.read_text(encoding="utf-8").startswith("ALTER TABLE commande")
    assert not (entities_root / "contact" / "contact.sql").exists()
    assert not (entities_root / "commande" / "commande_base.py").exists()


# ── build:model ───────────────────────────────────────────────────────────────

def test_build_model_validates_then_writes(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _article())
    _write_entity(entities_root, "commande", _commande())
    _write_relations(entities_root, _relations_vides())

    result = build_model(entities_root)

    assert isinstance(result, BuildModelResult)
    assert entities_root / "article" / "article.sql" in result.written
    assert entities_root / "article" / "article_base.py" in result.written
    assert entities_root / "relations.sql" in result.written
    assert (entities_root / "article" / "article.py") in result.created
    assert (entities_root / "article" / "__init__.py") in result.created


def test_build_model_dry_run_necrit_aucun_fichier(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _article())
    _write_relations(entities_root, _relations_vides())

    result = build_model(entities_root, dry_run=True)

    assert result.dry_run is True
    assert entities_root / "article" / "article.sql" in result.written
    assert entities_root / "article" / "article_base.py" in result.written
    assert entities_root / "article" / "article.py" in result.created
    assert not (entities_root / "article" / "article.sql").exists()
    assert not (entities_root / "article" / "article_base.py").exists()
    assert not (entities_root / "article" / "article.py").exists()
    assert not (entities_root / "article" / "__init__.py").exists()
    assert not (entities_root / "relations.sql").exists()


def test_check_model_aggregates_entity_then_relations_errors(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    invalid = {
        "schema_version": "1.0",
        "name": "article",  # lowercase — invalide PascalCase
        "table": "articles",
        "fields": [{"name": "title", "type": "string", "max_length": 255}],
    }
    _write_entity(entities_root, "article", invalid)
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    with pytest.raises(ModelValidationError) as exc_info:
        check_model(entities_root)

    message = str(exc_info.value)
    assert "article/article.json: JSON d'entite invalide" in message
    assert "entity: doit etre un nom PascalCase valide" in message
    assert "relations.json: validation des relations impossible" in message


def test_build_model_writes_nothing_if_invalid(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    invalid = {
        "schema_version": "1.0",
        "name": "Article",
        "table": "Articles",  # majuscule — invalide
        "fields": [{"name": "title", "type": "string", "max_length": 255}],
    }
    _write_entity(entities_root, "article", invalid)
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    with pytest.raises(ModelValidationError):
        build_model(entities_root)

    assert not (entities_root / "article" / "article.sql").exists()
    assert not (entities_root / "article" / "article_base.py").exists()
    assert not (entities_root / "relations.sql").exists()


def test_check_model_rejects_duplicate_entities(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _article())
    duplicate = {
        "schema_version": "1.0",
        "name": "Article",  # même nom — dupliqué
        "table": "posts",
        "fields": [{"name": "title", "type": "string", "max_length": 255}],
    }
    _write_entity(entities_root, "post", duplicate)
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    with pytest.raises(ModelValidationError) as exc_info:
        check_model(entities_root)

    message = str(exc_info.value)
    assert "entity 'Article' deja declaree" in message


def test_check_model_rejects_duplicate_tables(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _article())
    other = {
        "schema_version": "1.0",
        "name": "Post",
        "table": "articles",  # même table — dupliquée
        "fields": [{"name": "title", "type": "string", "max_length": 255}],
    }
    _write_entity(entities_root, "post", other)
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    with pytest.raises(ModelValidationError) as exc_info:
        check_model(entities_root)

    message = str(exc_info.value)
    assert "table 'articles' deja declaree" in message


def test_check_model_accepts_explicit_table_name(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    entity = {
        "schema_version": "1.0",
        "name": "Article",
        "table": "crm_articles",
        "fields": [{"name": "title", "type": "string", "max_length": 255}],
    }
    _write_entity(entities_root, "article", entity)
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    check_model(entities_root)


def test_check_model_rejects_folder_entity_mismatch(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    entity = {
        "schema_version": "1.0",
        "name": "Post",
        "table": "posts",
        "fields": [{"name": "title", "type": "string", "max_length": 255}],
    }
    _write_entity(entities_root, "article", entity)  # dossier "article" ≠ entité "Post"
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    with pytest.raises(ModelValidationError) as exc_info:
        check_model(entities_root)

    message = str(exc_info.value)
    assert "le dossier d'entite 'article' doit correspondre a l'entite 'Post' ('post')" in message


def test_build_model_generates_correct_sql_and_base_py(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _article())
    _write_relations(entities_root, _relations_vides())

    result = build_model(entities_root)

    article_sql = (entities_root / "article" / "article.sql").read_text(encoding="utf-8")
    article_base = (entities_root / "article" / "article_base.py").read_text(encoding="utf-8")

    assert entities_root / "relations.sql" in result.written
    assert "PRIMARY KEY (Id)" in article_sql
    assert "Id BIGINT UNSIGNED NOT NULL" in article_sql
    assert "def __init__(self, title, id=None):" in article_base


# ── BuildModelResult — preserved files ───────────────────────────────────────

def test_build_model_preserves_existing_manual_py(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _article())
    _write_relations(entities_root, _relations_vides())
    manual = entities_root / "article" / "article.py"
    manual.write_text("# existant\n", encoding="utf-8")

    result = build_model(entities_root)

    assert manual in result.preserved
    assert manual not in result.created
    assert manual.read_text(encoding="utf-8") == "# existant\n"


def test_build_model_preserves_existing_init(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _article())
    _write_relations(entities_root, _relations_vides())
    init = entities_root / "article" / "__init__.py"
    init.write_text("# existant\n", encoding="utf-8")

    result = build_model(entities_root)

    assert init in result.preserved
    assert init not in result.created
    assert init.read_text(encoding="utf-8") == "# existant\n"


def test_build_model_reports_preserved_files(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _article())
    _write_relations(entities_root, _relations_vides())
    (entities_root / "article" / "article.py").write_text("# existant\n", encoding="utf-8")
    (entities_root / "article" / "__init__.py").write_text("# existant\n", encoding="utf-8")

    result = build_model(entities_root)

    assert len(result.preserved) == 2
    assert len(result.created) == 0


# ── BuildModelResult — dry-run ────────────────────────────────────────────────

def test_build_model_dry_run_creates_nothing(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _article())
    _write_relations(entities_root, _relations_vides())

    result = build_model(entities_root, dry_run=True)

    assert result.dry_run is True
    assert not (entities_root / "article" / "article.sql").exists()
    assert not (entities_root / "article" / "article_base.py").exists()
    assert not (entities_root / "article" / "article.py").exists()
    assert not (entities_root / "article" / "__init__.py").exists()
    assert not (entities_root / "relations.sql").exists()


def test_build_model_dry_run_modifies_nothing(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _article())
    _write_relations(entities_root, _relations_vides())
    manual = entities_root / "article" / "article.py"
    manual.write_text("# existant\n", encoding="utf-8")

    build_model(entities_root, dry_run=True)

    assert manual.read_text(encoding="utf-8") == "# existant\n"
    assert not (entities_root / "article" / "article.sql").exists()


def test_build_model_dry_run_shows_planned_writes(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _article())
    _write_relations(entities_root, _relations_vides())

    result = build_model(entities_root, dry_run=True)

    assert entities_root / "article" / "article.sql" in result.written
    assert entities_root / "article" / "article_base.py" in result.written
    assert entities_root / "relations.sql" in result.written
    assert entities_root / "article" / "article.py" in result.created
    assert entities_root / "article" / "__init__.py" in result.created


# ── check:model preview ───────────────────────────────────────────────────────

def test_check_model_preview_displays_entity_and_fields(tmp_path: Path, capsys):
    from forge_cli.entities.model import _print_check_model_preview

    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _article())
    _write_relations(entities_root, _relations_vides())

    entity_sources, _ = check_model(entities_root)
    _print_check_model_preview(entity_sources, entities_root)

    output = capsys.readouterr().out
    assert "Article" in output
    assert "articles" in output
    assert "id" in output
    assert "BIGINT" in output
    assert "article.sql" in output
    assert "article_base.py" in output
    assert "__init__.py" in output


# ── sync:entity — manual file not touched ─────────────────────────────────────

def test_sync_entity_does_not_touch_manual_py(tmp_path: Path):
    from forge_cli.entities.model import sync_entity

    entities_root = tmp_path / "mvc" / "entities"
    entity_dir = entities_root / "contact"
    entity_dir.mkdir(parents=True)
    (entity_dir / "contact.json").write_text(
        json.dumps(_legacy_contact(), indent=2), encoding="utf-8"
    )
    manual = entity_dir / "contact.py"
    manual.write_text("# existant\n", encoding="utf-8")

    sync_entity(entities_root, "Contact")

    assert manual.read_text(encoding="utf-8") == "# existant\n"


# ── Rejet legacy ─────────────────────────────────────────────────────────────

def test_legacy_build_model_is_rejected(tmp_path: Path):
    """build:model refuse les entités format_version: 1 depuis LEGACY-REMOVE-001A."""
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _legacy_contact())
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    with pytest.raises(ModelValidationError) as exc_info:
        build_model(entities_root)
    assert "format_version" in str(exc_info.value)


def test_legacy_check_model_is_rejected(tmp_path: Path):
    """check_model refuse les entités format_version: 1 depuis LEGACY-REMOVE-001A."""
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _legacy_contact())
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    with pytest.raises(ModelValidationError):
        check_model(entities_root)
