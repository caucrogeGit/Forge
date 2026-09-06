"""PG/MSSQL-DB-INIT-PROVISIONING-001 (ADR-067/084) — db:init provisionne pg et mssql.

`forge db:init` génère et affiche le script SQL de provisioning du backend
actif (PostgreSQL et SQL Server compris) ; `--run` exécute. Les privilèges
applicatifs au-delà du DML restent propres à MariaDB : refus explicite
plutôt que du SQL inapplicable (règle B).
"""
from __future__ import annotations

import types
from typing import Any

import pytest

from forge_mvc_entities import db_init
from forge_mvc_entities.db_init import (
    DEFAULT_APP_PRIVILEGES,
    DbInitError,
    ProvisioningEnv,
    _ms_ident,
    _ms_string,
    _pg_ident,
    _pg_string,
    generate_provisioning_sql_mssql,
    generate_provisioning_sql_postgres,
)


@pytest.fixture(autouse=True)
def _sans_projet_sur_le_disque(monkeypatch):
    """Neutralise le chargement de `config.py` pour les tests de dispatch.

    `_dispatch_db_init` charge la configuration du projet avant de résoudre le
    backend (`DB-INIT-BACKEND-FROM-ENV-001`) : `DB_BACKEND` vit dans `env/dev`,
    et le résoudre d'abord revenait à ignorer ce que le projet déclare.

    Ces tests-ci portent sur l'aiguillage, quel backend mène à quel générateur,
    et montent un backend factice. Ils n'ont pas de projet sur le disque, et
    n'en ont pas besoin.

    L'ordre réel des deux appels est fixé ailleurs, sur l'arbre syntaxique et
    par un test de comportement dans un projet temporaire
    (`packages/forge-mvc-entities/tests/test_db_init_backend_from_env_001.py`).
    """
    monkeypatch.setattr(db_init, "load_project_config", lambda *a, **k: None)


_MIGRATIONS_DDL = "CREATE TABLE IF NOT EXISTS forge_migrations (factice INT)"


def _cfg(**over: object) -> ProvisioningEnv:
    base: dict[str, object] = dict(
        db_name="ventes",
        db_charset="utf8mb4",
        db_collation="utf8mb4_unicode_ci",
        host="localhost",
        admin_login="admin",
        admin_password="adminpwd",
        app_login="app",
        app_password="apppwd",
        app_privileges=DEFAULT_APP_PRIVILEGES,
    )
    base.update(over)
    return ProvisioningEnv(**base)  # type: ignore[arg-type]


# ── Script PostgreSQL ────────────────────────────────────────────────────────

def test_pg_sql_base_possedee_par_le_compte_admin():
    sql = generate_provisioning_sql_postgres(_cfg(), _MIGRATIONS_DDL)
    assert 'CREATE ROLE "admin" LOGIN PASSWORD \'adminpwd\';' in sql
    assert 'CREATE ROLE "app" LOGIN PASSWORD \'apppwd\';' in sql
    assert 'CREATE DATABASE "ventes" OWNER "admin";' in sql
    assert 'GRANT CONNECT ON DATABASE "ventes" TO "app";' in sql


def test_pg_sql_migrations_et_droits_futurs():
    sql = generate_provisioning_sql_postgres(_cfg(), _MIGRATIONS_DDL)
    # La suite du script bascule dans la base du projet (méta-commande psql).
    assert '\\connect "ventes"' in sql
    assert f"{_MIGRATIONS_DDL};" in sql
    assert 'ALTER TABLE forge_migrations OWNER TO "admin";' in sql
    # DML présent et futur pour l'applicatif (tables ET séquences).
    assert 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "app";' in sql
    assert 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "app";' in sql
    assert 'ALTER DEFAULT PRIVILEGES FOR ROLE "admin" IN SCHEMA public' in sql


def test_pg_sql_sans_syntaxe_mariadb():
    sql = generate_provisioning_sql_postgres(_cfg(), _MIGRATIONS_DDL)
    assert "CHARACTER SET" not in sql
    assert "FLUSH PRIVILEGES" not in sql
    assert "*.*" not in sql
    # Pas d'identifiant au quoting MariaDB (les backticks des commentaires
    # d'en-tête, qui citent la commande, restent admis).
    assert "`ventes`" not in sql


# ── Script SQL Server ────────────────────────────────────────────────────────

