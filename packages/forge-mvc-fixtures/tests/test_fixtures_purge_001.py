"""Comportement de forge fixtures:purge (FIXTURES-PURGE-001, ADR-074).

Sans base réelle : dérivation des tables cibles depuis les INSERT INTO, ordre de
suppression inverse, affichage par défaut, refus prod sans --force, exécution via
core.database.db mocké.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_fixtures")

from forge_mvc_fixtures.cli.purge import (
    collect_target_tables,
    main,
    purge_fixtures,
)


def _write_fixture(root: Path, name: str, sql: str) -> None:
    fixtures = root / "mvc" / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    (fixtures / name).write_text(sql, encoding="utf-8")


class TestCollectTargetTables:

    def test_dedup_and_first_appearance_order(self, tmp_path: Path) -> None:
        _write_fixture(tmp_path, "01.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")
        _write_fixture(
            tmp_path, "02.sql",
            "INSERT INTO contact (ville_id) VALUES (1);\n"
            "INSERT INTO ville (nom) VALUES ('Nice');",
        )
        files = sorted((tmp_path / "mvc" / "fixtures").glob("*.sql"))
        assert collect_target_tables(files) == ["ville", "contact"]

    def test_backticks_and_case_insensitive(self, tmp_path: Path) -> None:
        _write_fixture(tmp_path, "01.sql", "insert into `ville` (nom) values ('Lyon');")
        files = sorted((tmp_path / "mvc" / "fixtures").glob("*.sql"))
        assert collect_target_tables(files) == ["ville"]

    def test_ignores_commented_insert(self, tmp_path: Path) -> None:
        _write_fixture(tmp_path, "01.sql", "-- INSERT INTO secret (x) VALUES (1);\nINSERT INTO ville (nom) VALUES ('Lyon');")
        files = sorted((tmp_path / "mvc" / "fixtures").glob("*.sql"))
        assert collect_target_tables(files) == ["ville"]


class TestPurge:

    def test_no_fixtures_is_noop(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert purge_fixtures(tmp_path, run=False, force=False, env="dev") == 0
        assert "Rien à purger" in capsys.readouterr().out

    def test_no_target_tables(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _write_fixture(tmp_path, "01.sql", "SELECT 1;")
        assert purge_fixtures(tmp_path, run=False, force=False, env="dev") == 0
        assert "Aucune table cible" in capsys.readouterr().out

    def test_display_shows_deletes_in_reverse_order(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_fixture(tmp_path, "01.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")
        _write_fixture(tmp_path, "02.sql", "INSERT INTO contact (ville_id) VALUES (1);")
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda *a, **k: pytest.fail("db touché en affichage"))
        rc = purge_fixtures(tmp_path, run=False, force=False, env="dev")
        out = capsys.readouterr().out
        assert rc == 0
        # contact (référençante) supprimée avant ville (référencée).
        assert out.index("DELETE FROM contact") < out.index("DELETE FROM ville")
        assert "--run pour exécuter" in out

    def test_prod_refused_without_force(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_fixture(tmp_path, "01.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda *a, **k: pytest.fail("db touché malgré refus prod"))
        rc = purge_fixtures(tmp_path, run=True, force=False, env="prod")
        assert rc == 2
        assert "Refus" in capsys.readouterr().err

    def test_run_executes_deletes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _write_fixture(tmp_path, "01.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")
        _write_fixture(tmp_path, "02.sql", "INSERT INTO contact (ville_id) VALUES (1);")
        calls: list[str] = []
        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", lambda sql, *a, **k: calls.append(sql) or 0)
        rc = purge_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 0
        # F52 : la purge est encadrée par la (dés)activation FK du dialecte ; on
        # vérifie l'ordre des DELETE indépendamment du backend actif.
        deletes = [sql for sql in calls if sql.upper().startswith("DELETE")]
        assert deletes == ["DELETE FROM contact", "DELETE FROM ville"]
        assert "2 table(s) vidée(s)" in capsys.readouterr().out

    def test_execution_error_returns_1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _write_fixture(tmp_path, "01.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")

        def boom(sql: str, *a: object, **k: object) -> int:
            # Seul le DELETE échoue ; la (dés)activation FF encadrante passe.
            if sql.upper().startswith("DELETE"):
                raise RuntimeError("FK violation")
            return 0

        import core.database.db as db_mod
        monkeypatch.setattr(db_mod, "execute", boom)
        rc = purge_fixtures(tmp_path, run=True, force=False, env="dev")
        assert rc == 1
        assert "Erreur en purgeant" in capsys.readouterr().err


class TestMain:

    def test_main_display_by_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _write_fixture(tmp_path, "01.sql", "INSERT INTO ville (nom) VALUES ('Lyon');")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("APP_ENV", raising=False)
        assert main([]) == 0
        assert "DELETE FROM ville" in capsys.readouterr().out
