import sys
import types

import pytest

from cli.entities import db_init
from cli.entities.db_init import DbInitError, init_project_database, load_db_init_config


FORGE_MIGRATIONS_SQL = db_init.FORGE_MIGRATIONS_TABLE_SQL


class _FakeMariadbError(Exception):
    """Erreur MariaDB simulée portant un attribut ``errno`` (comme le driver)."""


class FakeCursor:
    def __init__(self, state: dict[str, object], executed: list[str], fail_on: str | None = None):
        self.state = state
        self.executed = executed
        self.fail_on = fail_on
        self._rows: list[tuple[object, ...]] = []

    def execute(self, statement: str):
        if self.fail_on and self.fail_on in statement:
            raise RuntimeError("boom")
        if self.state.get("deny_mysql_user") and "FROM mysql.user" in statement:
            error = _FakeMariadbError("SELECT command denied for table 'user'")
            error.errno = 1142
            raise error
        self.executed.append(statement)
        if "FROM INFORMATION_SCHEMA.SCHEMATA" in statement:
            db_name = self.state["db_name"]
            self._rows = [(db_name,)] if self.state["db_exists"] else []
            return
        if "FROM mysql.user" in statement:
            self._rows = [(host,) for host in self.state["user_hosts"]]
            return
        if statement.startswith("CREATE DATABASE "):
            self.state["db_exists"] = True
            self._rows = []
            return
        if statement.startswith("CREATE USER "):
            user_hosts = list(self.state["user_hosts"])
            if self.state["app_host"] not in user_hosts:
                user_hosts.append(self.state["app_host"])
            self.state["user_hosts"] = user_hosts
            self._rows = []
            return
        self._rows = []

    def fetchone(self):
        if not self._rows:
            return None
        return self._rows[0]

    def fetchall(self):
        return list(self._rows)

    def close(self):
        pass


class FakeConnection:
    def __init__(self, state: dict[str, object], executed: list[str], fail_on: str | None = None):
        self.state = state
        self.executed = executed
        self.fail_on = fail_on
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return FakeCursor(self.state, self.executed, self.fail_on)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


def _fake_config() -> types.SimpleNamespace:
    return types.SimpleNamespace(
        DB_HOST="db-host",
        DB_PORT=3306,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_LOGIN="app-user",
        DB_APP_PWD="app-pwd",
    )


def _apply_db_env(monkeypatch, fake_config: types.SimpleNamespace) -> None:
    """ADR-060 : les loaders lisent la config BDD dans l'environnement, plus dans
    les attributs de config.py. On reflète le fake_config dans os.environ."""
    for name in (
        "DB_HOST", "DB_PORT", "DB_ADMIN_LOGIN", "DB_ADMIN_PWD",
        "DB_NAME", "DB_CHARSET", "DB_COLLATION",
        "DB_APP_LOGIN", "DB_APP_PWD",
        "DB_APP_PRIVILEGES",
    ):
        if hasattr(fake_config, name):
            monkeypatch.setenv(name, str(getattr(fake_config, name)))


def _patch_db_init_config(monkeypatch, fake_config: types.SimpleNamespace) -> None:
    raw_privileges = getattr(fake_config, "DB_APP_PRIVILEGES", None)
    privileges = (
        db_init._parse_app_privileges(raw_privileges)
        if raw_privileges is not None
        else db_init.DEFAULT_APP_PRIVILEGES
    )
    # ADR-060/ADR-066 : le backend lit le serveur partagé (DB_HOST/DB_PORT) et les
    # identifiants d'administration dans l'env.
    monkeypatch.setenv("DB_HOST", str(getattr(fake_config, "DB_HOST", "localhost")))
    monkeypatch.setenv("DB_PORT", str(getattr(fake_config, "DB_PORT", 3306)))
    monkeypatch.setenv("DB_ADMIN_LOGIN", str(getattr(fake_config, "DB_ADMIN_LOGIN", "")))
    monkeypatch.setenv("DB_ADMIN_PWD", str(getattr(fake_config, "DB_ADMIN_PWD", "")))
    monkeypatch.setattr(
        db_init,
        "load_db_init_config",
        lambda: db_init.DbInitConfig(
            db_name=fake_config.DB_NAME,
            db_charset=fake_config.DB_CHARSET,
            db_collation=fake_config.DB_COLLATION,
            app_host=fake_config.DB_HOST,
            app_port=fake_config.DB_PORT,
            app_login=fake_config.DB_APP_LOGIN,
            app_password=fake_config.DB_APP_PWD,
            app_privileges=privileges,
        ),
    )


