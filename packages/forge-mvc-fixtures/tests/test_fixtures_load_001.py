"""Comportement de forge fixtures:load (FIXTURES-LOAD-001, ADR-074).

Sans base réelle : découpage SQL quote-aware, affichage par défaut (charte §7),
refus en production sans --force, exécution via core.database.db mocké.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_fixtures")

from forge_mvc_fixtures.cli.load import (
    active_env,
    collect_fixture_files,
    load_fixtures,
    main,
    order_fixture_files,
    split_sql_statements,
)


def _write_fixture(root: Path, name: str, sql: str) -> None:
    fixtures = root / "mvc" / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    (fixtures / name).write_text(sql, encoding="utf-8")


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


class TestSplit:

    def test_simple(self) -> None:
        stmts = split_sql_statements("INSERT INTO t VALUES (1); INSERT INTO t VALUES (2);")
        assert stmts == ["INSERT INTO t VALUES (1)", "INSERT INTO t VALUES (2)"]

    def test_semicolon_inside_string_is_not_a_separator(self) -> None:
        stmts = split_sql_statements("INSERT INTO t VALUES ('a;b'); INSERT INTO t VALUES ('c')")
        assert stmts == [
            "INSERT INTO t VALUES ('a;b')",
            "INSERT INTO t VALUES ('c')",
        ]

    def test_escaped_quote(self) -> None:
        stmts = split_sql_statements("INSERT INTO t VALUES ('l''ecole')")
        assert stmts == ["INSERT INTO t VALUES ('l''ecole')"]

    def test_trailing_statement_without_semicolon(self) -> None:
        assert split_sql_statements("SELECT 1") == ["SELECT 1"]


class TestCollect:

    def test_absent_dir_returns_empty(self, tmp_path: Path) -> None:
        assert collect_fixture_files(tmp_path) == []

    def test_sorted_by_name(self, tmp_path: Path) -> None:
        _write_fixture(tmp_path, "02_b.sql", "SELECT 2;")
        _write_fixture(tmp_path, "01_a.sql", "SELECT 1;")
        names = [p.name for p in collect_fixture_files(tmp_path)]
        assert names == ["01_a.sql", "02_b.sql"]


class TestOrdering:
    """F44 (ADR-077) : tri topologique par dépendances de clés étrangères."""

    def _setup(self, root: Path) -> None:
        _write_entity(root, "user", "User", "users")
        _write_entity(root, "eleve", "Eleve", "eleve")
        _write_relations(root, [
            {"type": "many_to_one", "from": "Eleve", "to": "User",
             "name": "compte", "foreign_key": "user_id"},
        ])
        # Nom de fichier trompeur : eleve < users alphabétiquement.
        _write_fixture(root, "eleve.sql", "INSERT INTO eleve (Nom) VALUES ('Durand');")
        _write_fixture(root, "users.sql", "INSERT INTO users (Email) VALUES ('a@b.fr');")

    def test_dependency_before_dependent(self, tmp_path: Path) -> None:
        self._setup(tmp_path)
        names = [p.name for p in order_fixture_files(tmp_path, collect_fixture_files(tmp_path))]
        # users référencé par eleve : chargé avant, malgré l'ordre alphabétique.
        assert names == ["users.sql", "eleve.sql"]

    def test_no_relations_falls_back_to_name(self, tmp_path: Path) -> None:
        _write_fixture(tmp_path, "eleve.sql", "INSERT INTO eleve (Nom) VALUES ('Durand');")
        _write_fixture(tmp_path, "users.sql", "INSERT INTO users (Email) VALUES ('a@b.fr');")
        names = [p.name for p in order_fixture_files(tmp_path, collect_fixture_files(tmp_path))]
        assert names == ["eleve.sql", "users.sql"]

    def test_cycle_falls_back_to_name(self, tmp_path: Path) -> None:
        _write_relations(tmp_path, [
            {"type": "many_to_one", "from": "A", "to": "B", "name": "b"},
            {"type": "many_to_one", "from": "B", "to": "A", "name": "a"},
        ])
        _write_entity(tmp_path, "a", "A", "a_table")
        _write_entity(tmp_path, "b", "B", "b_table")
        _write_fixture(tmp_path, "b_table.sql", "INSERT INTO b_table (X) VALUES (1);")
        _write_fixture(tmp_path, "a_table.sql", "INSERT INTO a_table (X) VALUES (1);")
        names = [p.name for p in order_fixture_files(tmp_path, collect_fixture_files(tmp_path))]
        assert names == ["a_table.sql", "b_table.sql"]

    def test_load_executes_in_dependency_order(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._setup(tmp_path)
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 1)
        rc = load_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 0
        assert calls == [
            "INSERT INTO users (Email) VALUES ('a@b.fr')",
            "INSERT INTO eleve (Nom) VALUES ('Durand')",
        ]


class TestNoFkChecks:
    """F44 (ADR-077) : --no-fk-checks encadre le chargement par la (dés)activation FK."""

    def test_wraps_load_with_dialect_ddl(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_fixture(tmp_path, "01.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 1)

        class _Dialect:
            def foreign_key_checks_ddl(self, *, enabled: bool) -> list[str]:
                return [f"SET FOREIGN_KEY_CHECKS = {1 if enabled else 0}"]

        class _Backend:
            dialect = _Dialect()

        import core.database.backend as backend_mod
        monkeypatch.setattr(backend_mod, "get_backend", lambda: _Backend())

        rc = load_fixtures(tmp_path, run=True, force=False, env="dev", no_fk_checks=True)
        assert rc == 0
        assert calls == [
            "SET FOREIGN_KEY_CHECKS = 0",
            "INSERT INTO ville (nom) VALUES ('Lyon')",
            "SET FOREIGN_KEY_CHECKS = 1",
        ]

    def test_reenables_fk_even_on_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_fixture(tmp_path, "01.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")
        calls: list[str] = []

        def execute(sql: str, *a: object, **k: object) -> int:
            calls.append(sql)
            if sql.startswith("INSERT"):
                raise RuntimeError("boom")
            return 1

        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", execute)

        class _Dialect:
            def foreign_key_checks_ddl(self, *, enabled: bool) -> list[str]:
                return ["SET FOREIGN_KEY_CHECKS = 1" if enabled else "SET FOREIGN_KEY_CHECKS = 0"]

        class _Backend:
            dialect = _Dialect()

        import core.database.backend as backend_mod
        monkeypatch.setattr(backend_mod, "get_backend", lambda: _Backend())

        rc = load_fixtures(tmp_path, run=True, force=False, env="dev", no_fk_checks=True)
        assert rc == 1
        # La réactivation FK a bien lieu malgré l'erreur (bloc finally).
        assert calls[-1] == "SET FOREIGN_KEY_CHECKS = 1"


class TestActiveEnv:

    def test_defaults_to_dev(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("APP_ENV", raising=False)
        assert active_env() == "dev"

    def test_reads_app_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_ENV", "prod")
        assert active_env() == "prod"


class TestLoadFixtures:

    def test_no_fixtures_is_noop(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        rc = load_fixtures(tmp_path, run=False, force=False, env="dev")
        assert rc == 0
        assert "Aucune fixture" in capsys.readouterr().out

    def test_display_only_does_not_touch_db(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_fixture(tmp_path, "01.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")
        # Toute tentative de connexion ferait échouer le test : le chemin
        # d'affichage ne doit jamais importer/exécuter la base.
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda *a, **k: pytest.fail("db touché en affichage"))
        rc = load_fixtures(tmp_path, run=False, force=False, env="dev")
        out = capsys.readouterr().out
        assert rc == 0
        assert "INSERT INTO ville" in out
        assert "--run pour exécuter" in out

    def test_prod_refused_without_force(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_fixture(tmp_path, "01.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda *a, **k: pytest.fail("db touché malgré refus prod"))
        rc = load_fixtures(tmp_path, run=True, force=False, env="prod")
        assert rc == 2
        assert "Refus" in capsys.readouterr().err

    def test_prod_runs_with_force(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_fixture(tmp_path, "01.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 1)
        rc = load_fixtures(tmp_path, run=True, force=True, env="prod")
        assert rc == 0
        assert calls == ["INSERT INTO ville (nom) VALUES ('Lyon')"]

    def test_run_executes_each_statement(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _write_fixture(tmp_path, "01.sql", "-- villes\nINSERT INTO ville (nom) VALUES ('Lyon');\nINSERT INTO ville (nom) VALUES ('Nice');")
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 1)
        rc = load_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 0
        assert calls == [
            "INSERT INTO ville (nom) VALUES ('Lyon')",
            "INSERT INTO ville (nom) VALUES ('Nice')",
        ]
        assert "2 instruction(s)" in capsys.readouterr().out

    def test_execution_error_returns_1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _write_fixture(tmp_path, "01.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")

        def boom(sql: str, *a: object, **k: object) -> int:
            raise RuntimeError("table absente")

        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", boom)
        rc = load_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 1
        assert "Erreur en chargeant 01.sql" in capsys.readouterr().err


class TestMain:

    def test_main_display_by_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _write_fixture(tmp_path, "01.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("APP_ENV", raising=False)
        rc = main([])
        assert rc == 0
        assert "--run pour exécuter" in capsys.readouterr().out
