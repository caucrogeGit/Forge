"""Tests — ENTITIES-DBINIT-CHARSET-ALLOWLIST-001 : allowlist DB_CHARSET/DB_COLLATION.

`db:init` interpole DB_CHARSET et DB_COLLATION dans le SQL de provisioning
(généré ADR-067 et exécuté --run). DB_NAME et DB_APP_PRIVILEGES étaient déjà
validés ; charset et collation ne l'étaient pas. Garde-fous :
  1. une valeur hors `[A-Za-z0-9_]{1,64}` est refusée par les DEUX chargeurs
     (`load_db_init_config` et `load_provisioning_env`) avec un message clair ;
  2. les valeurs légitimes (défauts MariaDB) passent ;
  3. le SQL généré ne peut donc plus véhiculer d'injection via ces variables.
"""
from __future__ import annotations

import pytest

import forge_mvc_entities.db_init as db_init
from forge_mvc_entities.db_init import (
    DbInitError,
    _validate_charset_token,
    generate_provisioning_sql,
    load_db_init_config,
    load_provisioning_env,
)


_BASE_ENV = {
    "DB_NAME": "demo",
    "DB_ADMIN_LOGIN": "demo_admin",
    "DB_ADMIN_PWD": "x",
    "DB_APP_LOGIN": "demo",
    "DB_APP_PWD": "x",
}


def _set_env(monkeypatch, **extra):
    # Même isolement que tests/test_db_init_provisioning_sql_001.py : les
    # chargeurs lisent os.environ, pas besoin d'un vrai projet (config.py).
    monkeypatch.setattr(db_init, "load_project_config", lambda: None)
    for key, value in {**_BASE_ENV, **extra}.items():
        monkeypatch.setenv(key, value)


INJECTIONS = [
    "utf8mb4; DROP DATABASE demo; --",
    "utf8mb4 COLLATE x",
    "utf8mb4'",
    "",
    "a" * 65,
]


class TestValidator:
    @pytest.mark.parametrize("value", INJECTIONS)
    def test_valeurs_hostiles_refusees(self, value):
        with pytest.raises(DbInitError):
            _validate_charset_token(value, "DB_CHARSET")

    @pytest.mark.parametrize("value", ["utf8mb4", "utf8mb4_unicode_ci", "latin1", "Binary"])
    def test_valeurs_legitimes_acceptees(self, value):
        _validate_charset_token(value, "DB_CHARSET")


class TestLoaders:
    @pytest.mark.parametrize("var", ["DB_CHARSET", "DB_COLLATION"])
    def test_load_db_init_config_refuse(self, monkeypatch, var):
        _set_env(monkeypatch, **{var: "utf8mb4; DROP DATABASE demo; --"})
        with pytest.raises(DbInitError, match=var):
            load_db_init_config()

    @pytest.mark.parametrize("var", ["DB_CHARSET", "DB_COLLATION"])
    def test_load_provisioning_env_refuse(self, monkeypatch, var):
        _set_env(monkeypatch, **{var: "x' COLLATE y"})
        with pytest.raises(DbInitError, match=var):
            load_provisioning_env()

    def test_defauts_acceptes_et_sql_genere_sain(self, monkeypatch):
        _set_env(monkeypatch)
        monkeypatch.delenv("DB_CHARSET", raising=False)
        monkeypatch.delenv("DB_COLLATION", raising=False)
        env = load_provisioning_env()
        sql = generate_provisioning_sql(env)
        assert "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci" in sql
