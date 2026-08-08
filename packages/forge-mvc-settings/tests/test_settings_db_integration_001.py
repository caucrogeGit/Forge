"""Intégration MariaDB du store de paramètres (SETTINGS-DB-INTEGRATION-001).

Vérifie le contrat SQL réel face au moteur : `CREATE_TABLE_SQL`, l'upsert
`ON DUPLICATE KEY UPDATE` et la lecture/suppression, là où les tests unitaires
utilisent un adapter en mémoire. Marqué `db` : sauté en local sans base, requis
en CI (`FORGE_REQUIRE_DB=1`). Connexion auto-suffisante via `FORGE_TEST_DB_*`.
Toute connexion est fermée (sinon un verrou de métadonnées bloquerait le DROP).
"""
from __future__ import annotations

import os
import uuid
from typing import Any

import pytest

pytestmark = pytest.mark.db

forge_mvc_settings = pytest.importorskip("forge_mvc_settings")

from forge_mvc_settings import (
    delete_setting,
    get_all_settings,
    get_setting,
    set_setting,
)

from forge_mvc_testing.db_probe import connection_failure_message

_REQUIRE_DB = os.environ.get("FORGE_REQUIRE_DB") == "1"


def _rendered_ddl() -> str:
    """DDL de la table, rendu pour le backend actif.

    La constante de schéma du module est supprimée
    (`OPTIN-DDL-CONSTANTS-001`) : deux façons officielles de créer la même
    table contredisaient le principe 11. La source unique est la déclaration
    `forge_mvc_settings.tables`, rendue par le dialecte.
    """
    from core.database.backend import get_backend
    from core.database.table_ddl import render_create_table
    from forge_mvc_settings.tables import APP_SETTINGS

    return chr(10).join(render_create_table(APP_SETTINGS, get_backend().dialect))

def _params() -> dict[str, Any]:
    return {
        "host": os.environ.get("FORGE_TEST_DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("FORGE_TEST_DB_PORT", "3306")),
        "user": os.environ.get("FORGE_TEST_DB_USER", "root"),
        "password": os.environ.get("FORGE_TEST_DB_PASSWORD", ""),
    }


class _ConnAdapter:
    """Expose fetch_one/fetch_all/execute sur une connexion mariadb (dict rows)."""

    def __init__(self, conn: Any, database: str) -> None:
        self._conn = conn
        self._database = database

    def execute(self, sql: str, params: Any = ()) -> int:
        cur = self._conn.cursor()
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        self._conn.commit()
        rc = cur.rowcount
        cur.close()
        return rc

    def fetch_one(self, sql: str, params: Any = ()) -> dict[str, Any] | None:
        cur = self._conn.cursor(dictionary=True)
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        row = cur.fetchone()
        cur.close()
        return row

    def fetch_all(self, sql: str, params: Any = ()) -> list[dict[str, Any]]:
        cur = self._conn.cursor(dictionary=True)
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        cur.close()
        return rows


@pytest.fixture
def settings_db() -> Any:
    try:
        import mariadb
    except ImportError:  # pragma: no cover
        pytest.skip("paquet python 'mariadb' non installé")

    params = _params()
    db_name = f"forge_it_settings_{uuid.uuid4().hex[:10]}"
    try:
        admin = mariadb.connect(**params)
    except Exception as error:  # noqa: BLE001
        message = connection_failure_message(
            "MariaDB", error, env_prefix="FORGE_TEST_DB"
        )
        if _REQUIRE_DB:
            pytest.fail(message + " (FORGE_REQUIRE_DB=1)")
        pytest.skip(message + " (test d'intégration sauté en local)")

    cur = admin.cursor()
    cur.execute(f"CREATE DATABASE `{db_name}`")
    cur.execute(f"USE `{db_name}`")
    cur.execute(_rendered_ddl())
    admin.commit()
    cur.close()
    try:
        yield _ConnAdapter(admin, db_name)
    finally:
        cur = admin.cursor()
        cur.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
        admin.commit()
        cur.close()
        admin.close()


def test_create_table_sql_is_valid_mariadb(settings_db: _ConnAdapter) -> None:
    # La table a été créée par la fixture via _rendered_ddl() ; un set/get prouve
    # que le DDL est accepté par le moteur.
    set_setting("etablissement.nom", "Collège X", db=settings_db)
    assert get_setting("etablissement.nom", db=settings_db) == "Collège X"


def test_real_upsert_and_types(settings_db: _ConnAdapter) -> None:
    set_setting("qcm.duree", 30, db=settings_db)
    set_setting("qcm.duree", 45, db=settings_db)  # ON DUPLICATE KEY UPDATE
    set_setting("maintenance", True, db=settings_db)
    assert get_setting("qcm.duree", db=settings_db) == 45
    assert get_setting("maintenance", db=settings_db) is True
    assert get_all_settings(db=settings_db) == {"maintenance": True, "qcm.duree": 45}


def test_real_delete(settings_db: _ConnAdapter) -> None:
    set_setting("temp", "x", db=settings_db)
    assert delete_setting("temp", db=settings_db) is True
    assert get_setting("temp", db=settings_db) is None
