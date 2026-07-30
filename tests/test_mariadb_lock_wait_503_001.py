"""MARIADB-LOCK-WAIT-503-001 : l'attente de verrou entre dans la famille, l'interblocage non.

`DB-UNAVAILABLE-FAMILY-001` a fait du contrat une question de famille, dont le
critère est « attendre suffit ». MariaDB a deux errno voisins, mesurés sur
serveur réel, qui ne répondent pas pareil à ce critère :

    1205  HY000  « Lock wait timeout exceeded »   attendre suffit
    1213  40001  « Deadlock found »               attendre n'y change rien

L'attente de verrou est de la contention pure, jumelle du verrou de fichier
SQLite et de la saturation du pool. L'interblocage, lui, dit que deux
transactions ont pris leurs verrous dans des ordres incompatibles : InnoDB en a
annulé une, et le remède est de revoir cet ordre. Le 500 le laisse visible dans
les journaux d'erreur, là où un 503 le rangerait parmi les conditions de
routine et rendrait un défaut d'ordonnancement récurrent invisible.

Le pendant sur serveur réel est
`tests/db/test_mariadb_lock_wait_real_server_001.py`.
"""
from __future__ import annotations

from typing import Any

import pytest


class _ErreurPilote(Exception):
    def __init__(self, message: str = "", **attributs: Any) -> None:
        super().__init__(message)
        for cle, valeur in attributs.items():
            setattr(self, cle, valeur)


@pytest.fixture()
def backend():
    return pytest.importorskip("forge_mvc_mariadb.backend").MariaDBBackend()


def test_l_attente_de_verrou_est_une_indisponibilite(backend) -> None:
    """Mesuré : errno 1205, SQLSTATE HY000, « Lock wait timeout exceeded »."""
    erreur = _ErreurPilote("Lock wait timeout exceeded; try restarting transaction",
                           errno=1205, sqlstate="HY000")

    assert backend.is_unavailable(erreur) is True


def test_l_interblocage_reste_une_erreur_du_serveur(backend) -> None:
    """Mesuré : errno 1213, SQLSTATE 40001, « Deadlock found ».

    Transitoire lui aussi, mais hors famille : le critère est « attendre
    suffit », et attendre n'y change rien.
    """
    erreur = _ErreurPilote("Deadlock found when trying to get lock",
                           errno=1213, sqlstate="40001")

    assert backend.is_unavailable(erreur) is False


def test_la_raison_de_l_exclusion_est_ecrite(backend) -> None:
    """Une exclusion non expliquée se fait rétablir au ticket suivant."""
    doc = type(backend).is_unavailable.__doc__ or ""

    assert "1213" in doc
    assert "attendre" in doc


@pytest.mark.parametrize(("errno", "attendu"), [
    (1205, True),    # attente de verrou, mesuré
    (2006, True),    # coupure, mesuré au cycle 3
    (2013, True),
    (1213, False),   # interblocage
    (1062, False),   # doublon
    (1048, False),   # NOT NULL
    (1146, False),   # table inconnue
])
def test_la_frontiere_de_la_famille(backend, errno: int, attendu: bool) -> None:
    assert backend.is_unavailable(_ErreurPilote(errno=errno)) is attendu
