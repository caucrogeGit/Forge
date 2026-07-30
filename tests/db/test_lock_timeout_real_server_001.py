"""DB-LOCK-TIMEOUT-QUALIFY-001, mesure sur serveurs réels.

Le protocole reprend celui de `test_mariadb_lock_wait_real_server_001.py` : une
première transaction tient un verrou de ligne, une seconde veut écrire avec une
attente bornée. La borne est posée **dans** le bloc `transaction()` : posée par
un `db.execute` isolé, elle mourrait avec la restitution de la connexion, la
remise à zéro du pool PostgreSQL effaçant justement les variables de session.

Le pendant hors base est `tests/test_db_lock_timeout_qualify_001.py`.
"""
from __future__ import annotations

from typing import Any

import pytest

pytestmark = pytest.mark.db

_TABLE = "forge_lock_timeout_probe"


@pytest.mark.db_pg
def test_postgres_le_depassement_devient_une_indisponibilite(real_pg_db: None) -> None:
    from core.database import db
    from core.database.backend import get_backend
    from core.database.errors import DatabaseUnavailableError
    from core.database.transaction import transaction

    backend = get_backend()
    db.execute(f"DROP TABLE IF EXISTS {_TABLE}")
    db.execute(f"CREATE TABLE {_TABLE} (id INT PRIMARY KEY, v INT)")
    db.execute(f"INSERT INTO {_TABLE} (id, v) VALUES (1, 0)")

    teneur: Any = backend.get_connection()
    teneur.autocommit = False
    curseur = teneur.cursor()
    curseur.execute(f"UPDATE {_TABLE} SET v = 1 WHERE id = 1")

    erreur: "BaseException | None" = None
    try:
        with transaction() as tx:
            db.execute("SET lock_timeout = 500", tx=tx)
            db.execute(f"UPDATE {_TABLE} SET v = 2 WHERE id = 1", tx=tx)
    except BaseException as capture:  # noqa: BLE001 — c'est le sujet du test
        erreur = capture
    finally:
        curseur.close()
        teneur.rollback()
        backend.close_connection(teneur)
        db.execute(f"DROP TABLE IF EXISTS {_TABLE}")

    assert erreur is not None, "le verrou tenu devrait faire échouer l'écriture"
    assert isinstance(erreur, DatabaseUnavailableError), (
        f"attendu une indisponibilité, obtenu "
        f"{type(erreur).__module__}.{type(erreur).__name__} : {erreur}"
    )


@pytest.mark.db_mssql
def test_mssql_le_depassement_devient_une_indisponibilite(real_mssql_db: None) -> None:
    from core.database import db
    from core.database.backend import get_backend
    from core.database.errors import DatabaseUnavailableError
    from core.database.transaction import transaction

    backend = get_backend()
    db.execute(f"IF OBJECT_ID('{_TABLE}') IS NOT NULL DROP TABLE {_TABLE}")
    db.execute(f"CREATE TABLE {_TABLE} (id INT PRIMARY KEY, v INT)")
    db.execute(f"INSERT INTO {_TABLE} (id, v) VALUES (1, 0)")

    teneur: Any = backend.get_connection()
    teneur.autocommit = False
    curseur = teneur.cursor()
    curseur.execute(f"UPDATE {_TABLE} SET v = 1 WHERE id = 1")

    erreur: "BaseException | None" = None
    try:
        with transaction() as tx:
            db.execute("SET LOCK_TIMEOUT 500", tx=tx)
            db.execute(f"UPDATE {_TABLE} SET v = 2 WHERE id = 1", tx=tx)
    except BaseException as capture:  # noqa: BLE001 — c'est le sujet du test
        erreur = capture
    finally:
        curseur.close()
        teneur.rollback()
        backend.close_connection(teneur)
        db.execute(f"IF OBJECT_ID('{_TABLE}') IS NOT NULL DROP TABLE {_TABLE}")

    assert erreur is not None, "le verrou tenu devrait faire échouer l'écriture"
    assert isinstance(erreur, DatabaseUnavailableError), (
        f"attendu une indisponibilité, obtenu "
        f"{type(erreur).__module__}.{type(erreur).__name__} : {erreur}"
    )
