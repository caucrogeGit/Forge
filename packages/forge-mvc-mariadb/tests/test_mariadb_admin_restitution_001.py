# pyright: strict
"""MARIADB-ADMIN-RESTITUTION-001 — la restitution sait d'où vient la connexion.

`close_connection` rendait un jeton de file pour **toute** connexion, y compris
une connexion d'administration qui n'en a jamais pris : ouverte en direct par
`get_admin_connection`, elle ne passe pas par le pool. La file étant bornée,
elle levait « Semaphore released too many times » après avoir pourtant fermé la
connexion : une restitution parfaitement légitime échouait.

C'est le jumeau du piège trouvé sur PostgreSQL au même cycle, où `close()`
d'une connexion empruntée brûlait sa place : dans les deux cas, la restitution
ignorait la provenance. Le pilote MariaDB ne permettant pas de marquer ses
objets connexion (extension C, pas de `__dict__`), le backend tient un registre
des identités empruntées, retirées à la restitution.

Fakes : aucune de ces vérifications n'exige un serveur. Le pendant sur serveur
réel est `tests/db/test_mariadb_admin_restitution_real_server_001.py`.
"""
from __future__ import annotations

import threading
from typing import Any

import pytest

pytest.importorskip("forge_mvc_mariadb")

from forge_mvc_mariadb.backend import MariaDBBackend  # noqa: E402


class _Connexion:
    def __init__(self) -> None:
        self.fermetures = 0

    def close(self) -> None:
        self.fermetures += 1


class _PoolFactice:
    def __init__(self, connexions: "list[_Connexion]") -> None:
        self._connexions = list(connexions)

    def get_connection(self) -> _Connexion:
        return self._connexions.pop(0)


def _backend_avec_pool(taille: int) -> "tuple[MariaDBBackend, list[_Connexion]]":
    backend = MariaDBBackend()
    connexions = [_Connexion() for _ in range(taille)]
    backend._pool = _PoolFactice(connexions)  # pyright: ignore[reportPrivateUsage]
    backend._gate = threading.BoundedSemaphore(taille)  # pyright: ignore[reportPrivateUsage]
    return backend, connexions


def _jetons(backend: MariaDBBackend) -> int:
    gate: Any = backend._gate  # pyright: ignore[reportPrivateUsage]
    return gate._value


def test_une_connexion_hors_pool_ne_rend_aucun_jeton() -> None:
    """Le cas mesuré : fermer une connexion d'administration levait."""
    backend, _ = _backend_avec_pool(2)
    admin = _Connexion()  # jamais empruntée : ouverte en direct

    backend.close_connection(admin)

    assert admin.fermetures == 1, "la connexion doit être fermée"
    assert _jetons(backend) == 2, "aucun jeton ne doit être rendu"


def test_une_connexion_empruntee_rend_son_jeton() -> None:
    backend, _ = _backend_avec_pool(2)
    connexion = backend.get_connection()
    assert _jetons(backend) == 1

    backend.close_connection(connexion)

    assert _jetons(backend) == 2


def test_une_double_restitution_ne_rend_pas_deux_jetons() -> None:
    """Le registre est consommé à la première restitution."""
    backend, _ = _backend_avec_pool(2)
    connexion = backend.get_connection()
    backend.close_connection(connexion)

    backend.close_connection(connexion)  # seconde fois : plus au registre

    assert _jetons(backend) == 2, "la file bornée ne doit pas gonfler"


def test_le_registre_suit_chaque_emprunt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_POOL_TIMEOUT", "1")
    backend, _ = _backend_avec_pool(2)

    a = backend.get_connection()
    b = backend.get_connection()
    backend.close_connection(a)
    backend.close_connection(b)

    assert _jetons(backend) == 2
    assert backend._borrowed == set()  # pyright: ignore[reportPrivateUsage]


def test_la_fermeture_du_pool_vide_le_registre() -> None:
    backend, _ = _backend_avec_pool(1)
    backend.get_connection()

    backend.close()

    assert backend._borrowed == set()  # pyright: ignore[reportPrivateUsage]