def test_mssql_sql_base_logins_et_utilisateurs():
    sql = generate_provisioning_sql_mssql(_cfg(), _MIGRATIONS_DDL)
    assert "IF DB_ID(N'ventes') IS NULL\nCREATE DATABASE [ventes];" in sql
    assert "CREATE LOGIN [admin] WITH PASSWORD = N'adminpwd';" in sql
    assert "CREATE LOGIN [app] WITH PASSWORD = N'apppwd';" in sql
    assert "USE [ventes];" in sql
    assert "CREATE USER [admin] FOR LOGIN [admin];" in sql
    assert "ALTER ROLE db_owner ADD MEMBER [admin];" in sql
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO [app];" in sql


def test_mssql_sql_migrations_et_lots_sqlcmd():
    sql = generate_provisioning_sql_mssql(_cfg(), _MIGRATIONS_DDL)
    assert f"{_MIGRATIONS_DDL};" in sql
    # Séparateurs de lots sqlcmd (CREATE DATABASE et USE isolés).
    assert sql.count("\nGO\n") >= 4


def test_mssql_sql_sans_syntaxe_mariadb():
    sql = generate_provisioning_sql_mssql(_cfg(), _MIGRATIONS_DDL)
    assert "CHARACTER SET" not in sql
    assert "FLUSH PRIVILEGES" not in sql
    assert "*.*" not in sql
    # Pas d'identifiant au quoting MariaDB (les backticks des commentaires
    # d'en-tête, qui citent la commande, restent admis).
    assert "`ventes`" not in sql


# ── Garde DML : escape hatch DB_APP_PRIVILEGES propre à MariaDB ─────────────

@pytest.mark.parametrize("generator", [
    generate_provisioning_sql_postgres,
    generate_provisioning_sql_mssql,
])
def test_privilege_non_dml_refuse_explicitement(generator: Any):
    cfg = _cfg(app_privileges=("SELECT", "INSERT", "CREATE"))
    with pytest.raises(DbInitError, match="CREATE") as exc:
        generator(cfg, _MIGRATIONS_DDL)
    assert "MariaDB" in str(exc.value)


# ── Quoting par dialecte ─────────────────────────────────────────────────────

def test_quoting_postgres():
    assert _pg_ident('a"b') == '"a""b"'
    assert _pg_string("o'brien") == "'o''brien'"


def test_quoting_mssql():
    assert _ms_ident("a]b") == "[a]]b]"
    assert _ms_string("o'brien") == "'o''brien'"


# ── Dispatch : défaut = génère le SQL du backend actif ──────────────────────

def _fake_backend(name: str):
    return types.SimpleNamespace(
        name=name,
        requires_provisioning=True,
        dialect=types.SimpleNamespace(forge_migrations_ddl=lambda: _MIGRATIONS_DDL),
    )


def test_defaut_postgres_genere_le_sql_sans_executer(monkeypatch, capsys):
    import core.database.backend as backend_mod

    monkeypatch.setattr(backend_mod, "get_backend", lambda: _fake_backend("postgres"))
    monkeypatch.setattr(db_init, "_check_required_env", lambda: None)
    monkeypatch.setattr(db_init, "load_provisioning_env", _cfg)
    called = {"executed": False}
    monkeypatch.setattr(db_init, "init_project_database", lambda: called.__setitem__("executed", True) or [])

    db_init._dispatch_db_init(run=False)

    out = capsys.readouterr().out
    assert 'CREATE DATABASE "ventes" OWNER "admin";' in out
    assert called["executed"] is False, "le mode par défaut ne doit RIEN exécuter"


def test_defaut_mssql_genere_le_sql_sans_executer(monkeypatch, capsys):
    import core.database.backend as backend_mod

    monkeypatch.setattr(backend_mod, "get_backend", lambda: _fake_backend("mssql"))
    monkeypatch.setattr(db_init, "_check_required_env", lambda: None)
    monkeypatch.setattr(db_init, "load_provisioning_env", _cfg)

    db_init._dispatch_db_init(run=False)

    out = capsys.readouterr().out
    assert "CREATE DATABASE [ventes];" in out


def test_run_postgres_route_vers_init_project_database(monkeypatch, capsys):
    import core.database.backend as backend_mod

    monkeypatch.setattr(backend_mod, "get_backend", lambda: _fake_backend("postgres"))
    monkeypatch.setattr(db_init, "_check_required_env", lambda: None)
    monkeypatch.setattr(db_init, "init_project_database", lambda: ["Base ventes créée."])

    db_init._dispatch_db_init(run=True)

    out = capsys.readouterr().out
    assert "[OK]" in out and "Base ventes créée." in out
    assert "CREATE DATABASE" not in out, "le mode --run exécute, il n'affiche pas le SQL"


