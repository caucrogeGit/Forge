"""TEST-DB-INIT-MIGRATIONS-001 — intégration MariaDB de db:init et du runner de migrations.

Les 25 tests `db` existants couvrent la couche d'accès, `db:apply`, les
transactions, les FK et le slug, mais deux chemins critiques n'étaient validés
qu'en mock :

- `forge db:init` (`cli.entities.db_init.init_project_database`) : création de la
  base, du compte applicatif et des GRANT, plus le mode dégradé `CREATE USER IF
  NOT EXISTS` quand l'admin n'a pas SELECT sur `mysql.user` (ADR-033, DB-INIT-
  MYSQL-USER-GRANT-001) ;
- le runner de migrations (`cli.entities.migrations.apply_pending_migrations`) :
  application réelle, idempotence, refus des états incohérents (CHANGED /
  MISSING) et rollback transactionnel réel quand le SQL d'une migration échoue.

Ces tests exercent une VRAIE MariaDB. Marqués `db` : sautés en local sans base,
requis en CI (`FORGE_REQUIRE_DB=1`, voir tests/db/conftest.py). Chaque test crée
une base et des comptes à nom unique, nettoyés en fin de test (hygiène stricte
des connexions : toute connexion est fermée, sinon un verrou de métadonnées
ouvert bloquerait le DROP DATABASE final).
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

import pytest

from cli.entities import db_init
from cli.entities import migrations as mig
from cli.entities.db_init import FORGE_MIGRATIONS_TABLE_SQL

pytestmark = pytest.mark.db

_REQUIRE_DB = os.environ.get("FORGE_REQUIRE_DB") == "1"

WIDGETS_SQL = (
    "CREATE TABLE widgets (\n"
    "    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,\n"
    "    label VARCHAR(50) NOT NULL\n"
    ");\n"
)


def _admin_params() -> dict[str, Any]:
    return {
        "host": os.environ.get("FORGE_TEST_DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("FORGE_TEST_DB_PORT", "3306")),
        "user": os.environ.get("FORGE_TEST_DB_USER", "root"),
        "password": os.environ.get("FORGE_TEST_DB_PASSWORD", ""),
    }


class _DbHarness:
    """Connexion d'administration + registre de nettoyage des objets créés."""

    def __init__(self) -> None:
        self.params = _admin_params()
        self.uid = uuid.uuid4().hex[:10]
        self.app_host = "127.0.0.1"
        self._dbs: list[str] = []
        self._users: list[tuple[str, str]] = []

    def connect(self, database: str | None = None) -> Any:
        import mariadb

        return mariadb.connect(database=database, **self.params)

    def name(self, prefix: str) -> str:
        # Préfixe `forge_it_` : matché par le GRANT pattern du test dégradé.
        return f"forge_it_{prefix}_{self.uid}"

    def track_db(self, db_name: str) -> str:
        self._dbs.append(db_name)
        return db_name

    def track_user(self, login: str, host: str) -> tuple[str, str]:
        self._users.append((login, host))
        return login, host

    def cleanup(self) -> None:
        conn = self.connect()
        try:
            cursor = conn.cursor()
            for db_name in self._dbs:
                cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
            for login, host in self._users:
                cursor.execute(f"DROP USER IF EXISTS '{login}'@'{host}'")
            conn.commit()
            cursor.close()
        finally:
            conn.close()


@pytest.fixture
def harness() -> Any:
    h = _DbHarness()
    try:
        probe = h.connect()
        probe.close()
    except Exception as error:  # noqa: BLE001 — toute erreur = base indisponible
        message = f"MariaDB de test injoignable : {error}"
        if _REQUIRE_DB:
            pytest.fail(message + " (FORGE_REQUIRE_DB=1)")
        pytest.skip(message + " (test d'intégration sauté en local)")
    try:
        yield h
    finally:
        h.cleanup()


def _db_init_config(h: _DbHarness, *, admin_login: str, admin_password: str,
                    db_name: str, app_login: str, app_password: str) -> db_init.DbInitConfig:
    return db_init.DbInitConfig(
        admin_host=h.params["host"],
        admin_port=h.params["port"],
        admin_login=admin_login,
        admin_password=admin_password,
        db_name=db_name,
        db_charset="utf8mb4",
        db_collation="utf8mb4_unicode_ci",
        app_host=h.app_host,
        app_port=h.params["port"],
        app_login=app_login,
        app_password=app_password,
        app_privileges=db_init.DEFAULT_APP_PRIVILEGES,
    )


# --------------------------------------------------------------------------- #
# forge db:init                                                               #
# --------------------------------------------------------------------------- #


