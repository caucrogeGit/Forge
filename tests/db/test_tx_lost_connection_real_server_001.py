"""CORE-TX-LOST-CONNECTION-001, mesure sur serveurs réels.

Le défaut ne se voyait qu'en tuant réellement la session pendant le bloc : le
rollback du chemin d'erreur échouait alors à son tour et sortait à la place de
la cause. Les trois backends serveur rendaient chacun l'exception de leur
pilote, c'est-à-dire exactement ce que l'ADR-054 promet de ne jamais laisser
atteindre l'application.

Le protocole reprend celui de `test_connection_lost_real_server_001.py` :
ouvrir le bloc, relever l'identifiant de session, la tuer depuis une seconde
connexion, puis rejouer une requête dans le même bloc.

Le pendant hors base est `tests/test_core_tx_lost_connection_001.py`.
"""
from __future__ import annotations

import time
from typing import Any

import pytest

pytestmark = pytest.mark.db


def _exiger_erreur_portable(erreur: "BaseException | None") -> None:
    """Le contrat : ce qui sort du bloc appartient au cœur, pas au pilote."""
    from core.database.errors import DatabaseUnavailableError

    assert erreur is not None, "la session tuée devrait faire échouer le bloc"
    assert isinstance(erreur, DatabaseUnavailableError), (
        "le bloc a laissé sortir "
        f"{type(erreur).__module__}.{type(erreur).__name__} : {erreur}"
    )


# ── MariaDB ──────────────────────────────────────────────────────────────────

def test_mariadb_une_coupure_dans_un_bloc_reste_qualifiee(real_db: None) -> None:
    from core.database import db
    from core.database.backend import get_backend
    from core.database.transaction import transaction

    backend = get_backend()
    erreur: "BaseException | None" = None
    try:
        with transaction() as tx:
            identifiant = db.fetch_one("SELECT CONNECTION_ID() AS cid", tx=tx)
            assert identifiant is not None

            bourreau = backend.get_connection()
            tueur = bourreau.cursor()
            tueur.execute(f"KILL {int(identifiant['cid'])}")
            tueur.close()
            backend.close_connection(bourreau)

            db.fetch_one("SELECT 1 AS v", tx=tx)
    except BaseException as capture:  # noqa: BLE001 — c'est le sujet du test
        erreur = capture

    _exiger_erreur_portable(erreur)


def test_mariadb_le_pool_reste_utilisable_apres(real_db: None) -> None:
    """La connexion doit avoir été rendue : sinon le pool perd une place.

    Le pool des tests est à deux connexions. Trois emprunts successifs après la
    coupure ne passent que si la connexion du bloc est bien repartie.
    """
    from core.database import db

    time.sleep(1.0)

    for _ in range(3):
        assert db.fetch_one("SELECT 1 AS v") == {"v": 1}


# ── PostgreSQL ───────────────────────────────────────────────────────────────

def test_postgres_une_coupure_dans_un_bloc_reste_qualifiee(real_pg_db: None) -> None:
    from core.database import db
    from core.database.backend import get_backend
    from core.database.transaction import transaction

    backend = get_backend()
    erreur: "BaseException | None" = None
    try:
        with transaction() as tx:
            ligne = db.fetch_one("SELECT pg_backend_pid() AS pid", tx=tx)
            assert ligne is not None

            bourreau = backend.get_connection()
            tueur = bourreau.cursor()
            # Marqueur Forge `?` et non `%s` : le curseur du backend traduit.
            tueur.execute("SELECT pg_terminate_backend(?)", (int(ligne["pid"]),))
            bourreau.commit()
            tueur.close()
            backend.close_connection(bourreau)

            db.fetch_one("SELECT 1 AS v", tx=tx)
    except BaseException as capture:  # noqa: BLE001 — c'est le sujet du test
        erreur = capture

    _exiger_erreur_portable(erreur)


def test_postgres_la_connexion_suivante_passe(real_pg_db: None) -> None:
    from core.database import db

    assert db.fetch_one("SELECT 1 AS v") == {"v": 1}


# ── SQL Server ───────────────────────────────────────────────────────────────

def test_mssql_une_coupure_dans_un_bloc_reste_qualifiee(real_mssql_db: None) -> None:
    from core.database import db
    from core.database.backend import get_backend
    from core.database.transaction import transaction

    backend = get_backend()
    erreur: "BaseException | None" = None
    try:
        with transaction() as tx:
            ligne = db.fetch_one("SELECT @@SPID AS spid", tx=tx)
            assert ligne is not None

            bourreau: Any = backend.get_connection()
            bourreau.autocommit = True
            tueur = bourreau.cursor()
            tueur.execute(f"KILL {int(ligne['spid'])}")
            tueur.close()
            backend.close_connection(bourreau)

            db.fetch_one("SELECT 1 AS v", tx=tx)
    except BaseException as capture:  # noqa: BLE001 — c'est le sujet du test
        erreur = capture

    _exiger_erreur_portable(erreur)


def test_mssql_la_connexion_suivante_passe(real_mssql_db: None) -> None:
    from core.database import db

    assert db.fetch_one("SELECT 1 AS v") == {"v": 1}
