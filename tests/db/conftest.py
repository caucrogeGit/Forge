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

_REQUIRE_DB = os.environ.get("FORGE_REQUIRE_DB") == "1"


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
    forge.configure(
        app_name="forge_test",
        db_host=params["host"],
        db_port=params["port"],
        db_user=params["user"],
        db_password=params["password"],
        db_name=params["name"],
        db_pool_size=2,
    )

    try:
        probe = connection.get_connection()  # crée le pool nommé une fois
        connection.close_connection(probe)
    except Exception as error:  # noqa: BLE001 — toute erreur de connexion = base indisponible
        message = f"MariaDB de test injoignable : {error}"
        if _REQUIRE_DB:
            pytest.fail(message + " (FORGE_REQUIRE_DB=1)")
        pytest.skip(message + " (test d'intégration sauté en local)")

    yield

    # ADR-054 : le pool vit dans le backend actif. reset_backend() le ferme
    # proprement (close()) et force une nouvelle résolution ensuite.
    reset_backend()
