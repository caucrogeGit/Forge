"""DB-CONNECTION-LOST-503-001, mesure sur serveurs réels.

`is_unavailable` repose sur des codes relevés à la main en tuant une
connexion côté serveur. Ces codes ne sont écrits nulle part de façon
contractuelle : ils appartiennent au pilote et peuvent changer avec lui.
Seul un test qui tue réellement la connexion prouve que la reconnaissance
tient encore.

Le protocole : ouvrir une connexion, relever son identifiant côté serveur, la
tuer depuis une seconde connexion, puis rejouer une requête. Sur MariaDB le
délai compte, le pilote revalidant au delà d'une demi-seconde d'inactivité ;
on frappe donc immédiatement, ce qui est justement le cas réel du redémarrage
sous trafic.

Le pendant hors base est `tests/test_db_connection_lost_503_001.py`.
"""
from __future__ import annotations

import time
from typing import Any

import pytest

pytestmark = pytest.mark.db


# ── MariaDB ──────────────────────────────────────────────────────────────────

def test_mariadb_une_connexion_tuee_devient_une_indisponibilite(
    real_db: None,
) -> None:
    """Le cas mesuré : sans traduction, `InterfaceError` faisait un 500."""
    from core.database import db
    from core.database.backend import get_backend
    from core.database.errors import DatabaseUnavailableError

    backend = get_backend()
    victime = backend.get_connection()
    cursor = victime.cursor()
    cursor.execute("SELECT CONNECTION_ID()")
    identifiant = cursor.fetchone()[0]
    cursor.close()
    backend.close_connection(victime)

    bourreau = backend.get_connection()
    tueur = bourreau.cursor()
    tueur.execute(f"KILL {int(identifiant)}")
    tueur.close()
    backend.close_connection(bourreau)

    # Immédiatement : sous le seuil de revalidation du pilote, la connexion
    # morte est remise en circulation telle quelle.
    erreur: "Exception | None" = None
    for _ in range(5):
        try:
            db.fetch_one("SELECT 1 AS v")
        except Exception as capture:  # noqa: BLE001 — c'est le sujet du test
            erreur = capture
            break

    if erreur is None:
        pytest.skip("le pilote a revalidé avant l'emprunt : coupure non observable")

    assert isinstance(erreur, DatabaseUnavailableError), (
        f"la coupure doit être qualifiée, pas remontée brute : {type(erreur).__name__}"
    )


def test_mariadb_la_requete_suivante_passe(real_db: None) -> None:
    """La condition est passagère : c'est ce qui justifie le 503 plutôt qu'un 500."""
    from core.database import db

    time.sleep(1.0)

    assert db.fetch_one("SELECT 1 AS v") == {"v": 1}


def test_mariadb_reconnait_ses_deux_errno(real_db: None) -> None:
    """2006 et 2013 selon que la coupure est vue avant ou pendant la requête."""
    import mariadb

    from core.database.backend import get_backend

    backend = get_backend()
    for errno in (2006, 2013):
        erreur = mariadb.InterfaceError("coupure")
        erreur.errno = errno  # pyright: ignore[reportAttributeAccessIssue]
        assert backend.is_unavailable(erreur) is True


def test_mariadb_ne_confond_pas_avec_un_doublon(real_db: None) -> None:
    """Un vrai doublon obtenu du serveur ne doit pas passer pour une coupure."""
    from core.database import db
    from core.database.backend import get_backend
    from core.database.errors import UniqueViolationError

    db.execute("DROP TABLE IF EXISTS forge_lost_dup")
    db.execute("CREATE TABLE forge_lost_dup (id INT PRIMARY KEY)")
    db.execute("INSERT INTO forge_lost_dup (id) VALUES (1)")
    try:
        with pytest.raises(UniqueViolationError):
            db.execute("INSERT INTO forge_lost_dup (id) VALUES (1)")
    finally:
        db.execute("DROP TABLE IF EXISTS forge_lost_dup")

    assert get_backend().is_unavailable(ValueError("rien à voir")) is False


# ── PostgreSQL ───────────────────────────────────────────────────────────────

