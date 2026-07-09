import json
from pathlib import Path

import pytest

from forge_mvc_entities import make_entity


def _configure_cli_roots(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)


def test_make_entity_no_input_preserves_scriptable_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys):
    _configure_cli_roots(monkeypatch, tmp_path)

    make_entity.main(["Contact", "--no-input"])

    entity_json = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    output = capsys.readouterr().out

    assert entity_json == {
        "schema_version": "1.0",
        "name": "Contact",
        "table": "contact",
        "fields": [{"name": "title", "type": "string", "max_length": 255, "required": True}],
        "options": {"timestamps": False, "soft_delete": False},
    }
    assert "Résumé avant écriture" not in output
    assert "modifier mvc/entities/contact/contact.json manuellement" in output


def test_make_entity_uses_current_working_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)

    make_entity.main(["Contact", "--no-input"])

    assert (tmp_path / "mvc" / "entities" / "contact" / "contact.json").exists()


def test_make_entity_interactive_builds_canonical_author_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys):
    _configure_cli_roots(monkeypatch, tmp_path)
    answers = iter(
        [
            "",       # table name (default: contact)
            "nom",    # first field name
            "string", # forge type
            "100",    # max_length
            "",       # required? (default: yes)
            "n",      # nullable? (no)
            "n",      # unique? (no)
            "n",      # add another field?
            "n",      # timestamps?
            "n",      # soft_delete?
            "o",      # confirm write?
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main(["Contact"])

    entity_json = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    output = capsys.readouterr().out

    assert entity_json == {
        "schema_version": "1.0",
        "name": "Contact",
        "table": "contact",
        "fields": [
            {
                "name": "nom",
                "type": "string",
                "max_length": 100,
                "required": True,
                "nullable": False,
                "unique": False,
            },
        ],
        "options": {"timestamps": False, "soft_delete": False},
    }
    assert "Résumé avant écriture" in output
    assert '"name": "Contact"' in output
    assert "modifier mvc/entities/contact/contact.json manuellement" in output


def test_make_entity_interactive_builds_integer_field(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _configure_cli_roots(monkeypatch, tmp_path)
    answers = iter(
        [
            "",         # table name
            "quantite", # field name
            "integer",  # forge type
            "",         # required? (yes)
            "n",        # nullable?
            "n",        # unique?
            "n",        # add another field?
            "n",        # timestamps?
            "n",        # soft_delete?
            "o",        # confirm write?
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main(["Contact"])

    entity_json = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    assert entity_json["fields"][0]["type"] == "integer"
    assert entity_json["fields"][0]["name"] == "quantite"


def test_make_entity_interactive_builds_decimal_field(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _configure_cli_roots(monkeypatch, tmp_path)
    answers = iter(
        [
            "",            # table name
            "montant_ttc", # field name
            "decimal",     # forge type
            "10",          # precision
            "2",           # scale
            "",            # required? (yes)
            "n",           # nullable?
            "n",           # unique?
            "n",           # add another field?
            "n",           # timestamps?
            "n",           # soft_delete?
            "o",           # confirm write?
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main(["Contact"])

    entity_json = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    assert entity_json["fields"][0]["type"] == "decimal"
    assert entity_json["fields"][0]["precision"] == 10
    assert entity_json["fields"][0]["scale"] == 2


def test_make_entity_interactive_builds_date_nullable_field(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _configure_cli_roots(monkeypatch, tmp_path)
    answers = iter(
        [
            "",               # table name
            "date_naissance", # field name
            "date",           # forge type
            "n",              # required? (no)
            "o",              # nullable? (yes)
            "n",              # unique?
            "n",              # add another field?
            "n",              # timestamps?
            "n",              # soft_delete?
            "o",              # confirm write?
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main(["Contact"])

    entity_json = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    assert entity_json["fields"][0]["type"] == "date"
    assert entity_json["fields"][0]["nullable"] is True


def test_make_entity_interactive_reprompts_on_invalid_forge_type(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys):
    _configure_cli_roots(monkeypatch, tmp_path)
    answers = iter(
        [
            "",        # table name
            "nom",     # field name
            "foo",     # invalid forge type
            "varchar", # still invalid
            "string",  # valid
            "60",      # max_length
            "",        # required? (yes)
            "n",       # nullable?
            "n",       # unique?
            "n",       # add another field?
            "n",       # timestamps?
            "n",       # soft_delete?
            "o",       # confirm write?
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main(["Contact"])

    entity_json = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    output = capsys.readouterr().out

    assert entity_json["fields"][0]["type"] == "string"
    assert "Type invalide." in output


def test_make_entity_interactive_can_ask_for_entity_name(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _configure_cli_roots(monkeypatch, tmp_path)
    answers = iter(
        [
            "Contact",  # entity name (prompted when not passed as arg)
            "",         # table name
            "titre",    # first field name
            "string",   # forge type
            "",         # max_length (none)
            "",         # required? (yes)
            "n",        # nullable?
            "n",        # unique?
            "n",        # add another field?
            "n",        # timestamps?
            "n",        # soft_delete?
            "o",        # confirm write?
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main([])

    entity_json = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    assert entity_json["name"] == "Contact"
    assert entity_json["fields"][0]["name"] == "titre"


def test_build_entity_init_reexport_explicite():
    # FORGE-7 : le __init__.py d'entité ré-exporte via un alias redondant
    # (from .x import X as X), reconnu comme ré-export explicite -> pas de F401.
    init = make_entity.build_entity_init("Contact")
    assert init == "from .contact import Contact as Contact\n"
