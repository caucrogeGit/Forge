"""Commande fixtures:generate (FIXTURES-GENERATE-001, ADR-076).

Sans base : le dialecte est injecté (SQLiteDialect). Vérifie le rendu des INSERT,
l'écriture write-if-new (§9), la reproductibilité par seed, et les erreurs.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("faker")
pytest.importorskip("forge_mvc_fixtures")
pytest.importorskip("forge_mvc_sqlite")

from forge_mvc_sqlite.dialect import SQLiteDialect

from forge_mvc_fixtures import FixtureReference
from forge_mvc_fixtures.cli.generate import (
    FIXTURE_TIMESTAMP,
    apply_timestamps,
    generate_fixtures,
    load_factory,
    render_inserts,
    render_value,
    timestamp_columns,
)

DIALECT = SQLiteDialect()

_FACTORY_SRC = '''
from forge_mvc_fixtures import Factory


class VilleFactory(Factory):
    table = "ville"

    def rows(self, count):
        return [{"nom": f"Ville {i}", "prefecture": i == 0} for i in range(count)]
'''


def _write_factory(root: Path, entity: str, src: str = _FACTORY_SRC) -> None:
    d = root / "mvc" / "fixtures" / "factories"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{entity}_factory.py").write_text(src, encoding="utf-8")


def _write_contract(root: Path, entity: str, *, timestamps: bool) -> None:
    import json

    d = root / "mvc" / "entities" / entity
    d.mkdir(parents=True, exist_ok=True)
    contract = {
        "name": entity.capitalize(),
        "table": entity,
        "fields": [],
        "options": {"timestamps": timestamps},
    }
    (d / f"{entity}.json").write_text(json.dumps(contract), encoding="utf-8")


class TestRenderInserts:

    def test_insert_lines(self) -> None:
        rows = [{"nom": "Lyon", "chef_lieu": True}, {"nom": "l'Isle", "chef_lieu": False}]
        sql = render_inserts("ville", rows, DIALECT)
        assert "INSERT INTO ville (nom, chef_lieu) VALUES ('Lyon', 1);" in sql
        # chaîne échappée + booléen SQLite 1/0
        assert "INSERT INTO ville (nom, chef_lieu) VALUES ('l''Isle', 0);" in sql

    def test_empty_rows(self) -> None:
        assert "Aucune ligne" in render_inserts("ville", [], DIALECT)


class TestFixtureReference:
    """F43 (ADR-077) : une référence devient une sous-requête résolue à la charge."""

    def test_render_value_plain_literal(self) -> None:
        assert render_value("Lyon", DIALECT) == "'Lyon'"

    def test_render_value_reference_subquery(self) -> None:
        ref = FixtureReference(table="users", key_column="Email", value="prof@ecole.fr")
        assert (
            render_value(ref, DIALECT)
            == "(SELECT Id FROM users WHERE Email = 'prof@ecole.fr' LIMIT 1)"
        )

    def test_render_value_reference_escapes_value(self) -> None:
        ref = FixtureReference(table="users", key_column="Nom", value="l'Isle")
        assert "WHERE Nom = 'l''Isle' LIMIT 1)" in render_value(ref, DIALECT)

    def test_insert_embeds_reference_subquery(self) -> None:
        ref = FixtureReference(table="users", key_column="Email", value="prof@ecole.fr")
        rows = [{"Nom": "Durand", "UserId": ref}]
        sql = render_inserts("eleve", rows, DIALECT)
        assert (
            "INSERT INTO eleve (Nom, UserId) VALUES "
            "('Durand', (SELECT Id FROM users WHERE Email = 'prof@ecole.fr' LIMIT 1));"
        ) in sql


class TestLoadFactory:

    def test_missing_factory_raises(self, tmp_path: Path) -> None:
        from forge_mvc_fixtures.cli.generate import GenerateError

        with pytest.raises(GenerateError, match="introuvable"):
            load_factory(tmp_path, "ville")

    def test_loads_subclass(self, tmp_path: Path) -> None:
        _write_factory(tmp_path, "ville")
        factory = load_factory(tmp_path, "ville")
        assert factory.table == "ville"


class TestGenerate:

    def test_writes_sql_file(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _write_factory(tmp_path, "ville")
        rc = generate_fixtures(tmp_path, "ville", rows=3, seed=1, force=False, dialect=DIALECT)
        assert rc == 0
        target = tmp_path / "mvc" / "fixtures" / "ville.sql"
        assert target.is_file()
        content = target.read_text(encoding="utf-8")
        assert content.count("INSERT INTO ville") == 3
        assert "Ville 0" in content
        assert "[OK]" in capsys.readouterr().out

    def test_write_if_new_refuses_existing(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _write_factory(tmp_path, "ville")
        target = tmp_path / "mvc" / "fixtures" / "ville.sql"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("-- déjà là\n", encoding="utf-8")
        rc = generate_fixtures(tmp_path, "ville", rows=2, seed=1, force=False, dialect=DIALECT)
        assert rc == 1
        assert target.read_text(encoding="utf-8") == "-- déjà là\n", "non écrasé sans --force"
        assert "Ajoutez --force" in capsys.readouterr().err

    def test_force_overwrites(self, tmp_path: Path) -> None:
        _write_factory(tmp_path, "ville")
        target = tmp_path / "mvc" / "fixtures" / "ville.sql"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("-- ancien\n", encoding="utf-8")
        rc = generate_fixtures(tmp_path, "ville", rows=2, seed=1, force=True, dialect=DIALECT)
        assert rc == 0
        assert "INSERT INTO ville" in target.read_text(encoding="utf-8")

    def test_seed_reproducible(self, tmp_path: Path) -> None:
        # Une factory qui utilise Faker : même seed -> même fichier.
        src = (
            "from forge_mvc_fixtures import Factory\n"
            "class VilleFactory(Factory):\n"
            "    table = 'ville'\n"
            "    def definition(self):\n"
            "        return {'nom': self.faker.city()}\n"
        )
        _write_factory(tmp_path, "ville", src)
        generate_fixtures(tmp_path, "ville", rows=5, seed=42, force=True, dialect=DIALECT)
        first = (tmp_path / "mvc" / "fixtures" / "ville.sql").read_text(encoding="utf-8")
        generate_fixtures(tmp_path, "ville", rows=5, seed=42, force=True, dialect=DIALECT)
        second = (tmp_path / "mvc" / "fixtures" / "ville.sql").read_text(encoding="utf-8")
        assert first == second

    def test_missing_factory_returns_2(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        rc = generate_fixtures(tmp_path, "ville", rows=3, seed=None, force=False, dialect=DIALECT)
        assert rc == 2
        assert "introuvable" in capsys.readouterr().err


class TestTimestamps:
    """F46 : timestamps NOT NULL posés automatiquement si l'entité les déclare."""

    def test_timestamp_columns_when_enabled(self, tmp_path: Path) -> None:
        _write_contract(tmp_path, "ville", timestamps=True)
        assert timestamp_columns(tmp_path, "ville") == ["CreatedAt", "UpdatedAt"]

    def test_timestamp_columns_when_disabled(self, tmp_path: Path) -> None:
        _write_contract(tmp_path, "ville", timestamps=False)
        assert timestamp_columns(tmp_path, "ville") == []

    def test_timestamp_columns_no_contract(self, tmp_path: Path) -> None:
        assert timestamp_columns(tmp_path, "ville") == []

    def test_apply_adds_missing_columns(self) -> None:
        rows = [{"Nom": "Lyon"}, {"Nom": "Nice"}]
        out = apply_timestamps(rows, ["CreatedAt", "UpdatedAt"])
        assert all(r["CreatedAt"] == FIXTURE_TIMESTAMP for r in out)
        assert all(r["UpdatedAt"] == FIXTURE_TIMESTAMP for r in out)

    def test_apply_respects_existing_column(self) -> None:
        # La factory a déjà fourni CreatedAt : non écrasé ; seul UpdatedAt ajouté.
        rows = [{"Nom": "Lyon", "CreatedAt": "2020-01-01 00:00:00"}]
        out = apply_timestamps(rows, ["CreatedAt", "UpdatedAt"])
        assert out[0]["CreatedAt"] == "2020-01-01 00:00:00"
        assert out[0]["UpdatedAt"] == FIXTURE_TIMESTAMP

    def test_apply_noop_without_columns(self) -> None:
        rows = [{"Nom": "Lyon"}]
        assert apply_timestamps(rows, []) == [{"Nom": "Lyon"}]

    def test_generate_emits_timestamps(self, tmp_path: Path) -> None:
        _write_factory(tmp_path, "ville")
        _write_contract(tmp_path, "ville", timestamps=True)
        rc = generate_fixtures(tmp_path, "ville", rows=2, seed=1, force=False, dialect=DIALECT)
        assert rc == 0
        content = (tmp_path / "mvc" / "fixtures" / "ville.sql").read_text(encoding="utf-8")
        assert "INSERT INTO ville (nom, prefecture, CreatedAt, UpdatedAt)" in content
        assert "'2024-01-01 00:00:00'" in content

    def test_generate_without_timestamps_unaffected(self, tmp_path: Path) -> None:
        _write_factory(tmp_path, "ville")
        _write_contract(tmp_path, "ville", timestamps=False)
        rc = generate_fixtures(tmp_path, "ville", rows=2, seed=1, force=False, dialect=DIALECT)
        assert rc == 0
        content = (tmp_path / "mvc" / "fixtures" / "ville.sql").read_text(encoding="utf-8")
        assert "CreatedAt" not in content

    def test_generate_no_contract_unaffected(self, tmp_path: Path) -> None:
        _write_factory(tmp_path, "ville")
        rc = generate_fixtures(tmp_path, "ville", rows=2, seed=1, force=False, dialect=DIALECT)
        assert rc == 0
        content = (tmp_path / "mvc" / "fixtures" / "ville.sql").read_text(encoding="utf-8")
        assert "CreatedAt" not in content