@pytest.mark.db_pg
def test_postgres_une_session_terminee_devient_une_indisponibilite(
    real_pg_db: None,
) -> None:
    from core.database import db
    from core.database.backend import get_backend
    from core.database.errors import DatabaseUnavailableError

    backend = get_backend()
    victime = backend.get_connection()
    cursor = victime.cursor()
    cursor.execute("SELECT pg_backend_pid()")
    pid = cursor.fetchone()[0]
    cursor.close()

    bourreau = backend.get_connection()
    tueur = bourreau.cursor()
    # Marqueur Forge `?` et non `%s` : le curseur du backend traduit les
    # marqueurs, et un `%s` écrit à la main serait échappé en `%%s`.
    tueur.execute("SELECT pg_terminate_backend(?)", (int(pid),))
    bourreau.commit()
    tueur.close()
    backend.close_connection(bourreau)

    erreur: "Exception | None" = None
    try:
        mort = victime.cursor()
        mort.execute("SELECT 1")
    except Exception as capture:  # noqa: BLE001 — c'est le sujet du test
        erreur = capture

    assert erreur is not None, "la session terminée devrait faire échouer la requête"
    assert backend.is_unavailable(erreur) is True

    # La victime doit repartir, morte ou vive : depuis POSTGRES-POOL-001 elle
    # occupe une place du pool tant qu'elle n'est pas rendue, et le pool la
    # remplace de lui-même en constatant qu'elle ne répond plus.
    backend.close_connection(victime)

    # Et le cœur traduit bien, sur une connexion neuve prise au backend.
    assert db.fetch_one("SELECT 1 AS v") == {"v": 1}
    assert issubclass(DatabaseUnavailableError, Exception)


@pytest.mark.db_pg
def test_postgres_ne_confond_pas_avec_une_erreur_de_requete(
    real_pg_db: None,
) -> None:
    """Une faute de syntaxe porte un SQLSTATE serveur : ce n'est pas une coupure."""
    from core.database.backend import get_backend

    backend = get_backend()
    connection = backend.get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM table_qui_nexiste_pas_du_tout")
        except Exception as erreur:  # noqa: BLE001 — c'est le sujet du test
            assert backend.is_unavailable(erreur) is False
        else:
            pytest.fail("la requête aurait dû échouer")
        finally:
            cursor.close()
    finally:
        backend.close_connection(connection)


# ── SQL Server ───────────────────────────────────────────────────────────────

@pytest.mark.db_mssql
def test_mssql_une_session_tuee_devient_une_indisponibilite(
    real_mssql_db: None,
) -> None:
    from core.database.backend import get_backend

    backend = get_backend()
    victime = backend.get_connection()
    cursor = victime.cursor()
    cursor.execute("SELECT @@SPID")
    spid = cursor.fetchone()[0]

    bourreau = backend.get_connection()
    bourreau.autocommit = True
    tueur = bourreau.cursor()
    tueur.execute(f"KILL {int(spid)}")
    tueur.close()
    backend.close_connection(bourreau)
    time.sleep(0.3)

    erreur: "Exception | None" = None
    try:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    except Exception as capture:  # noqa: BLE001 — c'est le sujet du test
        erreur = capture

    assert erreur is not None, "la session tuée devrait faire échouer la requête"
    assert backend.is_unavailable(erreur) is True, (
        f"SQLSTATE inattendu : {getattr(erreur, 'args', ())}"
    )


@pytest.mark.db_mssql
def test_mssql_ne_confond_pas_avec_une_erreur_de_requete(
    real_mssql_db: None,
) -> None:
    from core.database.backend import get_backend

    backend = get_backend()
    connection = backend.get_connection()
    try:
        cursor: Any = connection.cursor()
        try:
            cursor.execute("SELECT * FROM table_qui_nexiste_pas_du_tout")
        except Exception as erreur:  # noqa: BLE001 — c'est le sujet du test
            assert backend.is_unavailable(erreur) is False
        else:
            pytest.fail("la requête aurait dû échouer")
        finally:
            cursor.close()
    finally:
        backend.close_connection(connection)
