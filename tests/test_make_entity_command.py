import json
from pathlib import Path

import pytest

from forge_cli.entities import make_entity


def _configure_cli_roots(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)


def test_make_entity_no_input_preserves_scriptable_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys):
    _configure_cli_roots(monkeypatch, tmp_path)

    make_entity.main(["Contact", "--no-input"])

    entity_json = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    output = capsys.readouterr().out

    assert entity_json == {
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
    assert "Résumé avant écriture" not in output
    assert "modifier mvc/entities/contact/contact.json manuellement" in output


def test_make_entity_uses_current_working_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)

    make_entity.main(["Contact", "--no-input"])

    assert (tmp_path / "mvc" / "entities" / "contact" / "contact.json").exists()


def test_make_entity_interactive_builds_short_author_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys):
    _configure_cli_roots(monkeypatch, tmp_path)
    answers = iter(
        [
            "",
            "",
            "",
            "",
            "o",
            "nom",
            "VARCHAR",
            "100",
            "n",
            "n",
            "o",
            "",
            "100",
            "",
            "n",
            "o",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main(["Contact"])

    entity_json = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    output = capsys.readouterr().out

    assert entity_json == {
        "entity": "Contact",
        "fields": [
            {
                "name": "id",
                "sql_type": "INT",
                "primary_key": True,
                "auto_increment": True,
            },
            {
                "name": "nom",
                "sql_type": "VARCHAR(100)",
                "constraints": {
                    "not_empty": True,
                    "max_length": 100,
                },
            },
        ],
    }
    assert "Résumé avant écriture" in output
    assert '"entity": "Contact"' in output
    assert "modifier mvc/entities/contact/contact.json manuellement" in output


def test_make_entity_interactive_builds_char_sql_type(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _configure_cli_roots(monkeypatch, tmp_path)
    answers = iter(
        [
            "",
            "",
            "",
            "",
            "o",
            "code",
            "CHAR",
            "10",
            "n",
            "n",
            "o",
            "",
            "10",
            "",
            "n",
            "o",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main(["Contact"])

    entity_json = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    assert entity_json["fields"][1]["sql_type"] == "CHAR(10)"


def test_make_entity_interactive_builds_decimal_sql_type(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _configure_cli_roots(monkeypatch, tmp_path)
    answers = iter(
        [
            "",
            "",
            "",
            "",
            "o",
            "montant_ttc",
            "DECIMAL",
            "10",
            "2",
            "n",
            "n",
            "",
            "",
            "n",
            "o",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main(["Contact"])

    entity_json = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    assert entity_json["fields"][1]["sql_type"] == "DECIMAL(10,2)"


def test_make_entity_interactive_keeps_simple_sql_type(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _configure_cli_roots(monkeypatch, tmp_path)
    answers = iter(
        [
            "",
            "",
            "",
            "",
            "o",
            "date_naissance",
            "DATE",
            "o",
            "n",
            "n",
            "o",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main(["Contact"])

    entity_json = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    assert entity_json["fields"][1]["sql_type"] == "DATE"
    assert entity_json["fields"][1]["nullable"] is True


def test_make_entity_interactive_reprompts_on_invalid_sql_type(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys):
    _configure_cli_roots(monkeypatch, tmp_path)
    answers = iter(
        [
            "",
            "",
            "",
            "",
            "o",
            "nom",
            "foo",
            "varchar",
            "60",
            "n",
            "n",
            "o",
            "",
            "60",
            "",
            "n",
            "o",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main(["Contact"])

    entity_json = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    output = capsys.readouterr().out

    assert entity_json["fields"][1]["sql_type"] == "VARCHAR(60)"
    assert "Type SQL invalide." in output


def test_make_entity_interactive_can_ask_for_entity_name(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _configure_cli_roots(monkeypatch, tmp_path)
    answers = iter(
        [
            "Contact",
            "",
            "",
            "",
            "",
            "n",
            "o",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main([])

    entity_json = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    assert entity_json["entity"] == "Contact"
    assert entity_json["fields"][0]["name"] == "id"
