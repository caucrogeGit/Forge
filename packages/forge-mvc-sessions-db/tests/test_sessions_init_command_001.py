"""Garde-fous des commandes `forge sessions:init` / `sessions:gc` (retour 016 F34/F35).

Vérifie que le paquet embarque le DDL `forge_sessions` (avec colonne `version`),
que la commande le copie dans `mvc/models/sql/` sans écraser un fichier
divergent, et que le DDL ne pose pas de double horloge SGBD/Python (F37).
"""
from __future__ import annotations

from pathlib import Path

import pytest

forge_mvc_sessions_db = pytest.importorskip("forge_mvc_sessions_db")

from forge_mvc_sessions_db.cli.init import (
    init_sessions_schema,
    iter_sessions_sql_resources,
)

PKG_ROOT = Path(forge_mvc_sessions_db.__file__).resolve().parent


def test_ships_forge_sessions_ddl() -> None:
    sql_files = list((PKG_ROOT / "sql").glob("*.sql"))
    assert sql_files, "forge-mvc-sessions-db doit embarquer le DDL forge_sessions"
    sql = sql_files[0].read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS forge_sessions" in sql
    # F36 : colonne version pour la concurrence optimiste.
    assert "version" in sql
    # F37 : pas de double horloge (aucune autorité SGBD sur les horodatages).
    # On inspecte les lignes de définition, hors commentaires SQL (`-- ...`).
    ddl = "\n".join(line for line in sql.splitlines() if not line.strip().startswith("--"))
    assert "DEFAULT CURRENT_TIMESTAMP" not in ddl
    assert "ON UPDATE" not in ddl


def test_init_copies_ddl_into_models_sql(tmp_path: Path) -> None:
    (tmp_path / "mvc").mkdir()
    assert init_sessions_schema(tmp_path) == 0
    copied = list((tmp_path / "mvc" / "models" / "sql").glob("*.sql"))
    assert copied, "le DDL doit être copié dans mvc/models/sql/"


def test_init_without_mvc_dir_fails(tmp_path: Path) -> None:
    assert init_sessions_schema(tmp_path) == 1


def test_init_is_idempotent(tmp_path: Path) -> None:
    (tmp_path / "mvc").mkdir()
    assert init_sessions_schema(tmp_path) == 0
    assert init_sessions_schema(tmp_path) == 0


def test_init_never_overwrites_divergent_file(tmp_path: Path) -> None:
    (tmp_path / "mvc" / "models" / "sql").mkdir(parents=True)
    name = next(iter(iter_sessions_sql_resources()))[0]
    target = tmp_path / "mvc" / "models" / "sql" / name
    target.write_text("-- contenu projet à préserver\n", encoding="utf-8")
    assert init_sessions_schema(tmp_path) == 0
    assert target.read_text(encoding="utf-8") == "-- contenu projet à préserver\n"


def test_gc_command_calls_cleanup(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import forge_mvc_sessions_db.store as store_mod

    monkeypatch.setattr(store_mod.DbSessionStore, "cleanup_expired", lambda self: 3)
    from forge_mvc_sessions_db.cli.gc import main

    assert main([]) == 0
    assert "3 session" in capsys.readouterr().out