def test_backend_inconnu_toujours_refuse(monkeypatch):
    import core.database.backend as backend_mod

    monkeypatch.setattr(backend_mod, "get_backend", lambda: _fake_backend("oracle"))
    with pytest.raises(DbInitError, match="oracle"):
        db_init._dispatch_db_init(run=False)


# ── Exécution --run : séquence SQL réelle sur connexions factices ───────────

class _FakeCursor:
    def __init__(self, fetch_queue: "list[Any]") -> None:
        self.executed: "list[str]" = []
        self._fetch_queue = fetch_queue

    def execute(self, sql: str, params: "Any" = ()) -> None:
        self.executed.append(sql)

    def fetchone(self) -> "Any":
        return self._fetch_queue.pop(0) if self._fetch_queue else None

    def close(self) -> None:
        pass


class _FakeConnection:
    def __init__(self, fetch_queue: "list[Any]") -> None:
        self.cursor_obj = _FakeCursor(fetch_queue)
        self.autocommit = False
        self.committed = False

    def cursor(self, **_: Any) -> _FakeCursor:
        return self.cursor_obj

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass


def _run_backend(name: str):
    backend = _fake_backend(name)
    backend.close_connection = lambda connection: None
    return backend


def test_init_postgres_sequence_sql(monkeypatch):
    admin = _FakeConnection(fetch_queue=[None, None])  # base absente, rôle absent
    project = _FakeConnection(fetch_queue=[])
    monkeypatch.setattr(db_init, "load_provisioning_env", _cfg)
    monkeypatch.setattr(db_init, "_connect_admin", lambda: admin)
    monkeypatch.setattr(db_init, "_connect_admin_project", lambda db_name: project)

    actions = db_init._init_postgres(_run_backend("postgres"))

    assert admin.autocommit is True, "CREATE DATABASE s'exécute hors transaction"
    assert 'CREATE DATABASE "ventes"' in admin.cursor_obj.executed
    assert 'CREATE ROLE "app" LOGIN PASSWORD \'apppwd\'' in admin.cursor_obj.executed
    assert 'GRANT CONNECT ON DATABASE "ventes" TO "app"' in admin.cursor_obj.executed
    assert project.cursor_obj.executed[0] == _MIGRATIONS_DDL
    assert (
        'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "app"'
        in project.cursor_obj.executed
    )
    assert project.committed is True
    assert any("forge_migrations" in a for a in actions)


def test_init_mssql_sequence_sql(monkeypatch):
    admin = _FakeConnection(fetch_queue=[None, None])  # base absente, login absent
    project = _FakeConnection(fetch_queue=[(None,)])  # utilisateur absent
    monkeypatch.setattr(db_init, "load_provisioning_env", _cfg)
    monkeypatch.setattr(db_init, "_connect_admin", lambda: admin)
    monkeypatch.setattr(db_init, "_connect_admin_project", lambda db_name: project)

    actions = db_init._init_mssql(_run_backend("mssql"))

    assert admin.autocommit is True
    assert "CREATE DATABASE [ventes]" in admin.cursor_obj.executed
    assert "CREATE LOGIN [app] WITH PASSWORD = N'apppwd'" in admin.cursor_obj.executed
    assert "CREATE USER [app] FOR LOGIN [app]" in project.cursor_obj.executed
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO [app]" in project.cursor_obj.executed
    assert _MIGRATIONS_DDL in project.cursor_obj.executed
    assert any("forge_migrations" in a for a in actions)


def test_init_postgres_idempotent_ne_recree_rien(monkeypatch):
    admin = _FakeConnection(fetch_queue=[(1,), (1,)])  # base et rôle présents
    project = _FakeConnection(fetch_queue=[])
    monkeypatch.setattr(db_init, "load_provisioning_env", _cfg)
    monkeypatch.setattr(db_init, "_connect_admin", lambda: admin)
    monkeypatch.setattr(db_init, "_connect_admin_project", lambda db_name: project)

    actions = db_init._init_postgres(_run_backend("postgres"))

    assert 'CREATE DATABASE "ventes"' not in admin.cursor_obj.executed
    assert not any(sql.startswith("CREATE ROLE") for sql in admin.cursor_obj.executed)
    assert any("déjà présente" in a for a in actions)
    assert any("mot de passe non modifié" in a for a in actions)
