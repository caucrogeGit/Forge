"""MIGRATION-RESUME-JOURNAL-001, mesure sur serveurs réels.

Le scénario est exactement celui qui bloquait au cycle 3 : une migration à deux
`CREATE TABLE` dont le second est fautif, sur MariaDB. La première table
persiste, la migration n'est pas au journal, et la relance butait sur
« already exists » sans commande de rattrapage. Ce test va jusqu'au bout du
déblocage : échec, correction du fichier, relance qui reprend sans rejouer, et
journal des migrations enregistré.

Sur PostgreSQL, témoin transactionnel, rien ne change : l'annulation défait
tout et aucun journal de reprise n'est tenu.

Le pendant hors base est `tests/test_migration_resume_journal_001.py`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.db

_A = "forge_resume_a"
_B = "forge_resume_b"


def _cleanup(db: Any, dialect: Any) -> None:
    db.execute(f"DROP TABLE IF EXISTS {_A}")
    db.execute(f"DROP TABLE IF EXISTS {_B}")
    db.execute("DROP TABLE IF EXISTS forge_migration_steps")
    # Le registre est garanti avant d'y effacer la version de la sonde.
    db.execute(dialect.forge_migrations_ddl())
    db.execute("DELETE FROM forge_migrations WHERE version = ?", ("20260730150000",))


def _write_migration(tmp_path: Path, second_statement: str) -> Path:
    dossier = tmp_path / "migrations"
    dossier.mkdir(exist_ok=True)
    (dossier / "20260730150000_resume_probe.sql").write_text(
        f"CREATE TABLE {_A} (id INT PRIMARY KEY);\n{second_statement}\n",
        encoding="utf-8",
    )
    return dossier


def _tables(db: Any, *names: str) -> "list[str]":
    return [n for n in names
            if db.fetch_one(
                "SELECT TABLE_NAME AS t FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?", (n,))]


def test_mariadb_le_scenario_du_cycle_3_se_debloque(
    real_db: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import os

    from core.database import db
    from core.database.backend import get_backend
    from forge_mvc_entities import migrations as M

    # La fixture d'intégration ne pose que les identifiants applicatifs (ADR-033).
    monkeypatch.setenv("DB_ADMIN_LOGIN", os.environ.get("DB_APP_LOGIN", ""))
    monkeypatch.setenv("DB_ADMIN_PWD", os.environ.get("DB_APP_PWD", ""))
    backend = get_backend()
    _cleanup(db, backend.dialect)

    connection = backend.get_admin_connection(
        database=os.environ.get("DB_NAME", ""))
    try:
        # 1. La migration casse à l'instruction 2 : la table A persiste.
        dossier = _write_migration(tmp_path, f"CREATE TABLE {_B} (id NOTATYPE)")
        with pytest.raises(M.MigrationError) as capture:
            M.apply_pending_migrations(dossier, db=connection)

        assert "instruction 2 sur 2" in str(capture.value)
        assert "la reprise continuera à l'instruction 2" in str(capture.value)
        assert _tables(db, _A) == [_A], "la première table doit avoir persisté"

        # 2. Le journal de reprise retient exactement le préfixe.
        pas = M.load_migration_steps(connection)
        assert [p for p, _ in pas.get("20260730150000", [])] == [1]

        # 3. Réécrire l'instruction DÉJÀ appliquée est refusé.
        _write_migration(tmp_path, f"CREATE TABLE {_B} (id NOTATYPE)")
        fichier = dossier / "20260730150000_resume_probe.sql"
        fichier.write_text(
            f"CREATE TABLE {_A} (id BIGINT PRIMARY KEY);\n"
            f"CREATE TABLE {_B} (id INT);\n", encoding="utf-8")
        with pytest.raises(M.MigrationError, match="reprise refusée"):
            M.apply_pending_migrations(dossier, db=connection)

        # 4. Corriger la seule instruction fautive débloque : la reprise ne
        #    rejoue pas l'instruction 1, sinon « already exists » ressortirait.
        _write_migration(tmp_path, f"CREATE TABLE {_B} (id INT PRIMARY KEY)")
        appliquees = M.apply_pending_migrations(dossier, db=connection)

        assert [m.version for m in appliquees] == ["20260730150000"]
        assert _tables(db, _A, _B) == [_A, _B]
        journal = db.fetch_one(
            "SELECT COUNT(*) AS n FROM forge_migrations WHERE version = ?",
            ("20260730150000",))
        assert journal == {"n": 1}, "la migration doit être enregistrée"
        assert M.load_migration_steps(connection) == {}, "le journal de reprise s'efface"
    finally:
        connection.close()
        _cleanup(db, backend.dialect)


def test_mariadb_le_statut_signale_la_migration_interrompue(
    real_db: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import os

    from core.database import db
    from core.database.backend import get_backend
    from forge_mvc_entities import migrations as M

    monkeypatch.setenv("DB_ADMIN_LOGIN", os.environ.get("DB_APP_LOGIN", ""))
    monkeypatch.setenv("DB_ADMIN_PWD", os.environ.get("DB_APP_PWD", ""))
    backend = get_backend()
    _cleanup(db, backend.dialect)
    connection = backend.get_admin_connection(
        database=os.environ.get("DB_NAME", ""))
    try:
        dossier = _write_migration(tmp_path, f"CREATE TABLE {_B} (id NOTATYPE)")
        with pytest.raises(M.MigrationError):
            M.apply_pending_migrations(dossier, db=connection)

        pas = M.load_migration_steps(connection)
        assert len(pas.get("20260730150000", [])) == 1
    finally:
        connection.close()
        _cleanup(db, backend.dialect)


@pytest.mark.db_pg
def test_postgres_reste_atomique_et_sans_journal(
    real_pg_db: None, tmp_path: Path,
) -> None:
    """Le témoin transactionnel : annulation totale, aucun journal de reprise."""
    import os

    from core.database import db
    from core.database.backend import get_backend
    from forge_mvc_entities import migrations as M

    backend = get_backend()
    db.execute(f"DROP TABLE IF EXISTS {_A}")
    db.execute(f"DROP TABLE IF EXISTS {_B}")
    db.execute("DROP TABLE IF EXISTS forge_migrations")
    db.execute(backend.dialect.forge_migrations_ddl())

    monkey_admin = {"DB_ADMIN_LOGIN": os.environ.get("DB_APP_LOGIN", ""),
                    "DB_ADMIN_PWD": os.environ.get("DB_APP_PWD", "")}
    anciens = {k: os.environ.get(k) for k in monkey_admin}
    os.environ.update(monkey_admin)
    try:
        connection = backend.get_admin_connection(database=os.environ.get("DB_NAME", ""))
        try:
            dossier = _write_migration(tmp_path, f"CREATE TABLE {_B} (id NOTATYPE)")
            with pytest.raises(M.MigrationError):
                M.apply_pending_migrations(dossier, db=connection)

            ligne = db.fetch_one(
                "SELECT COUNT(*) AS n FROM information_schema.tables "
                "WHERE table_name IN (?, ?)", (_A, "forge_migration_steps"))
            assert ligne == {"n": 0}, "annulation totale, et aucun journal de reprise"
        finally:
            connection.close()
    finally:
        for cle, valeur in anciens.items():
            if valeur is None:
                os.environ.pop(cle, None)
            else:
                os.environ[cle] = valeur
