"""MARIADB-POOL-QUEUE-001 : une file d'attente devant le pool de connexions.

Le pilote MariaDB n'offre **aucune** file : son `get_connection()` lève
immédiatement dès que toutes les connexions sont prises. Mesuré avant
correctif, avec le pool par défaut de cinq et une lecture indexée de 0,26 ms :

    20 requêtes simultanées  ->   13 servies,   7 en échec
    200 requêtes simultanées ->   55 servies, 145 en échec

Ce n'est pas un problème de capacité : cinq connexions servent près de 19 000
requêtes par seconde. C'est l'absence de file. Une requête arrivée pendant une
pointe échouait alors qu'attendre une fraction de milliseconde suffisait.

**Une boucle de réessais aggrave la situation**, mesuré aussi : 200 emprunteurs
interrogeant le pool toutes les millisecondes se disputent son verrou, et le
nombre d'échecs passe de 146 à 170. Il faut un vrai sémaphore, où l'on patiente
sans solliciter le pool.

Marqué `db` : sauté sans serveur, requis en CI via FORGE_REQUIRE_DB=1.
"""
from __future__ import annotations

import threading
import time
from typing import Any

import pytest

pytestmark = pytest.mark.db

TABLE = "pool_queue_demo"


def _backend() -> Any:
    from core.database.backend import get_backend

    return get_backend()


@pytest.fixture()
def table_chargee(real_db: None) -> Any:
    """Une table indexée, pour des lectures rapides et réalistes."""
    from core.database import db

    db.execute(f"DROP TABLE IF EXISTS {TABLE}")
    db.execute(
        f"CREATE TABLE {TABLE} (id INT AUTO_INCREMENT PRIMARY KEY, n INT, INDEX(n))"
        " ENGINE=InnoDB"
    )
    for i in range(200):
        db.execute(f"INSERT INTO {TABLE} (n) VALUES (?)", (i % 20,))
    try:
        yield
    finally:
        db.execute(f"DROP TABLE IF EXISTS {TABLE}")


def _rafale(nombre: int) -> "tuple[int, int]":
    """Lance `nombre` lectures simultanées ; rend (servies, en échec)."""
    from core.database import db

    resultat = {"ok": 0, "ko": 0}
    verrou = threading.Lock()

    def lire() -> None:
        try:
            db.fetch_all(f"SELECT n FROM {TABLE} WHERE n = ? LIMIT 10", (7,))
            with verrou:
                resultat["ok"] += 1
        except Exception:  # noqa: BLE001 - on compte, on ne qualifie pas ici
            with verrou:
                resultat["ko"] += 1

    fils = [threading.Thread(target=lire) for _ in range(nombre)]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()
    return resultat["ok"], resultat["ko"]


# ── Le contrôle décisif : une rafale ne perd plus personne ───────────────────

@pytest.mark.parametrize("simultanees", [20, 50, 200])
def test_une_rafale_est_entierement_servie(simultanees: int, table_chargee: None) -> None:
    """Bien au delà de la taille du pool, et sans un seul échec."""
    servies, echecs = _rafale(simultanees)

    assert echecs == 0, f"{echecs} requêtes refusées sur {simultanees}"
    assert servies == simultanees


def test_la_rafale_reste_rapide(table_chargee: None) -> None:
    """La file fait patienter, elle ne doit pas effondrer le débit."""
    depart = time.time()
    servies, echecs = _rafale(200)
    duree = time.time() - depart

    assert (servies, echecs) == (200, 0)
    assert duree < 5.0, f"200 lectures en {duree:.1f}s : la file étrangle le débit"


# ── Le contrat de la file ────────────────────────────────────────────────────

def test_la_file_a_autant_de_jetons_que_le_pool(real_db: None) -> None:
    import os

    backend = _backend()
    backend.get_connection.__self__._get_pool()  # force la création du pool
    gate = backend._gate  # pyright: ignore[reportPrivateUsage]

    assert gate is not None, "la file doit naître avec le pool"
    assert gate._initial_value == int(os.environ.get("DB_POOL_SIZE", "5"))  # pyright: ignore[reportPrivateUsage]


def test_un_emprunt_rend_son_jeton_a_la_restitution(real_db: None) -> None:
    """Sans quoi la capacité s'éroderait à chaque requête."""
    backend = _backend()
    connexion = backend.get_connection()
    backend.close_connection(connexion)

    avant = backend._gate._value  # pyright: ignore[reportPrivateUsage]
    for _ in range(50):
        c = backend.get_connection()
        backend.close_connection(c)

    assert backend._gate._value == avant  # pyright: ignore[reportPrivateUsage]


def test_l_attente_expiree_leve_une_erreur_qualifiee(real_db: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Surcharge n'est pas panne : l'erreur doit être reconnaissable.

    Le cœur la traduit en 503 ; une exception de pilote donnerait un 500, qui
    annoncerait un bug du serveur là où le remède est d'élargir le pool.
    """
    from core.database.errors import DatabaseUnavailableError

    backend = _backend()
    monkeypatch.setenv("DB_POOL_TIMEOUT", "0.2")

    prises = [backend.get_connection() for _ in range(backend._gate._initial_value)]  # pyright: ignore[reportPrivateUsage]
    try:
        with pytest.raises(DatabaseUnavailableError):
            backend.get_connection()
    finally:
        for connexion in prises:
            backend.close_connection(connexion)


def test_apres_la_saturation_le_service_repart(real_db: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """La saturation est passagère : rien ne doit rester bloqué."""
    from core.database.errors import DatabaseUnavailableError

    backend = _backend()
    monkeypatch.setenv("DB_POOL_TIMEOUT", "0.2")

    prises = [backend.get_connection() for _ in range(backend._gate._initial_value)]  # pyright: ignore[reportPrivateUsage]
    with pytest.raises(DatabaseUnavailableError):
        backend.get_connection()
    for connexion in prises:
        backend.close_connection(connexion)

    reprise = backend.get_connection()
    backend.close_connection(reprise)
