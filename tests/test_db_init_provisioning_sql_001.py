"""DB-INIT-PROVISIONING-SQL-001 (ADR-067) — db:init génère le SQL par défaut.

`forge db:init` (défaut) affiche le script SQL de provisioning dérivé de env/,
sans se connecter ; `--run` exécute. Vérification préalable dans les deux modes :
variables requises renseignées et DB_NAME valide.
"""
from __future__ import annotations

import types

import pytest

from forge_mvc_entities import db_init
from forge_mvc_entities.db_init import (
    DEFAULT_APP_PRIVILEGES,
    DbInitError,
    ProvisioningEnv,
    _check_required_env,
    _validate_db_name,
    generate_provisioning_sql,
)


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


# ── Génération du script SQL ─────────────────────────────────────────────────

def test_sql_cree_la_base_en_premier():
    sql = generate_provisioning_sql(_cfg())
    assert "CREATE DATABASE IF NOT EXISTS `ventes`" in sql
    assert "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci" in sql


def test_sql_inclut_le_registre_forge_migrations():
    # FORGE-2 : la table forge_migrations doit figurer dans le SQL affiché
    # (elle ne requiert que CREATE sur la base), sinon migration:* échoue.
    sql = generate_provisioning_sql(_cfg())
    assert "USE `ventes`;" in sql
    assert "CREATE TABLE IF NOT EXISTS forge_migrations" in sql


def test_sql_deux_comptes_scelles_a_la_base():
    sql = generate_provisioning_sql(_cfg())
    # Admin : tous droits, mais SUR LA BASE seulement (jamais *.*).
    assert "CREATE OR REPLACE USER 'admin'@'localhost' IDENTIFIED BY 'adminpwd'" in sql
    assert "GRANT ALL PRIVILEGES ON `ventes`.* TO 'admin'@'localhost'" in sql
    assert "*.*" not in sql
    # Applicatif : DML uniquement.
    assert "CREATE OR REPLACE USER 'app'@'localhost' IDENTIFIED BY 'apppwd'" in sql
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON `ventes`.* TO 'app'@'localhost'" in sql
    assert sql.rstrip().endswith("FLUSH PRIVILEGES;")


def test_sql_hote_du_grant_suit_db_host():
    sql = generate_provisioning_sql(_cfg(host="10.0.0.5"))
    assert "@'10.0.0.5'" in sql
    assert "@'localhost'" not in sql


# ── Validation du nom de base ────────────────────────────────────────────────

@pytest.mark.parametrize("bad", ["", "a" * 65, " x", "x ", "a/b", "a.b", "a\\b", "a\tb"])
def test_db_name_invalide_rejete(bad: str):
    with pytest.raises(DbInitError):
        _validate_db_name(bad)


@pytest.mark.parametrize("good", ["ventes", "mon-projet", "ReferenCiel_Manager", "db1"])
def test_db_name_valide_accepte(good: str):
    _validate_db_name(good)  # ne lève pas


# ── Vérification préalable des variables ─────────────────────────────────────

def _set_env(monkeypatch, **values: str) -> None:
    monkeypatch.setattr(db_init, "load_project_config", lambda: None)
    for key in ("DB_NAME", "DB_ADMIN_LOGIN", "DB_ADMIN_PWD", "DB_APP_LOGIN", "DB_APP_PWD"):
        monkeypatch.delenv(key, raising=False)
    for key, val in values.items():
        monkeypatch.setenv(key, val)


def test_check_env_ok_si_tout_renseigne(monkeypatch):
    _set_env(
        monkeypatch,
        DB_NAME="ventes", DB_ADMIN_LOGIN="admin", DB_ADMIN_PWD="p",
        DB_APP_LOGIN="app", DB_APP_PWD="p",
    )
    _check_required_env()  # ne lève pas


def test_check_env_liste_les_cles_manquantes(monkeypatch):
    _set_env(monkeypatch, DB_NAME="ventes", DB_ADMIN_LOGIN="admin")
    with pytest.raises(DbInitError) as exc:
        _check_required_env()
    message = str(exc.value)
    assert "DB_ADMIN_PWD" in message and "DB_APP_LOGIN" in message and "DB_APP_PWD" in message
    assert "forge db:config" in message


def test_check_env_valeur_vide_compte_comme_manquante(monkeypatch):
    _set_env(
        monkeypatch,
        DB_NAME="ventes", DB_ADMIN_LOGIN="admin", DB_ADMIN_PWD="p",
        DB_APP_LOGIN="app", DB_APP_PWD="   ",
    )
    with pytest.raises(DbInitError, match="DB_APP_PWD"):
        _check_required_env()


def test_check_env_refuse_db_name_invalide(monkeypatch):
    _set_env(
        monkeypatch,
        DB_NAME="a/b", DB_ADMIN_LOGIN="admin", DB_ADMIN_PWD="p",
        DB_APP_LOGIN="app", DB_APP_PWD="p",
    )
    with pytest.raises(DbInitError, match="Nom de base invalide"):
        _check_required_env()


# ── Dispatch : défaut = génère, --run = exécute ──────────────────────────────

def _fake_mariadb_backend():
    return types.SimpleNamespace(name="mariadb", requires_provisioning=True)


def test_defaut_genere_le_sql_sans_executer(monkeypatch, capsys):
    import core.database.backend as backend_mod

    monkeypatch.setattr(backend_mod, "get_backend", _fake_mariadb_backend)
    monkeypatch.setattr(db_init, "_check_required_env", lambda: None)
    monkeypatch.setattr(db_init, "load_provisioning_env", _cfg)
    called = {"executed": False}
    monkeypatch.setattr(db_init, "init_project_database", lambda: called.__setitem__("executed", True) or [])

    db_init._dispatch_db_init(run=False)

    out = capsys.readouterr().out
    assert "CREATE DATABASE IF NOT EXISTS `ventes`" in out
    assert "FLUSH PRIVILEGES;" in out
    assert called["executed"] is False, "le mode par défaut ne doit RIEN exécuter"


def test_run_execute_le_provisioning(monkeypatch, capsys):
    import core.database.backend as backend_mod

    monkeypatch.setattr(backend_mod, "get_backend", _fake_mariadb_backend)
    monkeypatch.setattr(db_init, "_check_required_env", lambda: None)
    monkeypatch.setattr(db_init, "init_project_database", lambda: ["Base ventes créée."])

    db_init._dispatch_db_init(run=True)

    out = capsys.readouterr().out
    assert "[OK]" in out and "Base ventes créée." in out
    assert "CREATE DATABASE" not in out, "le mode --run exécute, il n'affiche pas le SQL"


def test_run_via_main(monkeypatch, capsys):
    import core.database.backend as backend_mod

    monkeypatch.setattr(backend_mod, "get_backend", _fake_mariadb_backend)
    monkeypatch.setattr(db_init, "_check_required_env", lambda: None)
    monkeypatch.setattr(db_init, "load_provisioning_env", _cfg)

    db_init.main(["db:init"])  # défaut
    assert "CREATE DATABASE" in capsys.readouterr().out
