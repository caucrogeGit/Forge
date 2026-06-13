"""Tests DB-APPLY-ADMIN-CREDS-001 — les migrations utilisent DB_ADMIN_* (ADR-033).

`forge db:apply` / `migration:status` appliquent des changements de structure :
ils se connectent en `DB_ADMIN_*`, pas en `DB_APP_*`. Le compte applicatif
`forge_app` reste en DML strict (plus de DDL accordé par défaut).
"""

import types
from pathlib import Path

import pytest

_SKELETON_ENV = Path(__file__).parent.parent / "forge_cli" / "skeleton" / "data" / "env" / "example"


def test_load_migration_db_config_uses_admin(monkeypatch):
    from forge_cli.entities import migrations

    fake = types.SimpleNamespace(
        DB_ADMIN_HOST="adminhost", DB_ADMIN_PORT=1,
        DB_ADMIN_LOGIN="forge_admin", DB_ADMIN_PWD="adminpwd",
        DB_APP_HOST="apphost", DB_APP_PORT=2,
        DB_APP_LOGIN="forge_app", DB_APP_PWD="apppwd",
        DB_NAME="projet_db",
    )
    monkeypatch.setattr(migrations, "load_project_config", lambda: fake)

    cfg = migrations.load_migration_db_config()

    assert cfg.login == "forge_admin", "les migrations doivent se connecter en DB_ADMIN_*"
    assert cfg.host == "adminhost"
    assert cfg.port == 1
    assert cfg.password == "adminpwd"
    assert cfg.database == "projet_db"


def test_db_init_default_app_privileges_dml_only():
    """forge_app n'est plus provisionné avec du DDL par défaut (ADR-033)."""
    from forge_cli.entities import db_init

    assert set(db_init.DEFAULT_APP_PRIVILEGES) == {"SELECT", "INSERT", "UPDATE", "DELETE"}
    for ddl in ("CREATE", "ALTER", "DROP", "INDEX", "REFERENCES"):
        assert ddl not in db_init.DEFAULT_APP_PRIVILEGES, (
            f"{ddl} ne doit plus être accordé par défaut à forge_app"
        )


def test_db_init_still_connects_as_admin():
    """db:init reste en DB_ADMIN_* (inchangé)."""
    from forge_cli.entities import db_init

    src = Path(db_init.__file__).read_text(encoding="utf-8")
    assert "admin_host" in src and "admin_login" in src


@pytest.mark.parametrize("var", ["DB_APP_PRIVILEGES"])
def test_skeleton_env_example_sans_ddl_app(var):
    """Le squelette ne suggère plus d'accorder du DDL à forge_app."""
    assert var not in _SKELETON_ENV.read_text(encoding="utf-8")