def test_db_init_creates_database_user_and_grants(
    harness: _DbHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_name = harness.track_db(harness.name("init"))
    app_login = f"app_{harness.uid}"
    harness.track_user(app_login, harness.app_host)
    cfg = _db_init_config(
        harness, admin_login=harness.params["user"], admin_password=harness.params["password"],
        db_name=db_name, app_login=app_login, app_password="s3cret",
    )
    monkeypatch.setattr(db_init, "load_db_init_config", lambda: cfg)

    actions = db_init.init_project_database()

    assert any("créée" in a for a in actions), actions
    assert any("Privilèges appliqués" in a for a in actions), actions
    assert any("forge_migrations" in a for a in actions), actions

    conn = harness.connect()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = ?",
            (db_name,),
        )
        assert cursor.fetchone() is not None, "la base doit exister"
        cursor.execute(
            "SELECT TABLE_NAME FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = 'forge_migrations'",
            (db_name,),
        )
        assert cursor.fetchone() is not None, "forge_migrations doit exister"
        cursor.execute("SELECT User FROM mysql.user WHERE User = ?", (app_login,))
        assert cursor.fetchone() is not None, "le compte applicatif doit exister"
        cursor.close()
    finally:
        conn.close()


def test_db_init_app_user_has_dml_only(
    harness: _DbHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Le compte applicatif a le DML accordé mais pas le DDL (ADR-033)."""
    db_name = harness.track_db(harness.name("dml"))
    app_login = f"app_{harness.uid}"
    harness.track_user(app_login, harness.app_host)
    cfg = _db_init_config(
        harness, admin_login=harness.params["user"], admin_password=harness.params["password"],
        db_name=db_name, app_login=app_login, app_password="s3cret",
    )
    monkeypatch.setattr(db_init, "load_db_init_config", lambda: cfg)
    db_init.init_project_database()

    import mariadb

    app_conn = mariadb.connect(
        host=harness.params["host"], port=harness.params["port"],
        user=app_login, password="s3cret", database=db_name,
    )
    try:
        cursor = app_conn.cursor()
        with pytest.raises(mariadb.Error):
            # CREATE n'est pas dans DEFAULT_APP_PRIVILEGES : refusé.
            cursor.execute("CREATE TABLE illegal_ddl (id INT)")
        cursor.close()
    finally:
        app_conn.close()


def test_db_init_is_idempotent(
    harness: _DbHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_name = harness.track_db(harness.name("idem"))
    app_login = f"app_{harness.uid}"
    harness.track_user(app_login, harness.app_host)
    cfg = _db_init_config(
        harness, admin_login=harness.params["user"], admin_password=harness.params["password"],
        db_name=db_name, app_login=app_login, app_password="s3cret",
    )
    monkeypatch.setattr(db_init, "load_db_init_config", lambda: cfg)

    db_init.init_project_database()
    actions = db_init.init_project_database()

    assert any("déjà présente" in a for a in actions), actions
    assert any("déjà présent" in a for a in actions), actions


def test_db_init_degraded_mode_without_mysql_user_select(
    harness: _DbHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Admin sans SELECT sur mysql.user : bascule en CREATE USER IF NOT EXISTS."""
    restricted = f"radm_{harness.uid}"
    harness.track_user(restricted, harness.app_host)
    db_name = harness.track_db(harness.name("deg"))
    app_login = f"app_{harness.uid}"
    harness.track_user(app_login, harness.app_host)

    # Admin restreint : peut créer des comptes et des bases du préfixe forge_it_,
    # accorder le DML, recharger les privilèges, mais ne peut PAS lire mysql.user
    # (pas de SELECT global).
    setup = harness.connect()
    try:
        cur = setup.cursor()
        cur.execute(f"CREATE USER '{restricted}'@'{harness.app_host}' IDENTIFIED BY 'apwd'")
        cur.execute(f"GRANT CREATE USER ON *.* TO '{restricted}'@'{harness.app_host}'")
        cur.execute(f"GRANT RELOAD ON *.* TO '{restricted}'@'{harness.app_host}'")
        cur.execute(
            "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE ON `forge_it_%`.* "
            f"TO '{restricted}'@'{harness.app_host}' WITH GRANT OPTION"
        )
        setup.commit()
        cur.close()
    finally:
        setup.close()

    cfg = _db_init_config(
        harness, admin_login=restricted, admin_password="apwd",
        db_name=db_name, app_login=app_login, app_password="s3cret",
    )
    monkeypatch.setattr(db_init, "load_db_init_config", lambda: cfg)

    actions = db_init.init_project_database()

    assert any("SELECT sur mysql.user" in a for a in actions), (
        "le mode dégradé doit signaler l'absence de SELECT sur mysql.user", actions,
    )
    assert any("créé ou déjà présent" in a for a in actions), actions
    assert any("forge_migrations" in a for a in actions), actions


# --------------------------------------------------------------------------- #
# runner de migrations                                                        #
# --------------------------------------------------------------------------- #


@pytest.fixture
def migrated_db(harness: _DbHarness) -> Any:
    """Base de test prête (forge_migrations créée), avec une fabrique de connexion."""
    db_name = harness.track_db(harness.name("mig"))
    setup = harness.connect()
    try:
        cur = setup.cursor()
        cur.execute(f"CREATE DATABASE `{db_name}`")
        cur.close()
        setup.commit()
    finally:
        setup.close()
    init = harness.connect(db_name)
    try:
        cur = init.cursor()
        cur.execute(FORGE_MIGRATIONS_TABLE_SQL)
        init.commit()
        cur.close()
    finally:
        init.close()
    return db_name


def _apply(harness: _DbHarness, db_name: str, migrations_dir: Path,
           *, dry_run: bool = False) -> list[mig.MigrationFile]:
    conn = harness.connect(db_name)
    try:
        return mig.apply_pending_migrations(migrations_dir, db=conn, dry_run=dry_run)
    finally:
        conn.close()


def _applied_versions(harness: _DbHarness, db_name: str) -> list[str]:
    conn = harness.connect(db_name)
    try:
        return [m.version for m in mig.load_applied_migrations(db=conn)]
    finally:
        conn.close()


def _scalar(harness: _DbHarness, db_name: str, sql: str) -> Any:
    conn = harness.connect(db_name)
    try:
        cur = conn.cursor()
        cur.execute(sql)
        row = cur.fetchone()
        conn.commit()
        cur.close()
        return row
    finally:
        conn.close()


def test_apply_creates_table_and_records_migration(
    harness: _DbHarness, migrated_db: str, tmp_path: Path
) -> None:
    (tmp_path / "20260101000000_create_widgets.sql").write_text(WIDGETS_SQL, encoding="utf-8")

    applied = _apply(harness, migrated_db, tmp_path)

    assert [m.version for m in applied] == ["20260101000000"]
    table = _scalar(
        harness, migrated_db,
        "SELECT TABLE_NAME FROM information_schema.TABLES "
        f"WHERE TABLE_SCHEMA = '{migrated_db}' AND TABLE_NAME = 'widgets'",
    )
    assert table is not None, "la table widgets doit être créée en base"
    assert _applied_versions(harness, migrated_db) == ["20260101000000"]


def test_apply_is_idempotent(
    harness: _DbHarness, migrated_db: str, tmp_path: Path
) -> None:
    (tmp_path / "20260101000000_create_widgets.sql").write_text(WIDGETS_SQL, encoding="utf-8")
    _apply(harness, migrated_db, tmp_path)

    again = _apply(harness, migrated_db, tmp_path)

    assert again == [], "une migration déjà appliquée ne doit pas être ré-exécutée"


def test_apply_dry_run_writes_nothing(
    harness: _DbHarness, migrated_db: str, tmp_path: Path
) -> None:
    (tmp_path / "20260101000000_create_widgets.sql").write_text(WIDGETS_SQL, encoding="utf-8")

    planned = _apply(harness, migrated_db, tmp_path, dry_run=True)

    assert [m.version for m in planned] == ["20260101000000"]
    assert _applied_versions(harness, migrated_db) == [], "dry-run ne doit rien enregistrer"
    table = _scalar(
        harness, migrated_db,
        "SELECT TABLE_NAME FROM information_schema.TABLES "
        f"WHERE TABLE_SCHEMA = '{migrated_db}' AND TABLE_NAME = 'widgets'",
    )
    assert table is None, "dry-run ne doit pas créer la table"


def test_apply_refuses_changed_migration(
    harness: _DbHarness, migrated_db: str, tmp_path: Path
) -> None:
    path = tmp_path / "20260101000000_create_widgets.sql"
    path.write_text(WIDGETS_SQL, encoding="utf-8")
    _apply(harness, migrated_db, tmp_path)

    # Le fichier local change de checksum après application : CHANGED.
    path.write_text(WIDGETS_SQL.replace("VARCHAR(50)", "VARCHAR(99)"), encoding="utf-8")
    with pytest.raises(mig.MigrationError, match="modifiée"):
        _apply(harness, migrated_db, tmp_path)


def test_apply_rolls_back_on_sql_failure(
    harness: _DbHarness, migrated_db: str, tmp_path: Path
) -> None:
    """Une migration dont une instruction échoue est annulée (rollback réel)."""
    (tmp_path / "20260101000000_create_widgets.sql").write_text(WIDGETS_SQL, encoding="utf-8")
    _apply(harness, migrated_db, tmp_path)

    # v2 : un INSERT valide suivi d'un INSERT sur une colonne inexistante.
    (tmp_path / "20260202000000_seed_then_fail.sql").write_text(
        "INSERT INTO widgets (label) VALUES ('temp');\n"
        "INSERT INTO widgets (nope) VALUES ('x');\n",
        encoding="utf-8",
    )
    with pytest.raises(mig.MigrationError, match="erreur SQL"):
        _apply(harness, migrated_db, tmp_path)

    count = _scalar(harness, migrated_db, "SELECT COUNT(*) FROM widgets")
    assert count[0] == 0, "l'INSERT valide doit être annulé par le rollback"
    assert "20260202000000" not in _applied_versions(harness, migrated_db), (
        "une migration échouée ne doit pas être enregistrée"
    )
