"""Fixtures callable (FIXTURES-CALLABLE-001, ADR-078).

Classe de base Fixture, découverte des mvc/fixtures/*.py, ordre unifié avec les
.sql, exécution par fixtures:load et démontage par fixtures:purge. Sans base
réelle : core.database.db est mocké.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_fixtures")

from forge_mvc_fixtures import Fixture
from forge_mvc_fixtures.cli.load import (
    FixtureDiscoveryError,
    collect_callable_fixtures,
    collect_fixture_files,
    load_fixtures,
    order_load_units,
)
from forge_mvc_fixtures.cli.purge import purge_fixtures


def _write_callable(root: Path, name: str, src: str) -> None:
    d = root / "mvc" / "fixtures"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(src, encoding="utf-8")


def _write_sql(root: Path, name: str, sql: str) -> None:
    d = root / "mvc" / "fixtures"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(sql, encoding="utf-8")


def _write_entity(root: Path, snake: str, name: str, table: str) -> None:
    d = root / "mvc" / "entities" / snake
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{snake}.json").write_text(
        json.dumps({"name": name, "table": table, "fields": []}), encoding="utf-8"
    )


def _write_relations(root: Path, relations: list[dict]) -> None:
    d = root / "mvc" / "entities"
    d.mkdir(parents=True, exist_ok=True)
    (d / "relations.json").write_text(
        json.dumps({"schema_version": "1.0", "relations": relations}), encoding="utf-8"
    )


_DEMO_FIXTURE = '''
from forge_mvc_fixtures import Fixture
from core.database import db


class DemoFixture(Fixture):
    tables = ("demo",)

    def load(self) -> None:
        db.execute("INSERT INTO demo (x) VALUES (1)")
'''


class TestFixtureBase:

    def test_load_requires_override(self) -> None:
        with pytest.raises(NotImplementedError):
            Fixture().load()

    def test_defaults(self) -> None:
        assert Fixture.tables == ()
        assert Fixture.depends_on == ()

    def test_purge_deletes_tables_in_reverse(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 0)

        class F(Fixture):
            tables = ("a", "b")

        F().purge()
        assert calls == ["DELETE FROM b", "DELETE FROM a"]


class TestDiscovery:

    def test_discovers_fixture(self, tmp_path: Path) -> None:
        _write_callable(tmp_path, "demo.py", _DEMO_FIXTURE)
        found = collect_callable_fixtures(tmp_path)
        assert len(found) == 1
        path, cls = found[0]
        assert path.name == "demo.py"
        assert issubclass(cls, Fixture)

    def test_ignores_dunder_and_non_fixture(self, tmp_path: Path) -> None:
        _write_callable(tmp_path, "__init__.py", "x = 1\n")
        _write_callable(tmp_path, "helper.py", "VALUE = 42\n")  # pas de Fixture
        assert collect_callable_fixtures(tmp_path) == []

    def test_ignores_factories_subdir(self, tmp_path: Path) -> None:
        # Les factories vivent dans un sous-dossier : pas des fixtures callable.
        d = tmp_path / "mvc" / "fixtures" / "factories"
        d.mkdir(parents=True, exist_ok=True)
        (d / "ville_factory.py").write_text(_DEMO_FIXTURE, encoding="utf-8")
        assert collect_callable_fixtures(tmp_path) == []

    def test_import_error_raises(self, tmp_path: Path) -> None:
        _write_callable(tmp_path, "broken.py", "import nonexistent_module_zzz\n")
        with pytest.raises(FixtureDiscoveryError, match="broken.py"):
            collect_callable_fixtures(tmp_path)

    def test_multiple_fixtures_raises(self, tmp_path: Path) -> None:
        src = (
            "from forge_mvc_fixtures import Fixture\n"
            "class A(Fixture):\n"
            "    def load(self): ...\n"
            "class B(Fixture):\n"
            "    def load(self): ...\n"
        )
        _write_callable(tmp_path, "two.py", src)
        with pytest.raises(FixtureDiscoveryError, match="une seule par fichier"):
            collect_callable_fixtures(tmp_path)


class TestOrdering:

    def test_callable_after_its_dependencies(self, tmp_path: Path) -> None:
        # users.sql (entité User) puis la fixture callable qui en dépend.
        _write_entity(tmp_path, "user", "User", "users")
        _write_entity(tmp_path, "eleve", "Eleve", "eleve")
        _write_relations(tmp_path, [
            {"type": "many_to_one", "from": "Eleve", "to": "User",
             "name": "compte", "foreign_key": "user_id"},
        ])
        _write_sql(tmp_path, "users.sql", "INSERT INTO users (Email) VALUES ('a@b.fr');")
        src = (
            "from forge_mvc_fixtures import Fixture\n"
            "class ImportFixture(Fixture):\n"
            "    depends_on = ('Eleve',)\n"
            "    def load(self): ...\n"
        )
        _write_callable(tmp_path, "import_data.py", src)
        units = order_load_units(
            tmp_path, collect_fixture_files(tmp_path), collect_callable_fixtures(tmp_path)
        )
        kinds = [(u.kind, u.path.name) for u in units]
        # users.sql (rang 0) avant la callable (dépend d'Eleve, rang 1).
        assert kinds == [("sql", "users.sql"), ("callable", "import_data.py")]

    def test_sql_before_callable_at_same_rank(self, tmp_path: Path) -> None:
        # Sans relations : .sql d'abord, puis callable, par nom.
        _write_sql(tmp_path, "aaa.sql", "INSERT INTO t (x) VALUES (1);")
        _write_callable(tmp_path, "zzz.py", _DEMO_FIXTURE)
        units = order_load_units(
            tmp_path, collect_fixture_files(tmp_path), collect_callable_fixtures(tmp_path)
        )
        assert [u.kind for u in units] == ["sql", "callable"]


class TestLoad:

    def test_dry_run_lists_callable(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _write_callable(tmp_path, "demo.py", _DEMO_FIXTURE)
        rc = load_fixtures(tmp_path, run=False, force=False, env="dev")
        out = capsys.readouterr().out
        assert rc == 0
        assert "demo.py (fixture Python)" in out
        assert "class DemoFixture" in out  # source affiché
        assert "--run pour exécuter" in out

    def test_run_calls_load(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _write_callable(tmp_path, "demo.py", _DEMO_FIXTURE)
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 0)
        rc = load_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 0
        assert calls == ["INSERT INTO demo (x) VALUES (1)"]

    def test_run_mixes_sql_and_callable_in_order(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_sql(tmp_path, "aaa.sql", "INSERT INTO t (x) VALUES (9);")
        _write_callable(tmp_path, "zzz.py", _DEMO_FIXTURE)
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 0)
        rc = load_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 0
        # .sql avant callable (même rang).
        assert calls == ["INSERT INTO t (x) VALUES (9)", "INSERT INTO demo (x) VALUES (1)"]

    def test_load_error_returns_1(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        src = (
            "from forge_mvc_fixtures import Fixture\n"
            "class BoomFixture(Fixture):\n"
            "    def load(self):\n"
            "        raise RuntimeError('boom')\n"
        )
        _write_callable(tmp_path, "boom.py", src)
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda *a, **k: 0)
        rc = load_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 1
        assert "boom.py" in capsys.readouterr().err

    def test_discovery_error_returns_2(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _write_callable(tmp_path, "broken.py", "import nonexistent_module_zzz\n")
        rc = load_fixtures(tmp_path, run=False, force=False, env="dev")
        assert rc == 2
        assert "broken.py" in capsys.readouterr().err


class TestPurgeCallable:

    def test_purge_default_deletes_declared_tables(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_callable(tmp_path, "demo.py", _DEMO_FIXTURE)
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 0)
        rc = purge_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 0
        assert calls == ["DELETE FROM demo"]

    def test_purge_custom_method(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        src = (
            "from forge_mvc_fixtures import Fixture\n"
            "from core.database import db\n"
            "class CustomFixture(Fixture):\n"
            "    def load(self): ...\n"
            "    def purge(self):\n"
            "        db.execute('DELETE FROM custom WHERE Seed = 1')\n"
        )
        _write_callable(tmp_path, "custom.py", src)
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 0)
        rc = purge_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 0
        assert calls == ["DELETE FROM custom WHERE Seed = 1"]

    def test_purge_callable_before_sql(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _write_sql(tmp_path, "users.sql", "INSERT INTO users (Email) VALUES ('a@b.fr');")
        _write_callable(tmp_path, "demo.py", _DEMO_FIXTURE)
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 0)
        rc = purge_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 0
        # callable démontée avant la table SQL.
        assert calls == ["DELETE FROM demo", "DELETE FROM users"]

    def test_purge_dry_run_lists_callable(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _write_callable(tmp_path, "demo.py", _DEMO_FIXTURE)
        rc = purge_fixtures(tmp_path, run=False, force=False, env="dev")
        out = capsys.readouterr().out
        assert rc == 0
        assert "DELETE FROM demo" in out
        assert "--run pour exécuter" in out
