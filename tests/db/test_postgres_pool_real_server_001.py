"""POSTGRES-POOL-001, mesure sur serveur réel.

Un pool ne se prouve pas hors base : ce qui compte est qu'une **même connexion
physique** resserve, que rien de l'emprunteur précédent n'y traîne, et que la
saturation attende au lieu d'échouer. `pg_backend_pid()` donne la preuve
directe, un identifiant de session par connexion physique.

Relevé avant le pool, pour mémoire : 12,12 ms par requête contre 0,16 ms sur
une connexion tenue, et 200 requêtes simultanées en 0,86 s. Après : une seule
session pour cinq requêtes à `DB_POOL_SIZE=1`, et 200 simultanées en 0,17 s.

Le pendant hors base est `packages/forge-mvc-postgres/tests/test_postgres_pool_001.py`.
"""
from __future__ import annotations

import os
import threading

import pytest

pytestmark = pytest.mark.db


@pytest.fixture()
def pool_d_une_place(real_pg_db: None, monkeypatch: pytest.MonkeyPatch):
    """Force une seule connexion physique : tout emprunt sert la même."""
    from core.database import db
    from core.database.backend import reset_backend

    monkeypatch.setenv("DB_POOL_SIZE", "1")
    monkeypatch.setenv("DB_POOL_TIMEOUT", "5")
    reset_backend()
    yield db
    reset_backend()


# ── La connexion physique est bien réutilisée ────────────────────────────────

def test_cinq_requetes_tiennent_dans_une_seule_session(pool_d_une_place) -> None:
    """Sans pool, chaque requête ouvrait sa propre session serveur."""
    sessions = set()
    for _ in range(5):
        ligne = pool_d_une_place.fetch_one("SELECT pg_backend_pid() AS pid")
        assert ligne is not None
        sessions.add(ligne["pid"])

    assert len(sessions) == 1, f"le pool devrait resservir la même session : {sessions}"


def test_le_pool_respecte_sa_taille(real_pg_db: None,
                                    monkeypatch: pytest.MonkeyPatch) -> None:
    """Deux places, donc au plus deux sessions distinctes sur la durée."""
    from core.database import db
    from core.database.backend import reset_backend

    monkeypatch.setenv("DB_POOL_SIZE", "2")
    reset_backend()
    try:
        sessions = set()
        for _ in range(10):
            ligne = db.fetch_one("SELECT pg_backend_pid() AS pid")
            assert ligne is not None
            sessions.add(ligne["pid"])

        assert len(sessions) <= 2, f"plus de sessions que de places : {sessions}"
    finally:
        reset_backend()


# ── Rien ne fuit d'un emprunteur au suivant ──────────────────────────────────

def test_une_table_temporaire_ne_survit_pas_a_la_restitution(
    pool_d_une_place,
) -> None:
    """La même connexion physique resservant, l'état doit être remis à zéro."""
    import psycopg

    pool_d_une_place.execute("CREATE TEMP TABLE forge_pool_temp (x INT)")

    with pytest.raises(psycopg.errors.UndefinedTable):
        pool_d_une_place.fetch_all("SELECT x FROM forge_pool_temp")


def test_une_variable_de_session_ne_survit_pas_non_plus(pool_d_une_place) -> None:
    pool_d_une_place.execute("SET application_name = 'sonde'")

    assert pool_d_une_place.fetch_one("SHOW application_name") == {
        "application_name": ""
    }


def test_les_requetes_preparees_survivent_a_la_remise_a_zero(
    pool_d_une_place,
) -> None:
    """Les effacer côté serveur désynchroniserait le catalogue de psycopg.

    Mesuré avec `DISCARD ALL` : la requête suivante échouait sur
    « l'instruction préparée _pg3_0 n'existe pas ». Le test rejoue donc
    plusieurs fois la même requête paramétrée, ce qui déclenche la préparation
    automatique de psycopg au delà de son seuil.
    """
    for valeur in range(8):
        ligne = pool_d_une_place.fetch_one("SELECT ? AS v", (valeur,))
        assert ligne == {"v": valeur}


