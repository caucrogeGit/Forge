"""Fixtures des tests d'intégration DB (marqueur `db`), ticket TEST-DB-INTEGRATION-CI-001.

Ces tests exercent la VRAIE couche d'accès `core.database.db` contre un serveur
MariaDB réel, là où le reste de la suite mocke la base.

Comportement en l'absence de base :
- en local (par défaut) : les tests sont SAUTÉS proprement ;
- en CI : `FORGE_REQUIRE_DB=1` impose la présence de la base, donc l'absence de
  connexion fait ÉCHOUER le test (la couche DB n'est jamais « verte par défaut »).

Paramètres de connexion lus depuis l'environnement (FORGE_TEST_DB_*), avec des
valeurs par défaut adaptées au service MariaDB de la CI.
"""
from __future__ import annotations

import os

import pytest

from forge_mvc_testing.db_probe import connection_failure_message

_REQUIRE_DB = os.environ.get("FORGE_REQUIRE_DB") == "1"
_REQUIRE_DB_PG = os.environ.get("FORGE_REQUIRE_DB_PG") == "1"
_REQUIRE_DB_MSSQL = os.environ.get("FORGE_REQUIRE_DB_MSSQL") == "1"


def _db_params() -> dict[str, object]:
    return {
        "host": os.environ.get("FORGE_TEST_DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("FORGE_TEST_DB_PORT", "3306")),
        "user": os.environ.get("FORGE_TEST_DB_USER", "root"),
        "password": os.environ.get("FORGE_TEST_DB_PASSWORD", ""),
        "name": os.environ.get("FORGE_TEST_DB_NAME", "forge_test"),
    }


@pytest.fixture(scope="session")
def real_db():
    """Configure Forge sur la MariaDB de test et crée le pool UNE seule fois.

    Le connecteur mariadb tient un registre de pools nommés : recréer un pool de
    même nom lève « Pool already exists ». La fixture est donc à portée session :
    le pool est créé au premier test `db`, réutilisé par les suivants, puis fermé
    proprement en fin de session.
    """
    import core.forge as forge
    from core.database import connection
    from core.database.backend import reset_backend

    params = _db_params()
    # ADR-060 : le backend lit la config de connexion runtime dans l'environnement.
    #
    # Ces clés doivent être RESTAURÉES en fin de session. `monkeypatch` est à
    # portée fonction et ne convient pas ici (la fixture est à portée session
    # pour le pool nommé), d'où la sauvegarde manuelle. Sans elle, `DB_APP_LOGIN`
    # restait à `root` pour tous les tests suivants du même processus : le
    # contrôle de sécurité prod y voyait à juste titre l'application tournant
    # sous le compte d'administration, et échouait. Le défaut ne se voyait ni en
    # CI, qui sépare les jobs `db` et `not db`, ni en local sans base ; mais
    # `tools/release-validate.sh` lance la suite ENTIÈRE, donc le garde de
    # release pouvait échouer pour une raison étrangère à la release.
    overrides = {
        "DB_HOST": str(params["host"]),
        "DB_PORT": str(params["port"]),
        "DB_APP_LOGIN": str(params["user"]),
        "DB_APP_PWD": str(params["password"]),
        "DB_NAME": str(params["name"]),
        "DB_POOL_SIZE": "2",
    }
    previous = {key: os.environ.get(key) for key in overrides}
    os.environ.update(overrides)
    forge.configure(app_name="forge_test")

    def _restore() -> None:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    try:
        probe = connection.get_connection()  # crée le pool nommé une fois
        connection.close_connection(probe)
    except Exception as error:  # noqa: BLE001 — la cause est classée, pas supposée
        _restore()
        message = connection_failure_message("MariaDB", error, env_prefix="FORGE_TEST_DB")
        if _REQUIRE_DB:
            pytest.fail(message + " (FORGE_REQUIRE_DB=1)")
        pytest.skip(message + " (test d'intégration sauté en local)")

    try:
        yield
    finally:
        # ADR-054 : le pool vit dans le backend actif. reset_backend() le ferme
        # proprement (close()) et force une nouvelle résolution ensuite.
        reset_backend()
        _restore()


@pytest.fixture()
def real_pg_db(monkeypatch: pytest.MonkeyPatch):
    """Configure Forge sur le PostgreSQL de test (backend actif : postgres).

    Portée fonction : psycopg n'utilise pas de pool nommé, et la fixture doit
    rendre le backend de la session (reset_backend + env restauré par
    monkeypatch) en sortant. Paramètres lus dans FORGE_TEST_PG_*, avec des
    valeurs par défaut adaptées au service PostgreSQL de la CI.
    """
    pytest.importorskip("psycopg", reason="psycopg (backend forge-mvc-postgres) absent")
    import core.forge as forge
    from core.database import connection
    from core.database.backend import reset_backend

    monkeypatch.setenv("DB_BACKEND", "postgres")
    monkeypatch.setenv("DB_HOST", os.environ.get("FORGE_TEST_PG_HOST", "127.0.0.1"))
    monkeypatch.setenv("DB_PORT", os.environ.get("FORGE_TEST_PG_PORT", "5432"))
    monkeypatch.setenv("DB_APP_LOGIN", os.environ.get("FORGE_TEST_PG_USER", "postgres"))
    monkeypatch.setenv("DB_APP_PWD", os.environ.get("FORGE_TEST_PG_PASSWORD", "forge_test_pg"))
    monkeypatch.setenv("DB_NAME", os.environ.get("FORGE_TEST_PG_NAME", "forge_test"))
    forge.configure(app_name="forge_test")
    reset_backend()
    try:
        probe = connection.get_connection()
        connection.close_connection(probe)
    except Exception as error:  # noqa: BLE001 — la cause est classée, pas supposée
        reset_backend()
        message = connection_failure_message("PostgreSQL", error, env_prefix="FORGE_TEST_PG")
        if _REQUIRE_DB_PG:
            pytest.fail(message + " (FORGE_REQUIRE_DB_PG=1)")
        pytest.skip(message + " (test d'intégration sauté en local)")

    yield

    reset_backend()


@pytest.fixture()
def real_mssql_db(monkeypatch: pytest.MonkeyPatch):
    """Configure Forge sur le SQL Server de test (backend actif : mssql).

    Le conteneur SQL Server ne crée aucune base au démarrage : la fixture crée
    la base de test au besoin via la connexion d'administration (master), hors
    transaction. Paramètres lus dans FORGE_TEST_MSSQL_*, avec des valeurs par
    défaut adaptées au service SQL Server de la CI.
    """
    pytest.importorskip("pyodbc", reason="pyodbc (backend forge-mvc-mssql) absent")
    import core.forge as forge
    from core.database import connection
    from core.database.backend import get_backend, reset_backend

    user = os.environ.get("FORGE_TEST_MSSQL_USER", "sa")
    password = os.environ.get("FORGE_TEST_MSSQL_PASSWORD", "Forge#Test#2026")
    db_name = os.environ.get("FORGE_TEST_MSSQL_NAME", "forge_test")
    monkeypatch.setenv("DB_BACKEND", "mssql")
    monkeypatch.setenv("DB_HOST", os.environ.get("FORGE_TEST_MSSQL_HOST", "127.0.0.1"))
    monkeypatch.setenv("DB_PORT", os.environ.get("FORGE_TEST_MSSQL_PORT", "1433"))
    monkeypatch.setenv("DB_APP_LOGIN", user)
    monkeypatch.setenv("DB_APP_PWD", password)
    monkeypatch.setenv("DB_ADMIN_LOGIN", user)
    monkeypatch.setenv("DB_ADMIN_PWD", password)
    monkeypatch.setenv("DB_NAME", db_name)
    forge.configure(app_name="forge_test")
    reset_backend()
    try:
        backend = get_backend()
        admin = backend.get_admin_connection()  # base de maintenance master
        try:
            admin.autocommit = True
            cursor = admin.cursor()
            # db_name vient de l'environnement de test, jamais d'une entrée
            # utilisateur (CREATE DATABASE n'accepte pas de paramètre lié).
            cursor.execute(f"IF DB_ID(N'{db_name}') IS NULL CREATE DATABASE [{db_name}]")
            cursor.close()
        finally:
            backend.close_connection(admin)
        probe = connection.get_connection()
        connection.close_connection(probe)
    except Exception as error:  # noqa: BLE001 — la cause est classée, pas supposée
        reset_backend()
        message = connection_failure_message("SQL Server", error, env_prefix="FORGE_TEST_MSSQL")
        if _REQUIRE_DB_MSSQL:
            pytest.fail(message + " (FORGE_REQUIRE_DB_MSSQL=1)")
        pytest.skip(message + " (test d'intégration sauté en local)")

    yield

    reset_backend()
