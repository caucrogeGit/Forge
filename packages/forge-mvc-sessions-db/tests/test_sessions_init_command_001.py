"""Garde-fous des commandes `forge sessions:init` / `sessions:gc` (retour 016 F34/F35 ; ADR-071).

Vérifie que le paquet **déclare** la table `forge_sessions` (avec colonne
`version`), que la commande écrit sa migration dans `mvc/migrations/` sans
écraser un fichier divergent, et que le DDL ne pose pas de double horloge
SGBD/Python (F37).

Depuis `OPTIN-DDL-SESSIONS-DB-001`, le paquet ne livre plus de `.sql` figé :
il déclare la table une fois (`forge_mvc_sessions_db.tables`) et le DDL est
**rendu pour le backend actif**. Les invariants métier (colonne `version`,
absence de double horloge) sont donc vérifiés sur le rendu, et pour chacun des
quatre backends plutôt que pour le seul MariaDB.
"""
from __future__ import annotations

from pathlib import Path

import pytest

forge_mvc_sessions_db = pytest.importorskip("forge_mvc_sessions_db")

from forge_mvc_sessions_db.cli.init import (
    init_sessions_migrations,
    iter_sessions_migration_resources,
)

PKG_ROOT = Path(forge_mvc_sessions_db.__file__).resolve().parent


BACKENDS = ("mariadb", "sqlite", "postgres", "mssql")


def _rendered(backend_name: str) -> str:
    """DDL rendu par le paquet pour un backend donné."""
    pytest.importorskip(f"forge_mvc_{backend_name}")
    from core.database.table_ddl import render_create_table
    from forge_mvc_sessions_db.tables import FORGE_SESSIONS

    module = __import__(f"forge_mvc_{backend_name}.dialect", fromlist=["dialect"])
    dialect_cls = next(
        value for key, value in vars(module).items()
        if key.endswith("Dialect") and isinstance(value, type)
    )
    return "\n".join(render_create_table(FORGE_SESSIONS, dialect_cls()))


def test_declares_forge_sessions_table() -> None:
    """Le paquet ne livre plus de SQL figé : il déclare la table."""
    from forge_mvc_sessions_db.tables import FORGE_SESSIONS, MIGRATIONS

    assert not (PKG_ROOT / "migrations").exists(), (
        "forge-mvc-sessions-db ne doit plus embarquer de .sql fige "
        "(OPTIN-DDL-SESSIONS-DB-001)."
    )
    assert FORGE_SESSIONS.name == "forge_sessions"
    assert MIGRATIONS and MIGRATIONS[0][0].endswith("_create_forge_sessions.sql")


@pytest.mark.parametrize("backend_name", BACKENDS)
def test_rendered_ddl_carries_business_invariants(backend_name: str) -> None:
    sql = _rendered(backend_name)
    assert "forge_sessions" in sql
    # F36 : colonne version pour la concurrence optimiste.
    assert "version" in sql
    # F37 : pas de double horloge (aucune autorité SGBD sur les horodatages).
    ddl = "\n".join(line for line in sql.splitlines() if not line.strip().startswith("--"))
    assert "DEFAULT CURRENT_TIMESTAMP" not in ddl
    assert "ON UPDATE" not in ddl.upper()


@pytest.mark.parametrize("backend_name", BACKENDS)
def test_rendered_ddl_is_portable(backend_name: str) -> None:
    """Le défaut mesuré par l'audit ne doit pas revenir par le rendu."""
    sql = _rendered(backend_name).upper()
    if backend_name == "mariadb":
        return
    for marker in ("AUTO_INCREMENT", "UNSIGNED", "ENGINE=", "LONGTEXT"):
        assert marker not in sql, f"{backend_name} : DDL contenant {marker}"


def test_init_copies_migration_into_mvc_migrations(tmp_path: Path) -> None:
    (tmp_path / "mvc").mkdir()
    assert init_sessions_migrations(tmp_path) == 0
    copied = list((tmp_path / "mvc" / "migrations").glob("*.sql"))
    assert copied, "la migration doit être copiée dans mvc/migrations/"


def test_init_without_mvc_dir_fails(tmp_path: Path) -> None:
    assert init_sessions_migrations(tmp_path) == 1


def test_init_is_idempotent(tmp_path: Path) -> None:
    (tmp_path / "mvc").mkdir()
    assert init_sessions_migrations(tmp_path) == 0
    assert init_sessions_migrations(tmp_path) == 0


def test_init_never_overwrites_divergent_file(tmp_path: Path) -> None:
    (tmp_path / "mvc" / "migrations").mkdir(parents=True)
    name = next(iter(iter_sessions_migration_resources()))[0]
    target = tmp_path / "mvc" / "migrations" / name
    target.write_text("-- contenu projet à préserver\n", encoding="utf-8")
    assert init_sessions_migrations(tmp_path) == 0
    assert target.read_text(encoding="utf-8") == "-- contenu projet à préserver\n"


def test_gc_command_calls_cleanup(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import forge_mvc_sessions_db.store as store_mod

    monkeypatch.setattr(store_mod.DbSessionStore, "cleanup_expired", lambda self: 3)
    from forge_mvc_sessions_db.cli.gc import main

    assert main([]) == 0
    assert "3 session" in capsys.readouterr().out