# ── La saturation attend, puis rend un 503 ───────────────────────────────────

def test_la_saturation_devient_une_indisponibilite(
    real_pg_db: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deux places, vingt arrivants, une seconde d'attente : le reste patiente en vain."""
    from core.database import db
    from core.database.backend import reset_backend
    from core.database.errors import DatabaseUnavailableError

    monkeypatch.setenv("DB_POOL_SIZE", "2")
    monkeypatch.setenv("DB_POOL_TIMEOUT", "1")
    reset_backend()
    verrou = threading.Lock()
    succes = [0]
    indisponibles = [0]
    autres: "list[BaseException]" = []

    def travail() -> None:
        try:
            db.fetch_one("SELECT pg_sleep(0.4), 1 AS un")
            with verrou:
                succes[0] += 1
        except DatabaseUnavailableError:
            with verrou:
                indisponibles[0] += 1
        except BaseException as erreur:  # noqa: BLE001 — c'est le sujet du test
            with verrou:
                autres.append(erreur)

    try:
        fils = [threading.Thread(target=travail) for _ in range(20)]
        for f in fils:
            f.start()
        for f in fils:
            f.join()

        assert not autres, f"aucune erreur brute ne doit sortir : {autres[:2]}"
        assert indisponibles[0] > 0, "la saturation doit se voir"
        assert succes[0] > 0, "les places disponibles doivent servir"
        assert succes[0] + indisponibles[0] == 20
    finally:
        reset_backend()


def test_la_concurrence_ordinaire_passe_sans_echec(
    real_pg_db: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """200 requêtes brèves sur cinq places : personne ne doit être refusé."""
    from core.database import db
    from core.database.backend import reset_backend

    monkeypatch.setenv("DB_POOL_SIZE", "5")
    monkeypatch.setenv("DB_POOL_TIMEOUT", "10")
    reset_backend()
    verrou = threading.Lock()
    succes = [0]
    echecs: "list[BaseException]" = []

    def travail() -> None:
        try:
            db.fetch_one("SELECT 1 AS un")
            with verrou:
                succes[0] += 1
        except BaseException as erreur:  # noqa: BLE001 — c'est le sujet du test
            with verrou:
                echecs.append(erreur)

    try:
        fils = [threading.Thread(target=travail) for _ in range(200)]
        for f in fils:
            f.start()
        for f in fils:
            f.join()

        assert not echecs, f"{len(echecs)} échec(s) : {echecs[:2]}"
        assert succes[0] == 200
    finally:
        reset_backend()


# ── Les variables de pool ne sont plus ignorées ──────────────────────────────

def test_db_pool_size_est_reellement_lu(real_pg_db: None,
                                        monkeypatch: pytest.MonkeyPatch) -> None:
    from core.database.backend import get_backend, reset_backend

    monkeypatch.setenv("DB_POOL_SIZE", "3")
    reset_backend()
    try:
        backend = get_backend()
        backend.get_connection()  # provoque la création du pool
        assert backend._pool.max_size == 3  # pyright: ignore[reportAttributeAccessIssue]
    finally:
        reset_backend()


def test_l_administration_n_emprunte_pas_au_pool(
    real_pg_db: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Elle est ouverte en direct, et sa fermeture ne doit pas la rendre au pool.

    La fixture d'intégration ne pose que les identifiants applicatifs, le
    provisionnement PostgreSQL n'étant pas son objet : on ajoute donc les
    identifiants d'administration, que le backend lit séparément (ADR-033).
    """
    from core.database.backend import get_backend

    monkeypatch.setenv("DB_ADMIN_LOGIN", os.environ.get("DB_APP_LOGIN", ""))
    monkeypatch.setenv("DB_ADMIN_PWD", os.environ.get("DB_APP_PWD", ""))
    backend = get_backend()
    admin = backend.get_admin_connection(database=os.environ.get("DB_NAME", ""))

    assert getattr(admin, "pooled", False) is False
    backend.close_connection(admin)
