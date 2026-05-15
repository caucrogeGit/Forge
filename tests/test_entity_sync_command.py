from pathlib import Path

import pytest

from forge_cli.entities.model import sync_entity


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _contact_definition() -> str:
    return """{
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
      "nullable": false,
      "primary_key": true,
      "auto_increment": true,
      "constraints": {}
    },
    {
      "name": "nom",
      "column": "Nom",
      "python_type": "str",
      "sql_type": "VARCHAR(100)",
      "nullable": false,
      "primary_key": false,
      "auto_increment": false,
      "constraints": {
        "not_empty": true,
        "max_length": 100
      }
    }
  ]
}"""


def test_sync_entity_regenerates_only_sql_and_base(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    entity_dir = entities_root / "contact"
    _write(entity_dir / "contact.json", _contact_definition())
    _write(entity_dir / "contact.py", "# manuel\n")
    _write(entity_dir / "__init__.py", "from .contact import Contact\n")

    sql_path, base_path = sync_entity(entities_root, "Contact")

    assert sql_path == entity_dir / "contact.sql"
    assert base_path == entity_dir / "contact_base.py"
    assert sql_path.exists()
    assert base_path.exists()
    assert (entity_dir / "contact.py").read_text(encoding="utf-8") == "# manuel\n"
    assert (entity_dir / "__init__.py").read_text(encoding="utf-8") == "from .contact import Contact\n"
    assert not (entities_root / "relations.sql").exists()


def test_sync_entity_accepts_short_author_json(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    entity_dir = entities_root / "contact"
    _write(
        entity_dir / "contact.json",
        """{
  "entity": "Contact",
  "fields": [
    {
      "name": "id",
      "sql_type": "INT",
      "primary_key": true,
      "auto_increment": true
    },
    {
      "name": "date_naissance",
      "sql_type": "DATE"
    }
  ]
}""",
    )
    _write(entity_dir / "contact.py", "# manuel\n")
    _write(entity_dir / "__init__.py", "from .contact import Contact\n")

    sql_path, base_path = sync_entity(entities_root, "Contact")

    sql_content = sql_path.read_text(encoding="utf-8")
    base_content = base_path.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS contact" in sql_content
    assert "Id INT NOT NULL AUTO_INCREMENT" in sql_content
    assert "DateNaissance DATE NOT NULL" in sql_content
    assert "date.fromisoformat" in base_content


def test_sync_entity_fails_cleanly_if_entity_is_missing(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"

    with pytest.raises(ValueError, match="Entite introuvable : Contact"):
        sync_entity(entities_root, "Contact")


def test_sync_entity_fails_cleanly_if_json_is_missing(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    entity_dir = entities_root / "contact"
    entity_dir.mkdir(parents=True)

    with pytest.raises(ValueError, match="JSON d'entite introuvable"):
        sync_entity(entities_root, "Contact")


def test_sync_entity_writes_nothing_if_json_is_invalid(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    entity_dir = entities_root / "contact"
    _write(
        entity_dir / "contact.json",
        """{
  "format_version": 1,
  "entity": "contact",
  "table": "Contact",
  "description": "",
  "fields": []
}""",
    )
    _write(entity_dir / "contact.py", "# manuel\n")
    _write(entity_dir / "__init__.py", "from .contact import Contact\n")

    with pytest.raises(Exception):
        sync_entity(entities_root, "Contact")

    assert not (entity_dir / "contact.sql").exists()
    assert not (entity_dir / "contact_base.py").exists()
    assert (entity_dir / "contact.py").read_text(encoding="utf-8") == "# manuel\n"
    assert (entity_dir / "__init__.py").read_text(encoding="utf-8") == "from .contact import Contact\n"
