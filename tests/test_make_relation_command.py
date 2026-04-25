import json
from pathlib import Path

import pytest

from forge_cli.entities import make_relation


def _configure_roots(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    entities_dir = tmp_path / "mvc" / "entities"
    monkeypatch.chdir(tmp_path)
    return entities_dir


def _write_entity(entities_dir: Path, folder: str, data: dict) -> None:
    entity_dir = entities_dir / folder
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{folder}.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _contact() -> dict:
    return {
        "entity": "Contact",
        "fields": [
            {
                "name": "id",
                "sql_type": "INT",
                "primary_key": True,
                "auto_increment": True,
            }
        ],
    }


def _groupe() -> dict:
    return {
        "entity": "Groupe",
        "fields": [
            {
                "name": "id",
                "sql_type": "INT",
                "primary_key": True,
                "auto_increment": True,
            }
        ],
    }


def _contact_groupe() -> dict:
    return {
        "entity": "ContactGroupe",
        "fields": [
            {
                "name": "id",
                "sql_type": "INT",
                "primary_key": True,
                "auto_increment": True,
            },
            {
                "name": "contact_id",
                "sql_type": "INT",
            },
            {
                "name": "groupe_id",
                "sql_type": "INT",
            },
        ],
    }


def test_make_relation_creates_relations_json_and_appends_relation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys):
    entities_dir = _configure_roots(monkeypatch, tmp_path)
    _write_entity(entities_dir, "contact", _contact())
    _write_entity(entities_dir, "groupe", _groupe())
    _write_entity(entities_dir, "contact_groupe", _contact_groupe())

    answers = iter(
        [
            "",
            "ContactGroupe",
            "Contact",
            "",
            "",
            "contact_groupe_contact",
            "fk_contact_groupe_contact",
            "",
            "",
            "o",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_relation.main([])

    relations_json = json.loads((entities_dir / "relations.json").read_text(encoding="utf-8"))
    output = capsys.readouterr().out

    assert relations_json == {
        "format_version": 1,
        "relations": [
            {
                "name": "contact_groupe_contact",
                "type": "many_to_one",
                "from_entity": "ContactGroupe",
                "to_entity": "Contact",
                "from_field": "contact_id",
                "to_field": "id",
                "foreign_key_name": "fk_contact_groupe_contact",
                "on_delete": "RESTRICT",
                "on_update": "CASCADE",
            }
        ],
    }
    assert "Résumé avant écriture" in output
    assert '"type": "many_to_one"' in output
    assert "forge sync:relations" in output


def test_make_relation_uses_current_working_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    entities_dir = _configure_roots(monkeypatch, tmp_path)
    _write_entity(entities_dir, "contact", _contact())
    _write_entity(entities_dir, "contact_groupe", _contact_groupe())

    answers = iter(
        [
            "",
            "ContactGroupe",
            "Contact",
            "",
            "",
            "contact_groupe_contact",
            "fk_contact_groupe_contact",
            "",
            "",
            "o",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_relation.main([])

    assert (tmp_path / "mvc" / "entities" / "relations.json").exists()


def test_make_relation_preserves_format_version_and_existing_relations(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    entities_dir = _configure_roots(monkeypatch, tmp_path)
    _write_entity(entities_dir, "contact", _contact())
    _write_entity(entities_dir, "groupe", _groupe())
    _write_entity(entities_dir, "contact_groupe", _contact_groupe())
    (entities_dir / "relations.json").write_text(
        json.dumps(
            {
                "format_version": 1,
                "relations": [
                    {
                        "name": "contact_groupe_contact",
                        "type": "many_to_one",
                        "from_entity": "ContactGroupe",
                        "to_entity": "Contact",
                        "from_field": "contact_id",
                        "to_field": "id",
                        "foreign_key_name": "fk_contact_groupe_contact",
                        "on_delete": "CASCADE",
                        "on_update": "CASCADE",
                    }
                ],
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    answers = iter(
        [
            "",
            "ContactGroupe",
            "Groupe",
            "",
            "",
            "contact_groupe_groupe",
            "fk_contact_groupe_groupe",
            "CASCADE",
            "",
            "o",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_relation.main([])

    relations_json = json.loads((entities_dir / "relations.json").read_text(encoding="utf-8"))
    assert relations_json["format_version"] == 1
    assert len(relations_json["relations"]) == 2
    assert relations_json["relations"][1]["to_field"] == "id"
    assert relations_json["relations"][1]["from_field"] == "groupe_id"


def test_make_relation_rejects_obvious_duplicate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    entities_dir = _configure_roots(monkeypatch, tmp_path)
    _write_entity(entities_dir, "contact", _contact())
    _write_entity(entities_dir, "contact_groupe", _contact_groupe())
    (entities_dir / "relations.json").write_text(
        json.dumps(
            {
                "format_version": 1,
                "relations": [
                    {
                        "name": "contact_groupe_contact",
                        "type": "many_to_one",
                        "from_entity": "ContactGroupe",
                        "to_entity": "Contact",
                        "from_field": "contact_id",
                        "to_field": "id",
                        "foreign_key_name": "fk_contact_groupe_contact",
                        "on_delete": "RESTRICT",
                        "on_update": "CASCADE",
                    }
                ],
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    answers = iter(
        [
            "",
            "ContactGroupe",
            "Contact",
            "",
            "",
            "contact_groupe_contact",
            "fk_contact_groupe_contact",
            "",
            "",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    with pytest.raises(SystemExit, match="1"):
        make_relation.main([])


def test_make_relation_explains_many_to_many_is_not_directly_supported(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys):
    entities_dir = _configure_roots(monkeypatch, tmp_path)
    _write_entity(entities_dir, "contact", _contact())
    _write_entity(entities_dir, "contact_groupe", _contact_groupe())

    answers = iter(
        [
            "many_to_many",
            "",
            "ContactGroupe",
            "Contact",
            "",
            "",
            "contact_groupe_contact",
            "fk_contact_groupe_contact",
            "",
            "",
            "n",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    with pytest.raises(SystemExit, match="0"):
        make_relation.main([])

    output = capsys.readouterr().out
    assert "ne supporte pas many_to_many directement" in output
    assert "Aucune écriture effectuée." in output
