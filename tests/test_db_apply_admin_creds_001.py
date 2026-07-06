"""Tests DB-APPLY-ADMIN-CREDS-001 — les migrations utilisent DB_ADMIN_* (ADR-033).

`forge db:apply` / `migration:status` appliquent des changements de structure :
ils se connectent en `DB_ADMIN_*`, pas en `DB_APP_*`. Le compte applicatif
`forge_app` reste en DML strict (plus de DDL accordé par défaut).
"""

import types
from pathlib import Path

import pytest

_SKELETON_ENV = Path(__file__).parent.parent / "skeleton" / "data" / "env" / "example"


def test_load_migration_db_config_ne_porte_que_la_base(monkeypatch):
    # ADR-060 : les identifiants d'administration sont lus par le backend depuis
    # DB_ADMIN_*. Le loader ne porte plus que le nom de la base cible ; il
    # n'expose aucun identifiant (ni admin ni app).
    from cli.entities import migrations

    fake = types.SimpleNamespace(
        DB_ADMIN_HOST="adminhost", DB_ADMIN_PORT=1,
        DB_ADMIN_LOGIN="forge_admin", DB_ADMIN_PWD="adminpwd",
        DB_APP_HOST="apphost", DB_APP_PORT=2,
        DB_APP_LOGIN="forge_app", DB_APP_PWD="apppwd",
        DB_NAME="projet_db",
    )
    monkeypatch.setattr(migrations, "load_project_config", lambda: fake)
    monkeypatch.setenv("DB_NAME", "projet_db")  # ADR-060 : DB_NAME lu dans l'env

    cfg = migrations.load_migration_db_config()

    assert cfg.database == "projet_db"
    for absent in ("host", "port", "login", "password"):
        assert not hasattr(cfg, absent), f"le loader ne doit plus exposer {absent}"


def test_load_db_apply_config_ne_porte_que_la_base(monkeypatch):
    # ADR-060 : idem db:apply, le loader ne porte plus que la base cible.
    from cli.entities import db_apply

    fake = types.SimpleNamespace(
        DB_ADMIN_HOST="adminhost", DB_ADMIN_PORT=1,
        DB_ADMIN_LOGIN="forge_admin", DB_ADMIN_PWD="adminpwd",
        DB_APP_HOST="apphost", DB_APP_PORT=2,
        DB_APP_LOGIN="forge_app", DB_APP_PWD="apppwd",
        DB_NAME="projet_db",
    )
    monkeypatch.setattr(db_apply, "load_project_config", lambda: fake)
    monkeypatch.setenv("DB_NAME", "projet_db")  # ADR-060 : DB_NAME lu dans l'env

    cfg = db_apply.load_db_apply_config()

    assert cfg.database == "projet_db"
    for absent in ("host", "port", "login", "password"):
        assert not hasattr(cfg, absent), f"le loader ne doit plus exposer {absent}"


def test_db_apply_et_migrations_passent_par_admin_connection():
    """Garde-fou ADR-033/ADR-060 : le DDL emprunte la connexion d'administration
    (get_admin_connection, qui lit DB_ADMIN_*), jamais get_connection (DB_APP_*)."""
    from cli.entities import db_apply, migrations

    for module in (db_apply, migrations):
        src = Path(module.__file__).read_text(encoding="utf-8")
        assert "get_admin_connection(" in src, (
            f"{module.__name__} doit se connecter via get_admin_connection (DDL en DB_ADMIN_*)"
        )


def test_db_init_default_app_privileges_dml_only():
    """forge_app n'est plus provisionné avec du DDL par défaut (ADR-033)."""
    from cli.entities import db_init

    assert set(db_init.DEFAULT_APP_PRIVILEGES) == {"SELECT", "INSERT", "UPDATE", "DELETE"}
    for ddl in ("CREATE", "ALTER", "DROP", "INDEX", "REFERENCES"):
        assert ddl not in db_init.DEFAULT_APP_PRIVILEGES, (
            f"{ddl} ne doit plus être accordé par défaut à forge_app"
        )


def test_db_init_still_connects_as_admin():
    """db:init reste en connexion d'administration (get_admin_connection lit DB_ADMIN_*)."""
    from cli.entities import db_init

    src = Path(db_init.__file__).read_text(encoding="utf-8")
    assert "get_admin_connection(" in src


@pytest.mark.parametrize("var", ["DB_APP_PRIVILEGES"])
def test_skeleton_env_example_sans_ddl_app(var):
    """Le squelette ne suggère plus d'accorder du DDL à forge_app."""
    assert var not in _SKELETON_ENV.read_text(encoding="utf-8")