def _write_config(path, fake_config: types.SimpleNamespace) -> None:
    lines = [
        f"DB_HOST={fake_config.DB_HOST!r}",
        f"DB_PORT={fake_config.DB_PORT!r}",
        f"DB_ADMIN_LOGIN={fake_config.DB_ADMIN_LOGIN!r}",
        f"DB_ADMIN_PWD={fake_config.DB_ADMIN_PWD!r}",
        f"DB_NAME={fake_config.DB_NAME!r}",
        f"DB_CHARSET={fake_config.DB_CHARSET!r}",
        f"DB_COLLATION={fake_config.DB_COLLATION!r}",
        f"DB_APP_LOGIN={fake_config.DB_APP_LOGIN!r}",
        f"DB_APP_PWD={fake_config.DB_APP_PWD!r}",
    ]
    if hasattr(fake_config, "DB_APP_PRIVILEGES"):
        lines.append(f"DB_APP_PRIVILEGES={fake_config.DB_APP_PRIVILEGES!r}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def test_load_db_init_config_reads_provisioning_and_app(monkeypatch, tmp_path):
    # ADR-060 : les identifiants d'administration (connexion) sont lus par le
    # backend depuis DB_ADMIN_* ; le loader ne porte plus que les paramètres de
    # provisionnement (base, jeu de caractères, compte applicatif).
    fake_config = _fake_config()
    _write_config(tmp_path / "config.py", fake_config)
    _apply_db_env(monkeypatch, fake_config)
    monkeypatch.chdir(tmp_path)

    cfg = load_db_init_config()

    for absent in ("admin_host", "admin_port", "admin_login", "admin_password"):
        assert not hasattr(cfg, absent), f"DbInitConfig ne doit plus porter {absent}"
    assert cfg.db_name == "gestion_ventes"
    assert cfg.db_charset == "utf8mb4"
    assert cfg.db_collation == "utf8mb4_unicode_ci"
    assert cfg.app_host == "db-host"
    assert cfg.app_port == 3306
    assert cfg.app_login == "app-user"
    assert cfg.app_password == "app-pwd"
    assert cfg.app_privileges == db_init.DEFAULT_APP_PRIVILEGES


def test_load_db_init_config_uses_current_working_directory(monkeypatch, tmp_path):
    fake_config = _fake_config()
    fake_config.DB_NAME = "cwd_db"
    _write_config(tmp_path / "config.py", fake_config)
    _apply_db_env(monkeypatch, fake_config)
    monkeypatch.chdir(tmp_path)

    cfg = load_db_init_config()

    assert cfg.db_name == "cwd_db"


def test_db_init_hors_projet_erreur_propre(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit):
        db_init.main(["db:init"])

    output = capsys.readouterr().out
    assert "config.py absent" in output
    assert "ModuleNotFoundError" not in output


def test_db_init_creates_missing_database_and_app_user(monkeypatch):
    executed: list[str] = []
    state = {
        "db_name": "gestion_ventes",
        "db_exists": False,
        "user_hosts": [],
        "app_host": "localhost",
    }
    connection = FakeConnection(state, executed)
    fake_config = types.SimpleNamespace(
        DB_HOST="localhost",
        DB_PORT=3306,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
    )
    captured_kwargs: dict[str, object] = {}

    def connect(**kwargs):
        captured_kwargs.update(kwargs)
        return connection

    fake_mariadb = types.SimpleNamespace(connect=connect)
    _patch_db_init_config(monkeypatch, fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    actions = init_project_database()

    assert captured_kwargs == {
        "host": "localhost",
        "port": 3306,
        "user": "admin-user",
        "password": "admin-pwd",
    }
    assert executed == [
        "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'gestion_ventes'",
        "CREATE DATABASE `gestion_ventes` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci",
        "SELECT Host FROM mysql.user WHERE User = 'forge_app' ORDER BY Host",
        "CREATE USER 'forge_app'@'localhost' IDENTIFIED BY 'secret'",
        "GRANT SELECT, INSERT, UPDATE, DELETE ON `gestion_ventes`.* TO 'forge_app'@'localhost'",
        "USE `gestion_ventes`",
        FORGE_MIGRATIONS_SQL,
    ]
    assert connection.committed is True
    assert actions == [
        "Base gestion_ventes créée.",
        "Utilisateur applicatif forge_app@localhost créé.",
        "Privilèges appliqués sur gestion_ventes à forge_app@localhost (SELECT, INSERT, UPDATE, DELETE).",
        "Table forge_migrations prête.",
    ]


def test_db_init_degrades_when_mysql_user_read_denied(monkeypatch):
    """DB-INIT-MYSQL-USER-GRANT-001 — repli si la lecture de mysql.user est refusée.

    Un compte d'administration minimal (forge_admin sans SELECT sur mysql.user)
    ne peut pas lire les hôtes du compte applicatif. db:init ne doit pas échouer :
    il bascule sur CREATE USER IF NOT EXISTS et signale le mode dégradé.
    """
    executed: list[str] = []
    state = {
        "db_name": "gestion_ventes",
        "db_exists": False,
        "user_hosts": [],
        "app_host": "localhost",
        "deny_mysql_user": True,
    }
    connection = FakeConnection(state, executed)
    fake_config = types.SimpleNamespace(
        DB_HOST="localhost",
        DB_PORT=3306,
        DB_ADMIN_LOGIN="forge_admin",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
    )

    def connect(**kwargs):
        return connection

    fake_mariadb = types.SimpleNamespace(connect=connect)
    _patch_db_init_config(monkeypatch, fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    actions = init_project_database()

    # Le SELECT sur mysql.user a été tenté puis refusé : il n'est pas exécuté.
    assert not any("FROM mysql.user" in s for s in executed)
    # Repli : CREATE USER IF NOT EXISTS au lieu de CREATE USER nu.
    assert (
        "CREATE USER IF NOT EXISTS 'forge_app'@'localhost' IDENTIFIED BY 'secret'"
        in executed
    )
    # Les privilèges applicatifs et la table de migrations sont quand même posés.
    assert (
        "GRANT SELECT, INSERT, UPDATE, DELETE ON `gestion_ventes`.* TO 'forge_app'@'localhost'"
        in executed
    )
    assert connection.committed is True
    # Une action signale explicitement le mode dégradé.
    assert any("mysql.user" in a and "ignorée" in a for a in actions)
    assert any("créé ou déjà présent" in a for a in actions)


def test_db_init_reports_existing_database_and_user_then_reapplies_privileges(monkeypatch):
    executed: list[str] = []
    state = {
        "db_name": "gestion_ventes",
        "db_exists": True,
        "user_hosts": ["localhost"],
        "app_host": "localhost",
    }
    connection = FakeConnection(state, executed)
    fake_config = types.SimpleNamespace(
        DB_HOST="localhost",
        DB_PORT=3306,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
    )

    def connect(**kwargs):
        return connection

    fake_mariadb = types.SimpleNamespace(connect=connect)
    _patch_db_init_config(monkeypatch, fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    actions = init_project_database()

    assert executed == [
        "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'gestion_ventes'",
        "SELECT Host FROM mysql.user WHERE User = 'forge_app' ORDER BY Host",
        "GRANT SELECT, INSERT, UPDATE, DELETE ON `gestion_ventes`.* TO 'forge_app'@'localhost'",
        "USE `gestion_ventes`",
        FORGE_MIGRATIONS_SQL,
    ]
    assert connection.committed is True
    assert actions == [
        "Base gestion_ventes déjà présente.",
        "Utilisateur applicatif forge_app@localhost déjà présent.",
        "Vérification manuelle nécessaire : le mot de passe et l'état de forge_app@localhost ne sont pas modifiés par forge db:init.",
        "Privilèges appliqués sur gestion_ventes à forge_app@localhost (SELECT, INSERT, UPDATE, DELETE).",
        "Table forge_migrations prête.",
    ]


def test_db_init_requires_manual_verification_for_existing_user_on_other_host(monkeypatch):
    executed: list[str] = []
    state = {
        "db_name": "gestion_ventes",
        "db_exists": True,
        "user_hosts": ["%"],
        "app_host": "localhost",
    }
    connection = FakeConnection(state, executed)
    fake_config = types.SimpleNamespace(
        DB_HOST="localhost",
        DB_PORT=3306,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
    )

    def connect(**kwargs):
        return connection

    fake_mariadb = types.SimpleNamespace(connect=connect)
    _patch_db_init_config(monkeypatch, fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    with pytest.raises(DbInitError, match="Vérification manuelle nécessaire"):
        init_project_database()

    assert executed == [
        "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'gestion_ventes'",
        "SELECT Host FROM mysql.user WHERE User = 'forge_app' ORDER BY Host",
    ]
    assert connection.rolled_back is True


def test_db_init_rolls_back_on_sql_error(monkeypatch):
    executed: list[str] = []
    state = {
        "db_name": "gestion_ventes",
        "db_exists": False,
        "user_hosts": [],
        "app_host": "localhost",
    }
    connection = FakeConnection(state, executed, fail_on="GRANT")
    fake_config = types.SimpleNamespace(
        DB_HOST="localhost",
        DB_PORT=3306,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
    )

    def connect(**kwargs):
        return connection

    fake_mariadb = types.SimpleNamespace(connect=connect)
    _patch_db_init_config(monkeypatch, fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    with pytest.raises(DbInitError, match="Provisioning MariaDB impossible"):
        init_project_database()

    assert connection.rolled_back is True


def test_db_init_is_idempotent(monkeypatch):
    first_executed: list[str] = []
    second_executed: list[str] = []
    first_state = {
        "db_name": "gestion_ventes",
        "db_exists": False,
        "user_hosts": [],
        "app_host": "localhost",
    }
    second_state = {
        "db_name": "gestion_ventes",
        "db_exists": True,
        "user_hosts": ["localhost"],
        "app_host": "localhost",
    }
    connections = [
        FakeConnection(first_state, first_executed),
        FakeConnection(second_state, second_executed),
    ]
    fake_config = types.SimpleNamespace(
        DB_HOST="localhost",
        DB_PORT=3306,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
    )

    def connect(**kwargs):
        return connections.pop(0)

    fake_mariadb = types.SimpleNamespace(connect=connect)
    _patch_db_init_config(monkeypatch, fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    first_actions = init_project_database()
    second_actions = init_project_database()

    assert FORGE_MIGRATIONS_SQL in first_executed
    assert FORGE_MIGRATIONS_SQL in second_executed
    assert len(first_actions) == 4
    assert len(second_actions) == 5


def test_load_db_init_config_reads_custom_db_app_privileges(monkeypatch, tmp_path):
    fake_config = _fake_config()
    fake_config.DB_APP_PRIVILEGES = "SELECT,INSERT,UPDATE"
    _write_config(tmp_path / "config.py", fake_config)
    _apply_db_env(monkeypatch, fake_config)
    monkeypatch.chdir(tmp_path)

    cfg = load_db_init_config()

    assert cfg.app_privileges == ("SELECT", "INSERT", "UPDATE")


def test_load_db_init_config_rejects_invalid_privilege(monkeypatch, tmp_path):
    from cli.entities.db_init import DbInitError

    fake_config = _fake_config()
    fake_config.DB_APP_PRIVILEGES = "SELECT,TRUNCATE"
    _write_config(tmp_path / "config.py", fake_config)
    _apply_db_env(monkeypatch, fake_config)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(DbInitError, match="TRUNCATE"):
        load_db_init_config()


def test_db_init_uses_custom_privileges_in_grant(monkeypatch):
    executed: list[str] = []
    state = {
        "db_name": "gestion_ventes",
        "db_exists": False,
        "user_hosts": [],
        "app_host": "localhost",
    }
    connection = FakeConnection(state, executed)
    fake_config = types.SimpleNamespace(
        DB_HOST="localhost",
        DB_PORT=3306,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
        DB_APP_PRIVILEGES="SELECT,INSERT",
    )

    def connect(**kwargs):
        return connection

    fake_mariadb = types.SimpleNamespace(connect=connect)
    _patch_db_init_config(monkeypatch, fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    actions = init_project_database()

    grant_stmt = next(s for s in executed if s.startswith("GRANT"))
    assert grant_stmt == "GRANT SELECT, INSERT ON `gestion_ventes`.* TO 'forge_app'@'localhost'"
    assert any("SELECT, INSERT" in a for a in actions)


def test_db_init_creates_forge_migrations_table_idempotently(monkeypatch):
    executed: list[str] = []
    state = {
        "db_name": "gestion_ventes",
        "db_exists": True,
        "user_hosts": ["localhost"],
        "app_host": "localhost",
    }
    connection = FakeConnection(state, executed)
    fake_config = types.SimpleNamespace(
        DB_HOST="localhost",
        DB_PORT=3306,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
    )

    def connect(**kwargs):
        return connection

    fake_mariadb = types.SimpleNamespace(connect=connect)
    _patch_db_init_config(monkeypatch, fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    actions = init_project_database()

    assert "USE `gestion_ventes`" in executed
    assert FORGE_MIGRATIONS_SQL in executed
    assert FORGE_MIGRATIONS_SQL.startswith("CREATE TABLE IF NOT EXISTS forge_migrations")
    assert "UNIQUE KEY uq_forge_migrations_version (version)" in FORGE_MIGRATIONS_SQL
    assert "UNIQUE KEY uq_forge_migrations_filename (filename)" in FORGE_MIGRATIONS_SQL
    assert "Table forge_migrations prête." in actions


def test_db_init_quotes_database_before_creating_forge_migrations(monkeypatch):
    executed: list[str] = []
    state = {
        "db_name": "gestion`ventes",
        "db_exists": True,
        "user_hosts": ["localhost"],
        "app_host": "localhost",
    }
    connection = FakeConnection(state, executed)
    fake_config = types.SimpleNamespace(
        DB_HOST="localhost",
        DB_PORT=3306,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion`ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
    )

    def connect(**kwargs):
        return connection

    fake_mariadb = types.SimpleNamespace(connect=connect)
    _patch_db_init_config(monkeypatch, fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    init_project_database()

    assert "USE `gestion``ventes`" in executed


def test_db_init_refuse_provisioning_backend_serveur_non_mariadb(monkeypatch):
    """db:init révèle clairement qu'il ne provisionne pas encore postgres/mssql
    (backend serveur sans provisioning), au lieu d'exécuter du SQL MariaDB."""
    pytest.importorskip("forge_mvc_postgres")
    from core.database import backend as backend_module

    monkeypatch.setenv("DB_BACKEND", "postgres")
    backend_module.reset_backend()
    try:
        with pytest.raises(DbInitError) as excinfo:
            init_project_database()
    finally:
        backend_module.reset_backend()

    message = str(excinfo.value)
    assert "postgres" in message
    assert "db:apply" in message
