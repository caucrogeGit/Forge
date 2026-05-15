import json
import sys
import types
from pathlib import Path

import pytest

from forge_cli.entities import db_apply
from forge_cli.entities.db_apply import (
    DbApplyError,
    apply_model_sql,
    collect_sql_files,
    load_db_apply_config,
    verify_sql_files,
)


def _write_entity(root: Path, folder: str, data: dict, sql: str) -> None:
    entity_dir = root / folder
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{folder}.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (entity_dir / f"{folder}.sql").write_text(sql, encoding="utf-8")


def _write_relations(root: Path, relations: dict, sql: str) -> None:
    (root / "relations.json").write_text(json.dumps(relations, indent=2) + "\n", encoding="utf-8")
    (root / "relations.sql").write_text(sql, encoding="utf-8")


def _contact() -> dict:
    return {
        "format_version": 1,
        "entity": "Contact",
        "table": "contact",
        "description": "",
        "fields": [
            {
                "name": "id",
                "column": "Id",
                "python_type": "int",
                "sql_type": "INT",
                "nullable": False,
                "primary_key": True,
                "auto_increment": True,
                "constraints": {},
            }
        ],
    }


def _commande() -> dict:
    return {
        "format_version": 1,
        "entity": "Commande",
        "table": "commande",
        "description": "",
        "fields": [
            {
                "name": "id",
                "column": "Id",
                "python_type": "int",
                "sql_type": "INT",
                "nullable": False,
                "primary_key": True,
                "auto_increment": True,
                "constraints": {},
            },
            {
                "name": "contact_id",
                "column": "ContactId",
                "python_type": "int",
                "sql_type": "INT",
                "nullable": False,
                "primary_key": False,
                "auto_increment": False,
                "constraints": {},
            },
        ],
    }


def _relations() -> dict:
    return {
        "format_version": 1,
        "relations": [
            {
                "name": "commande_contact",
                "type": "many_to_one",
                "from_entity": "Commande",
                "to_entity": "Contact",
                "from_field": "contact_id",
                "to_field": "id",
                "foreign_key_name": "fk_commande_contact",
                "on_delete": "RESTRICT",
                "on_update": "CASCADE",
            }
        ],
    }


class FakeCursor:
    def __init__(self, executed: list[str], fail_on: str | None = None):
        self.executed = executed
        self.fail_on = fail_on

    def execute(self, statement: str):
        if self.fail_on and self.fail_on in statement:
            raise RuntimeError("boom")
        self.executed.append(statement)

    def close(self):
        pass


class FakeConnection:
    def __init__(self, executed: list[str], fail_on: str | None = None):
        self.executed = executed
        self.fail_on = fail_on
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return FakeCursor(self.executed, self.fail_on)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


def _install_fake_modules(monkeypatch, connection: FakeConnection):
    fake_config = types.SimpleNamespace(
        DB_ADMIN_HOST="admin-host",
        DB_ADMIN_PORT=3307,
        DB_ADMIN_LOGIN="admin",
        DB_ADMIN_PWD="admin-secret",
        DB_APP_HOST="localhost",
        DB_APP_PORT=3306,
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
        DB_NAME="forge_db",
    )
    captured_kwargs: dict[str, object] = {}

    def connect(**kwargs):
        captured_kwargs.update(kwargs)
        return connection

    fake_mariadb = types.SimpleNamespace(connect=connect)
    _patch_db_apply_config(monkeypatch, fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)
    return captured_kwargs


def _patch_db_apply_config(monkeypatch, fake_config: types.SimpleNamespace) -> None:
    monkeypatch.setattr(
        db_apply,
        "load_db_apply_config",
        lambda: db_apply.DbApplyConfig(
            host=fake_config.DB_APP_HOST,
            port=fake_config.DB_APP_PORT,
            login=fake_config.DB_APP_LOGIN,
            password=fake_config.DB_APP_PWD,
            database=fake_config.DB_NAME,
        ),
    )


