import json
import sys
import types
from pathlib import Path

import pytest

from cli.entities import db_apply
from cli.entities.db_apply import (
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
        "schema_version": "1.0",
        "name": "Contact",
        "table": "contact",
        "description": "",
        "fields": [{"name": "nom", "type": "string", "max_length": 100}],
    }


def _commande() -> dict:
    return {
        "schema_version": "1.0",
        "name": "Commande",
        "table": "commande",
        "description": "",
        "fields": [{"name": "contact_id", "type": "integer"}],
    }


def _relations() -> dict:
    return {"schema_version": "1.0", "relations": []}


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
        DB_HOST="admin-host",
        DB_PORT=3307,
        DB_ADMIN_LOGIN="admin",
        DB_ADMIN_PWD="admin-secret",
        DB_NAME="forge_db",
    )
    captured_kwargs: dict[str, object] = {}

    def connect(**kwargs):
        captured_kwargs.update(kwargs)
        return connection

    fake_mariadb = types.SimpleNamespace(connect=connect)
    _patch_db_apply_config(monkeypatch, fake_config)
    # ADR-060 : le backend lit les identifiants d'administration dans l'env.
    monkeypatch.setenv("DB_HOST", fake_config.DB_HOST)
    monkeypatch.setenv("DB_PORT", str(fake_config.DB_PORT))
    monkeypatch.setenv("DB_ADMIN_LOGIN", fake_config.DB_ADMIN_LOGIN)
    monkeypatch.setenv("DB_ADMIN_PWD", fake_config.DB_ADMIN_PWD)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)
    return captured_kwargs


def _patch_db_apply_config(monkeypatch, fake_config: types.SimpleNamespace) -> None:
    monkeypatch.setattr(
        db_apply,
        "load_db_apply_config",
        lambda: db_apply.DbApplyConfig(database=fake_config.DB_NAME),
    )


def _write_config(path: Path, fake_config: types.SimpleNamespace) -> None:
    path.write_text(
        "\n".join(
            [
                f"DB_HOST={fake_config.DB_HOST!r}",
                f"DB_PORT={fake_config.DB_PORT!r}",
                f"DB_ADMIN_LOGIN={fake_config.DB_ADMIN_LOGIN!r}",
                f"DB_ADMIN_PWD={fake_config.DB_ADMIN_PWD!r}",
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


def test_collect_sql_files_inclut_models_sql(tmp_path: Path):
    # FORGE-3 : le SQL applicatif de mvc/models/sql (ex. socle auth:init) est
    # appliqué, après les entités et relations, en ordre alphabétique interne.
    root = tmp_path / "mvc" / "entities"
    (root / "contact").mkdir(parents=True)
    models_sql = tmp_path / "mvc" / "models" / "sql"
    models_sql.mkdir(parents=True)
    (models_sql / "users.sql").write_text("CREATE TABLE users (Id INT);\n", encoding="utf-8")
    (models_sql / "auth_tokens.sql").write_text("CREATE TABLE auth_tokens (Id INT);\n", encoding="utf-8")
    files = collect_sql_files(root)
    assert [item.path.as_posix() for item in files] == [
        (root / "contact" / "contact.sql").as_posix(),
        (root / "relations.sql").as_posix(),
        (models_sql / "auth_tokens.sql").as_posix(),
        (models_sql / "users.sql").as_posix(),
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
        "host": "admin-host",
        "port": 3307,
        "user": "admin",
        "password": "admin-secret",
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


def test_load_db_apply_config_returns_db_name(monkeypatch, tmp_path):
    # ADR-060 : les identifiants d'administration sont lus par le backend depuis
    # DB_ADMIN_* ; le loader ne porte plus que le nom de la base cible (DB_NAME).
    fake_config = types.SimpleNamespace(
        DB_HOST="admin-host",
        DB_PORT=3310,
        DB_ADMIN_LOGIN="admin-user",
        DB_ADMIN_PWD="admin-pwd",
        DB_NAME="app-db",
    )
    _write_config(tmp_path / "config.py", fake_config)
    monkeypatch.setenv("DB_NAME", fake_config.DB_NAME)  # ADR-060 : DB_NAME lu dans l'env
    monkeypatch.chdir(tmp_path)

    cfg = load_db_apply_config()

    assert cfg.database == "app-db"
    for absent in ("host", "port", "login", "password"):
        assert not hasattr(cfg, absent)


def test_load_db_apply_config_uses_current_working_directory(monkeypatch, tmp_path):
    fake_config = types.SimpleNamespace(
        DB_HOST="localhost",
        DB_PORT=3306,
        DB_ADMIN_LOGIN="forge_admin",
        DB_ADMIN_PWD="secret",
        DB_NAME="cwd_apply_db",
    )
    _write_config(tmp_path / "config.py", fake_config)
    monkeypatch.setenv("DB_NAME", fake_config.DB_NAME)  # ADR-060 : DB_NAME lu dans l'env
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
    _write_relations(root, {"schema_version": "1.0", "relations": []}, "")

    fake_config = types.SimpleNamespace(
        DB_HOST="localhost",
        DB_PORT=3306,
        DB_ADMIN_LOGIN="forge_admin",
        DB_ADMIN_PWD="secret",
        DB_NAME="forge_db",
    )

    def connect(**kwargs):
        raise RuntimeError("Unknown database")

    fake_mariadb = types.SimpleNamespace(connect=connect)
    _patch_db_apply_config(monkeypatch, fake_config)
    monkeypatch.setitem(sys.modules, "mariadb", fake_mariadb)

    with pytest.raises(DbApplyError, match="forge db:init"):
        apply_model_sql(root)


def test_apply_model_sql_serverless_sqlite(tmp_path: Path, monkeypatch):
    """db:apply route par le backend pour un projet SQLite et crée les tables."""
    pytest.importorskip("forge_mvc_sqlite")
    import sqlite3

    from core.database import backend as backend_module

    root = tmp_path / "mvc" / "entities"
    _write_entity(
        root,
        "contact",
        _contact(),
        "CREATE TABLE IF NOT EXISTS contact (Id INTEGER PRIMARY KEY AUTOINCREMENT, Nom TEXT);\n",
    )
    _write_relations(root, _relations(), "")

    db_file = tmp_path / "app.db"
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    # ADR-060 : le backend lit le chemin du fichier dans DB_NAME (env) ; ici
    # load_project_config est mocké, on pose donc DB_NAME explicitement.
    monkeypatch.setenv("DB_NAME", str(db_file))
    monkeypatch.setattr(
        "cli.project.project_config.load_project_config",
        lambda: types.SimpleNamespace(APP_NAME="t", DB_NAME=str(db_file)),
    )

    backend_module.reset_backend()
    try:
        applied = apply_model_sql(root)
    finally:
        backend_module.reset_backend()

    assert any(p.name == "contact.sql" for p in applied)
    assert db_file.exists()
    conn = sqlite3.connect(str(db_file))
    try:
        tables = {
            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "contact" in tables
        conn.execute("INSERT INTO contact (Nom) VALUES (?)", ("Ada",))
        conn.commit()
    finally:
        conn.close()
