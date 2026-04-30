import json
from pathlib import Path

import pytest

from forge_cli.entities.model import BuildModelResult, ModelValidationError, build_model, check_model, sync_relations


def _write_entity(root: Path, folder: str, data: dict) -> None:
    entity_dir = root / folder
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{folder}.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_relations(root: Path, data: dict) -> None:
    (root / "relations.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _contact() -> dict:
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


def _commande() -> dict:
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


def _relations() -> dict:
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


def test_sync_relations_writes_only_relations_sql(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact())
    _write_entity(entities_root, "commande", _commande())
    _write_relations(entities_root, _relations())

    output = sync_relations(entities_root)

    assert output == entities_root / "relations.sql"
    assert output.read_text(encoding="utf-8").startswith("ALTER TABLE commande")
    assert not (entities_root / "contact" / "contact.sql").exists()
    assert not (entities_root / "commande" / "commande_base.py").exists()


def test_build_model_validates_then_writes(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact())
    _write_entity(entities_root, "commande", _commande())
    _write_relations(entities_root, _relations())

    result = build_model(entities_root)

    assert isinstance(result, BuildModelResult)
    assert entities_root / "contact" / "contact.sql" in result.written
    assert entities_root / "contact" / "contact_base.py" in result.written
    assert entities_root / "relations.sql" in result.written
    assert (entities_root / "contact" / "contact.py") in result.created
    assert (entities_root / "contact" / "__init__.py") in result.created


def test_build_model_dry_run_necrit_aucun_fichier(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact())
    _write_entity(entities_root, "commande", _commande())
    _write_relations(entities_root, _relations())

    result = build_model(entities_root, dry_run=True)

    assert result.dry_run is True
    assert entities_root / "contact" / "contact.sql" in result.written
    assert entities_root / "contact" / "contact_base.py" in result.written
    assert entities_root / "contact" / "contact.py" in result.created
    assert not (entities_root / "contact" / "contact.sql").exists()
    assert not (entities_root / "contact" / "contact_base.py").exists()
    assert not (entities_root / "contact" / "contact.py").exists()
    assert not (entities_root / "contact" / "__init__.py").exists()
    assert not (entities_root / "relations.sql").exists()


def test_check_model_aggregates_entity_then_relations_errors(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    contact = _contact()
    contact["entity"] = "contact"
    _write_entity(entities_root, "contact", contact)
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    with pytest.raises(ModelValidationError) as exc_info:
        check_model(entities_root)

    message = str(exc_info.value)
    assert "contact/contact.json: JSON d'entite invalide" in message
    assert "entity: doit etre un nom PascalCase valide" in message
    assert "relations.json: validation des relations impossible" in message


def test_build_model_writes_nothing_if_invalid(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    contact = _contact()
    contact["table"] = "Contact"
    _write_entity(entities_root, "contact", contact)
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    with pytest.raises(ModelValidationError):
        build_model(entities_root)

    assert not (entities_root / "contact" / "contact.sql").exists()
    assert not (entities_root / "contact" / "contact_base.py").exists()
    assert not (entities_root / "relations.sql").exists()


def test_check_model_rejects_duplicate_entities(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    duplicate_entity = _contact()
    duplicate_entity["table"] = "client"
    _write_entity(entities_root, "contact", _contact())
    _write_entity(entities_root, "client", duplicate_entity)
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    with pytest.raises(ModelValidationError) as exc_info:
        check_model(entities_root)

    message = str(exc_info.value)
    assert "entity 'Contact' deja declaree" in message


def test_check_model_rejects_duplicate_tables(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    client = _contact()
    client["entity"] = "Client"
    client["table"] = "contact"
    _write_entity(entities_root, "contact", _contact())
    _write_entity(entities_root, "client", client)
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    with pytest.raises(ModelValidationError) as exc_info:
        check_model(entities_root)

    message = str(exc_info.value)
    assert "table 'contact' deja declaree" in message


def test_check_model_accepts_explicit_table_name(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    contact = _contact()
    contact["table"] = "crm_contact"
    _write_entity(entities_root, "contact", contact)
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    check_model(entities_root)


def test_check_model_rejects_folder_entity_mismatch(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    client = _contact()
    client["entity"] = "Client"
    client["table"] = "client"
    _write_entity(entities_root, "contact", client)
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    with pytest.raises(ModelValidationError) as exc_info:
        check_model(entities_root)

    message = str(exc_info.value)
    assert "le dossier d'entite 'contact' doit correspondre a l'entite 'Client' ('client')" in message


def test_build_model_accepts_short_and_mixed_entity_json(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(
        entities_root,
        "contact",
        {
            "entity": "Contact",
            "fields": [
                {
                    "name": "id",
                    "sql_type": "INT",
                    "primary_key": True,
                    "auto_increment": True,
                }
            ],
        },
    )
    _write_entity(
        entities_root,
        "commande",
        {
            "entity": "Commande",
            "table": "commande",
            "fields": [
                {
                    "name": "id",
                    "sql_type": "INT",
                    "primary_key": True,
                    "auto_increment": True,
                },
                {
                    "name": "contact_id",
                    "column": "ContactId",
                    "python_type": "int",
                    "sql_type": "INT",
                },
            ],
        },
    )
    _write_relations(entities_root, _relations())

    result = build_model(entities_root)

    contact_sql = (entities_root / "contact" / "contact.sql").read_text(encoding="utf-8")
    commande_base = (entities_root / "commande" / "commande_base.py").read_text(encoding="utf-8")

    assert entities_root / "relations.sql" in result.written
    assert "PRIMARY KEY (Id)" in contact_sql
    assert "Id INT NOT NULL" in contact_sql
    assert "def __init__(self, contact_id, id=None):" in commande_base


# ── BuildModelResult — preserved files ───────────────────────────────────────

def test_build_model_preserves_existing_manual_py(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact())
    _write_relations(entities_root, {"format_version": 1, "relations": []})
    manual = entities_root / "contact" / "contact.py"
    manual.write_text("# existant\n", encoding="utf-8")

    result = build_model(entities_root)

    assert manual in result.preserved
    assert manual not in result.created
    assert manual.read_text(encoding="utf-8") == "# existant\n"


def test_build_model_preserves_existing_init(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact())
    _write_relations(entities_root, {"format_version": 1, "relations": []})
    init = entities_root / "contact" / "__init__.py"
    init.write_text("# existant\n", encoding="utf-8")

    result = build_model(entities_root)

    assert init in result.preserved
    assert init not in result.created
    assert init.read_text(encoding="utf-8") == "# existant\n"


def test_build_model_reports_preserved_files(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact())
    _write_relations(entities_root, {"format_version": 1, "relations": []})
    (entities_root / "contact" / "contact.py").write_text("# existant\n", encoding="utf-8")
    (entities_root / "contact" / "__init__.py").write_text("# existant\n", encoding="utf-8")

    result = build_model(entities_root)

    assert len(result.preserved) == 2
    assert len(result.created) == 0


# ── BuildModelResult — dry-run ────────────────────────────────────────────────

def test_build_model_dry_run_creates_nothing(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact())
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    result = build_model(entities_root, dry_run=True)

    assert result.dry_run is True
    assert not (entities_root / "contact" / "contact.sql").exists()
    assert not (entities_root / "contact" / "contact_base.py").exists()
    assert not (entities_root / "contact" / "contact.py").exists()
    assert not (entities_root / "contact" / "__init__.py").exists()
    assert not (entities_root / "relations.sql").exists()


def test_build_model_dry_run_modifies_nothing(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact())
    _write_relations(entities_root, {"format_version": 1, "relations": []})
    manual = entities_root / "contact" / "contact.py"
    manual.write_text("# existant\n", encoding="utf-8")

    build_model(entities_root, dry_run=True)

    assert manual.read_text(encoding="utf-8") == "# existant\n"
    assert not (entities_root / "contact" / "contact.sql").exists()


def test_build_model_dry_run_shows_planned_writes(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact())
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    result = build_model(entities_root, dry_run=True)

    assert entities_root / "contact" / "contact.sql" in result.written
    assert entities_root / "contact" / "contact_base.py" in result.written
    assert entities_root / "relations.sql" in result.written
    assert entities_root / "contact" / "contact.py" in result.created
    assert entities_root / "contact" / "__init__.py" in result.created


# ── sync:entity — manual file not touched ─────────────────────────────────────

def test_check_model_preview_displays_entity_and_fields(tmp_path: Path, capsys):
    from forge_cli.entities.model import _print_check_model_preview

    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _contact())
    _write_relations(entities_root, {"format_version": 1, "relations": []})

    entity_sources, _ = check_model(entities_root)
    _print_check_model_preview(entity_sources, entities_root)

    output = capsys.readouterr().out
    assert "Contact" in output
    assert "contact" in output
    assert "id" in output
    assert "INT" in output
    assert "contact.sql" in output
    assert "contact_base.py" in output
    assert "__init__.py" in output


def test_sync_entity_does_not_touch_manual_py(tmp_path: Path):
    from forge_cli.entities.model import sync_entity

    entities_root = tmp_path / "mvc" / "entities"
    entity_dir = entities_root / "contact"
    entity_dir.mkdir(parents=True)
    (entity_dir / "contact.json").write_text(
        json.dumps(_contact(), indent=2), encoding="utf-8"
    )
    manual = entity_dir / "contact.py"
    manual.write_text("# existant\n", encoding="utf-8")

    sync_entity(entities_root, "Contact")

    assert manual.read_text(encoding="utf-8") == "# existant\n"