def _write_config(path: Path, fake_config: types.SimpleNamespace) -> None:
    path.write_text(
        "\n".join(
            [
                f"DB_APP_HOST={fake_config.DB_APP_HOST!r}",
                f"DB_APP_PORT={fake_config.DB_APP_PORT!r}",
                f"DB_APP_LOGIN={fake_config.DB_APP_LOGIN!r}",
                f"DB_APP_PWD={fake_config.DB_APP_PWD!r}",
                f"DB_NAME={fake_config.DB_NAME!r}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_collect_sql_files_orders_entities_then_relations(tmp_path: Path):
    root = tmp_path / "mvc" / "entities"
    (root / "zeta").mkdir(parents=True)
    (root / "alpha").mkdir(parents=True)
    files = collect_sql_files(root)
    assert [item.path.as_posix() for item in files] == [
        (root / "alpha" / "alpha.sql").as_posix(),
        (root / "zeta" / "zeta.sql").as_posix(),
        (root / "relations.sql").as_posix(),
    ]


def test_verify_sql_files_rejects_missing_or_empty_entity_sql(tmp_path: Path):
    root = tmp_path / "mvc" / "entities"
    (root / "contact").mkdir(parents=True)
    files = collect_sql_files(root)
    with pytest.raises(DbApplyError):
        verify_sql_files(files)

    (root / "contact" / "contact.sql").write_text("", encoding="utf-8")
    (root / "relations.sql").write_text("", encoding="utf-8")
    with pytest.raises(DbApplyError, match="fichier SQL d'entite vide"):
        verify_sql_files(files)


def test_apply_model_sql_executes_entities_then_relations_and_empty_relations_is_noop(tmp_path: Path, monkeypatch):
    root = tmp_path / "mvc" / "entities"
    _write_entity(root, "contact", _contact(), "CREATE TABLE contact (Id INT);\n")
    _write_entity(root, "commande", _commande(), "CREATE TABLE commande (Id INT, ContactId INT);\n")
    _write_relations(root, _relations(), "")

    executed: list[str] = []
    connection = FakeConnection(executed)
    captured_kwargs = _install_fake_modules(monkeypatch, connection)

    applied = apply_model_sql(root)

    assert [path.name for path in applied] == ["commande.sql", "contact.sql"]
    assert executed == [
        "CREATE TABLE commande (Id INT, ContactId INT)",
        "CREATE TABLE contact (Id INT)",
    ]
    assert connection.committed is True
    assert captured_kwargs == {
        "host": "localhost",
        "port": 3306,
        "user": "forge_app",
        "password": "secret",
        "database": "forge_db",
    }


def test_apply_model_sql_rolls_back_on_first_sql_error(tmp_path: Path, monkeypatch):
    root = tmp_path / "mvc" / "entities"
    _write_entity(root, "contact", _contact(), "CREATE TABLE contact (Id INT);\n")
    _write_entity(root, "commande", _commande(), "CREATE TABLE commande (Id INT, ContactId INT);\n")
    _write_relations(root, _relations(), "ALTER TABLE commande ADD CONSTRAINT fk FOREIGN KEY (ContactId) REFERENCES contact (Id);\n")

    executed: list[str] = []
    connection = FakeConnection(executed, fail_on="ALTER TABLE")
    _install_fake_modules(monkeypatch, connection)

    with pytest.raises(DbApplyError, match="relations.sql: erreur SQL"):
        apply_model_sql(root)

    assert connection.rolled_back is True


def test_load_db_apply_config_uses_app_credentials(monkeypatch, tmp_path):
    fake_config = types.SimpleNamespace(
        DB_APP_HOST="app-host",
        DB_APP_PORT=3310,
        DB_APP_LOGIN="app-user",
        DB_APP_PWD="app-pwd",
        DB_NAME="app-db",
    )
    _write_config(tmp_path / "config.py", fake_config)
    monkeypatch.chdir(tmp_path)

    cfg = load_db_apply_config()

    assert cfg.host == "app-host"
    assert cfg.port == 3310
    assert cfg.login == "app-user"
    assert cfg.password == "app-pwd"
    assert cfg.database == "app-db"


def test_load_db_apply_config_uses_current_working_directory(monkeypatch, tmp_path):
    fake_config = types.SimpleNamespace(
        DB_APP_HOST="localhost",
        DB_APP_PORT=3306,
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
        DB_NAME="cwd_apply_db",
    )
    _write_config(tmp_path / "config.py", fake_config)
    monkeypatch.chdir(tmp_path)

    cfg = load_db_apply_config()

    assert cfg.database == "cwd_apply_db"


def test_db_apply_hors_projet_erreur_propre(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit):
        db_apply.main(["db:apply"])

    output = capsys.readouterr().out
    assert "config.py absent" in output or "mvc/entities" in output
    assert "ModuleNotFoundError" not in output


def test_apply_model_sql_reports_missing_database_preparation(tmp_path: Path, monkeypatch):
    root = tmp_path / "mvc" / "entities"
    _write_entity(root, "contact", _contact(), "CREATE TABLE contact (Id INT);\n")
    _write_relations(root, {"format_version": 1, "relations": []}, "")

    fake_config = types.SimpleNamespace(
        DB_APP_HOST="localhost",
        DB_APP_PORT=3306,
        DB_APP_LOGIN="forge_app",
        DB_APP_PWD="secret",
        DB_NAME="forge_db",
    )

    def connect(**kwargs):
        raise RuntimeError("Unknown database")

    fake_mariadb = types.SimpleNamespace(connect=connect)
    _patch_db_apply_config(monkeypatch, fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    with pytest.raises(DbApplyError, match="forge db:init"):
        apply_model_sql(root)
