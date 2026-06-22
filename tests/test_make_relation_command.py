import json
from pathlib import Path

import pytest

from cli.entities import make_relation


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


def _canonical_relation_contact() -> dict:
    return {
        "type": "many_to_one",
        "from": "ContactGroupe",
        "to": "Contact",
        "name": "contact",
        "foreign_key": "contact_id",
        "nullable": True,
        "on_delete": "cascade",
        "index": True,
    }


def test_make_relation_creates_relations_json_and_appends_relation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys):
    entities_dir = _configure_roots(monkeypatch, tmp_path)
    _write_entity(entities_dir, "contact", _contact())
    _write_entity(entities_dir, "groupe", _groupe())
    _write_entity(entities_dir, "contact_groupe", _contact_groupe())

    answers = iter(
        [
            "",             # type (many_to_one)
            "ContactGroupe",# from
            "Contact",      # to
            "contact",      # name
            "",             # inverse_name (empty)
            "",             # foreign_key (default: contact_id)
            "",             # nullable (default: True)
            "",             # on_delete (default: restrict)
            "",             # index (default: True)
            "o",            # confirm
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_relation.main([])

    relations_json = json.loads((entities_dir / "relations.json").read_text(encoding="utf-8"))
    output = capsys.readouterr().out

    assert relations_json == {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_one",
                "from": "ContactGroupe",
                "to": "Contact",
                "name": "contact",
                "foreign_key": "contact_id",
                "nullable": True,
                "on_delete": "restrict",
                "index": True,
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
            "",
            "",
            "",
            "",
            "o",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_relation.main([])

    assert (tmp_path / "mvc" / "entities" / "relations.json").exists()


def test_make_relation_preserves_existing_relations_and_appends_second(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    entities_dir = _configure_roots(monkeypatch, tmp_path)
    _write_entity(entities_dir, "contact", _contact())
    _write_entity(entities_dir, "groupe", _groupe())
    _write_entity(entities_dir, "contact_groupe", _contact_groupe())
    (entities_dir / "relations.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "relations": [_canonical_relation_contact()],
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
            "",
            "",
            "",
            "",
            "o",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_relation.main([])

    relations_json = json.loads((entities_dir / "relations.json").read_text(encoding="utf-8"))
    assert relations_json["schema_version"] == "1.0"
    assert len(relations_json["relations"]) == 2
    assert relations_json["relations"][1]["to"] == "Groupe"
    assert relations_json["relations"][1]["name"] == "groupe"
    assert relations_json["relations"][1]["foreign_key"] == "groupe_id"


def test_make_relation_rejects_obvious_duplicate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    entities_dir = _configure_roots(monkeypatch, tmp_path)
    _write_entity(entities_dir, "contact", _contact())
    _write_entity(entities_dir, "contact_groupe", _contact_groupe())
    (entities_dir / "relations.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "relations": [_canonical_relation_contact()],
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
            "contact",      # same name → duplicate
            "",
            "",
            "",
            "",
            "",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    with pytest.raises(SystemExit, match="1"):
        make_relation.main([])


def test_make_relation_many_to_many_writes_canonical_relation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys):
    entities_dir = _configure_roots(monkeypatch, tmp_path)
    _write_entity(entities_dir, "contact", _contact())
    _write_entity(entities_dir, "groupe", _groupe())

    answers = iter(
        [
            "many_to_many", # type
            "Contact",      # from entity
            "Groupe",       # to entity
            "",             # name (default: "groupes")
            "",             # inverse_name (empty)
            "",             # pivot table (default: "contact_groupe")
            "",             # from_key (default: "contact_id")
            "",             # to_key (default: "groupe_id")
            "",             # on_delete (default: "cascade")
            "o",            # confirm
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_relation.main([])

    relations_json = json.loads((entities_dir / "relations.json").read_text(encoding="utf-8"))
    output = capsys.readouterr().out

    assert relations_json["schema_version"] == "1.0"
    assert len(relations_json["relations"]) == 1
    relation = relations_json["relations"][0]
    assert relation["type"] == "many_to_many"
    assert relation["from"] == "Contact"
    assert relation["to"] == "Groupe"
    assert relation["name"] == "groupes"
    assert relation["pivot"]["table"] == "contact_groupe"
    assert relation["pivot"]["from_key"] == "contact_id"
    assert relation["pivot"]["to_key"] == "groupe_id"
    assert relation["pivot"]["id"] is True
    assert relation["pivot"]["unique_pair"] is True
    assert relation["pivot"]["on_delete"] == "cascade"
    assert "Résumé avant écriture" in output
    assert "forge sync:relations" in output
