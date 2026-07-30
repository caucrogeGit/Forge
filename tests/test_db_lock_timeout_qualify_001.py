"""DB-LOCK-TIMEOUT-QUALIFY-001 : un dépassement d'attente de verrou bornée rend 503.

`MARIADB-LOCK-WAIT-503-001` a admis l'errno 1205 dans la famille des
indisponibilités, au critère « attendre suffit ». PostgreSQL et SQL Server ont
le même dépassement, mais seulement quand l'exploitant borne l'attente, les
deux serveurs attendant indéfiniment par défaut (`lock_timeout` à 0,
`LOCK_TIMEOUT` à -1, mesurés). Signaux mesurés en tenant le verrou depuis une
seconde transaction, la borne posée :

    PostgreSQL   LockNotAvailable     SQLSTATE 55P03
    SQL Server   ProgrammingError     SQLSTATE 42000, « (1222) » dans le message

Le SQLSTATE de SQL Server ne peut pas servir seul : `42000` est la classe des
erreurs de syntaxe. On exige donc le numéro natif dans le message, comme
`is_unique_violation` avec 2627.

Les interblocages restent dehors, sur les trois serveurs : `40P01` PostgreSQL,
victime 1205 SQL Server, errno 1213 MariaDB. Attendre n'y change rien.

Le pendant sur serveurs réels est `tests/db/test_lock_timeout_real_server_001.py`.
"""
from __future__ import annotations

from typing import Any

import pytest


class _ErreurPilote(Exception):
    def __init__(self, message: str = "", **attributs: Any) -> None:
        super().__init__(message)
        for cle, valeur in attributs.items():
            setattr(self, cle, valeur)


# ── PostgreSQL ───────────────────────────────────────────────────────────────

def test_postgres_le_depassement_de_verrou_est_une_indisponibilite() -> None:
    backend = pytest.importorskip("forge_mvc_postgres.backend").PostgreSQLBackend()

    assert backend.is_unavailable(_ErreurPilote(sqlstate="55P03")) is True


def test_postgres_l_interblocage_reste_dehors() -> None:
    """`40P01` (`deadlock_detected`) : le remède est de revoir l'ordre des verrous."""
    backend = pytest.importorskip("forge_mvc_postgres.backend").PostgreSQLBackend()

    assert backend.is_unavailable(_ErreurPilote(sqlstate="40P01")) is False


# ── SQL Server ───────────────────────────────────────────────────────────────

def test_mssql_le_depassement_de_verrou_est_une_indisponibilite() -> None:
    backend = pytest.importorskip("forge_mvc_mssql.backend").MSSQLBackend()
    erreur = _ErreurPilote()
    erreur.args = ("42000", "[42000] [Microsoft][ODBC Driver 18 for SQL Server]"
                            "[SQL Server]Lock request time out period exceeded."
                            " (1222) (SQLExecDirectW)")

    assert backend.is_unavailable(erreur) is True


def test_mssql_la_classe_42000_seule_ne_suffit_pas() -> None:
    """`42000` porte aussi les vraies erreurs de syntaxe : elles font un 500."""
    backend = pytest.importorskip("forge_mvc_mssql.backend").MSSQLBackend()
    erreur = _ErreurPilote()
    erreur.args = ("42000", "[42000] Incorrect syntax near 'SELCT'. (102)")

    assert backend.is_unavailable(erreur) is False


def test_mssql_le_numero_natif_sans_sa_classe_ne_suffit_pas_non_plus() -> None:
    """Un « (1222) » égaré dans un autre message ne doit pas qualifier."""
    backend = pytest.importorskip("forge_mvc_mssql.backend").MSSQLBackend()
    erreur = _ErreurPilote()
    erreur.args = ("23000", "Violation of UNIQUE KEY. The duplicate key value "
                            "is (1222). (2627)")

    assert backend.is_unavailable(erreur) is False


def test_mssql_l_interblocage_reste_dehors() -> None:
    """La victime d'interblocage reçoit l'erreur native 1205, SQLSTATE 40001."""
    backend = pytest.importorskip("forge_mvc_mssql.backend").MSSQLBackend()
    erreur = _ErreurPilote()
    erreur.args = ("40001", "[40001] Transaction (Process ID 52) was deadlocked "
                            "on lock resources and has been chosen as the "
                            "deadlock victim. Rerun the transaction. (1205)")

    assert backend.is_unavailable(erreur) is False
