"""DB-LOCK-TIMEOUT-QUALIFY-001 et DB-LOCK-WAIT-BOUND-001, mesure sur serveurs réels.

Deux étages, mesurés l'un après l'autre.

**La qualification** : une première transaction tient un verrou de ligne, une
seconde veut écrire avec une attente bornée posée par l'appelant. La borne est
posée **dans** le bloc `transaction()` : posée par un `db.execute` isolé, elle
mourrait avec la restitution de la connexion, la remise à zéro du pool
PostgreSQL effaçant justement les variables de session.

**La borne par défaut** : même protocole, mais l'appelant ne pose rien. Avant
`DB-LOCK-WAIT-BOUND-001`, PostgreSQL et SQL Server attendaient indéfiniment et
MariaDB 50 secondes : une transaction coincée épuisait les workers un à un.
Les connexions du runtime reçoivent désormais `DB_POOL_TIMEOUT` comme borne, et
le test vérifie la **durée** autant que le verdict : sans la borne, il
resterait suspendu.

Le pendant hors base est `tests/test_db_lock_timeout_qualify_001.py`.
"""
from __future__ import annotations

import time
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


# ── La borne par défaut (DB-LOCK-WAIT-BOUND-001) ─────────────────────────────

def _ecrire_derriere_un_verrou(db: Any, backend: Any, sql_update: str) -> "tuple[BaseException | None, float]":
    """Tient le verrou depuis une connexion du backend, écrit depuis la couche db."""
    teneur: Any = backend.get_connection()
    teneur.autocommit = False
    curseur = teneur.cursor()
    curseur.execute(sql_update)

    erreur: "BaseException | None" = None
    debut = time.perf_counter()
    try:
        db.execute(sql_update)
    except BaseException as capture:  # noqa: BLE001 — c'est le sujet du test
        erreur = capture
    duree = time.perf_counter() - debut
    curseur.close()
    teneur.rollback()
    backend.close_connection(teneur)
    return erreur, duree


def _exiger_borne(erreur: "BaseException | None", duree: float) -> None:
    from core.database.errors import DatabaseUnavailableError

    assert erreur is not None, (
        f"l'écriture est PASSÉE en {duree:.1f}s : la borne n'a pas agi"
    )
    assert isinstance(erreur, DatabaseUnavailableError), (
        f"attendu une indisponibilité, obtenu "
        f"{type(erreur).__module__}.{type(erreur).__name__} : {erreur}"
    )
    assert duree < 8.0, f"borne à 1 s mais {duree:.1f}s d'attente"
    assert duree >= 0.5, "l'attente doit avoir eu lieu avant le refus"


def test_mariadb_l_attente_est_bornee_sans_que_l_appelant_ne_pose_rien(
    real_db: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Avant la borne, le serveur faisait patienter 50 secondes."""
    from core.database import db
    from core.database.backend import get_backend, reset_backend

    monkeypatch.setenv("DB_POOL_TIMEOUT", "1")
    reset_backend()
    try:
        db.execute(f"DROP TABLE IF EXISTS {_TABLE}")
        db.execute(f"CREATE TABLE {_TABLE} (id INT PRIMARY KEY, v INT) ENGINE=InnoDB")
        db.execute(f"INSERT INTO {_TABLE} (id, v) VALUES (1, 0)")

        erreur, duree = _ecrire_derriere_un_verrou(
            db, get_backend(), f"UPDATE {_TABLE} SET v = v + 1 WHERE id = 1")

        _exiger_borne(erreur, duree)
        db.execute(f"DROP TABLE IF EXISTS {_TABLE}")
    finally:
        reset_backend()


@pytest.mark.db_pg
def test_postgres_l_attente_est_bornee_sans_que_l_appelant_ne_pose_rien(
    real_pg_db: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Avant la borne, le serveur attendait indéfiniment (`lock_timeout` à 0)."""
    from core.database import db
    from core.database.backend import get_backend, reset_backend

    monkeypatch.setenv("DB_POOL_TIMEOUT", "1")
    reset_backend()
    try:
        db.execute(f"DROP TABLE IF EXISTS {_TABLE}")
        db.execute(f"CREATE TABLE {_TABLE} (id INT PRIMARY KEY, v INT)")
        db.execute(f"INSERT INTO {_TABLE} (id, v) VALUES (1, 0)")

        erreur, duree = _ecrire_derriere_un_verrou(
            db, get_backend(), f"UPDATE {_TABLE} SET v = v + 1 WHERE id = 1")

        _exiger_borne(erreur, duree)
        db.execute(f"DROP TABLE IF EXISTS {_TABLE}")
    finally:
        reset_backend()


@pytest.mark.db_pg
def test_postgres_la_borne_survit_a_la_remise_a_zero_du_pool(
    real_pg_db: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`RESET ALL` revient à la valeur de session posée par `options`, pas à 0.

    C'est le point délicat du montage : posée par un `SET` ordinaire, la borne
    serait effacée par la remise à zéro entre deux emprunts.
    """
    from core.database import db
    from core.database.backend import reset_backend

    monkeypatch.setenv("DB_POOL_TIMEOUT", "1")
    monkeypatch.setenv("DB_POOL_SIZE", "1")
    reset_backend()
    try:
        # Plusieurs emprunts successifs : chacun passe par la remise à zéro.
        for _ in range(3):
            ligne = db.fetch_one("SHOW lock_timeout")
            assert ligne == {"lock_timeout": "1s"}, f"borne perdue : {ligne}"
    finally:
        reset_backend()


@pytest.mark.db_mssql
def test_mssql_l_attente_est_bornee_sans_que_l_appelant_ne_pose_rien(
    real_mssql_db: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Avant la borne, le serveur attendait indéfiniment (`LOCK_TIMEOUT` à -1)."""
    from core.database import db
    from core.database.backend import get_backend, reset_backend

    monkeypatch.setenv("DB_POOL_TIMEOUT", "1")
    reset_backend()
    try:
        db.execute(f"IF OBJECT_ID('{_TABLE}') IS NOT NULL DROP TABLE {_TABLE}")
        db.execute(f"CREATE TABLE {_TABLE} (id INT PRIMARY KEY, v INT)")
        db.execute(f"INSERT INTO {_TABLE} (id, v) VALUES (1, 0)")

        erreur, duree = _ecrire_derriere_un_verrou(
            db, get_backend(), f"UPDATE {_TABLE} SET v = v + 1 WHERE id = 1")

        _exiger_borne(erreur, duree)
        db.execute(f"IF OBJECT_ID('{_TABLE}') IS NOT NULL DROP TABLE {_TABLE}")
    finally:
        reset_backend()
