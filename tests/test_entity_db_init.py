import sys
import types

import pytest

from forge_cli.entities.db_init import DbInitError, init_project_database, load_db_init_config


class FakeCursor:
    def __init__(self, state: dict[str, object], executed: list[str], fail_on: str | None = None):
        self.state = state
        self.executed = executed
        self.fail_on = fail_on
        self._rows: list[tuple[object, ...]] = []

    def execute(self, statement: str):
        if self.fail_on and self.fail_on in statement:
            raise RuntimeError("boom")
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


def test_load_db_init_config_reads_admin_and_app_separately(monkeypatch):
    fake_config = types.SimpleNamespace(
        DB_ADMIN_HOST="admin-host",
        DB_ADMIN_PORT=3307,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_HOST="app-host",
        DB_APP_PORT=3306,
        DB_APP_LOGIN="app-user",
        DB_APP_PWD="app-pwd",
    )
    monkeypatch.setitem(sys.modules, "config", fake_config)

    cfg = load_db_init_config()

    assert cfg.admin_host == "admin-host"
    assert cfg.admin_port == 3307
    assert cfg.admin_login == "admin-user"
    assert cfg.admin_password == "admin-pwd"
    assert cfg.db_name == "gestion_ventes"
    assert cfg.db_charset == "utf8mb4"
    assert cfg.db_collation == "utf8mb4_unicode_ci"
    assert cfg.app_host == "app-host"
    assert cfg.app_port == 3306
    assert cfg.app_login == "app-user"
    assert cfg.app_password == "app-pwd"


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
        DB_ADMIN_HOST="admin-host",
        DB_ADMIN_PORT=3307,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_HOST="localhost",
        DB_APP_PORT=3306,
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
    )
    captured_kwargs: dict[str, object] = {}

    def connect(**kwargs):
        captured_kwargs.update(kwargs)
        return connection

    fake_mariadb = types.SimpleNamespace(connect=connect)
    monkeypatch.setitem(sys.modules, "config", fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    actions = init_project_database()

    assert captured_kwargs == {
        "host": "admin-host",
        "port": 3307,
        "user": "admin-user",
        "password": "admin-pwd",
    }
    assert executed == [
        "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'gestion_ventes'",
        "CREATE DATABASE `gestion_ventes` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci",
        "SELECT Host FROM mysql.user WHERE User = 'forge_app' ORDER BY Host",
        "CREATE USER 'forge_app'@'localhost' IDENTIFIED BY 'secret'",
        "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES ON `gestion_ventes`.* TO 'forge_app'@'localhost'",
        "FLUSH PRIVILEGES",
    ]
    assert connection.committed is True
    assert actions == [
        "Base gestion_ventes créée.",
        "Utilisateur applicatif forge_app@localhost créé.",
        "Privilèges appliqués sur gestion_ventes à forge_app@localhost (SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES).",
    ]


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
        DB_ADMIN_HOST="admin-host",
        DB_ADMIN_PORT=3307,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_HOST="localhost",
        DB_APP_PORT=3306,
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
    )

    def connect(**kwargs):
        return connection

    fake_mariadb = types.SimpleNamespace(connect=connect)
    monkeypatch.setitem(sys.modules, "config", fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    actions = init_project_database()

    assert executed == [
        "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'gestion_ventes'",
        "SELECT Host FROM mysql.user WHERE User = 'forge_app' ORDER BY Host",
        "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES ON `gestion_ventes`.* TO 'forge_app'@'localhost'",
        "FLUSH PRIVILEGES",
    ]
    assert connection.committed is True
    assert actions == [
        "Base gestion_ventes déjà présente.",
        "Utilisateur applicatif forge_app@localhost déjà présent.",
        "Vérification manuelle nécessaire : le mot de passe et l'état de forge_app@localhost ne sont pas modifiés par forge db:init.",
        "Privilèges appliqués sur gestion_ventes à forge_app@localhost (SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES).",
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
        DB_ADMIN_HOST="admin-host",
        DB_ADMIN_PORT=3307,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_HOST="localhost",
        DB_APP_PORT=3306,
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
    )

    def connect(**kwargs):
        return connection

    fake_mariadb = types.SimpleNamespace(connect=connect)
    monkeypatch.setitem(sys.modules, "config", fake_config)
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
        DB_ADMIN_HOST="admin-host",
        DB_ADMIN_PORT=3307,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_HOST="localhost",
        DB_APP_PORT=3306,
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
    )

    def connect(**kwargs):
        return connection

    fake_mariadb = types.SimpleNamespace(connect=connect)
    monkeypatch.setitem(sys.modules, "config", fake_config)
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
        DB_ADMIN_HOST="admin-host",
        DB_ADMIN_PORT=3307,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="gestion_ventes",
        DB_CHARSET="utf8mb4",
        DB_COLLATION="utf8mb4_unicode_ci",
        DB_APP_HOST="localhost",
        DB_APP_PORT=3306,
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
    )

    def connect(**kwargs):
        return connections.pop(0)

    fake_mariadb = types.SimpleNamespace(connect=connect)
    monkeypatch.setitem(sys.modules, "config", fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    first_actions = init_project_database()
    second_actions = init_project_database()

    assert len(first_actions) == 3
    assert len(second_actions) == 4
