"""MFA-TOTP-REPLAY-SHARED-001 : le registre adossé à la base est bien partagé.

Le test central ouvre **deux connexions distinctes** et pose un
`DbTotpReplayStore` sur chacune, ce qui reproduit deux workers gunicorn. Un code
accepté par le premier doit être refusé par le second. C'est la propriété que le
registre en mémoire ne peut pas offrir, et le seul motif de ce ticket.

Marqué `db` : sauté en local sans base, requis en CI. Connexion auto-suffisante
via `FORGE_TEST_DB_*`, sur le gabarit des autres tests d'intégration de paquet.
"""
from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from typing import Any

import pytest

pytestmark = pytest.mark.db

pytest.importorskip("forge_mvc_mfa")

from forge_mvc_mfa.replay_store_db import DbTotpReplayStore

_REQUIRE_DB = os.environ.get("FORGE_REQUIRE_DB") == "1"


def _rendered_ddl() -> str:
    """DDL de la table, rendu pour le backend actif (source unique, ADR-071)."""
    from core.database.backend import get_backend
    from core.database.table_ddl import render_create_table
    from forge_mvc_mfa.tables import TOTP_REPLAY

    return chr(10).join(render_create_table(TOTP_REPLAY, get_backend().dialect))


def _params() -> dict[str, Any]:
    return {
        "host": os.environ.get("FORGE_TEST_DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("FORGE_TEST_DB_PORT", "3306")),
        "user": os.environ.get("FORGE_TEST_DB_USER", "root"),
        "password": os.environ.get("FORGE_TEST_DB_PASSWORD", ""),
    }


class _ConnAdapter:
    """Surface minimale attendue par `DbTotpReplayStore` : `execute`, `fetch_one`."""

    def __init__(self, conn: Any, database: str) -> None:
        self._conn = conn
        self._database = database

    def execute(self, sql: str, params: Any = ()) -> int:
        cur = self._conn.cursor()
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        self._conn.commit()
        compte = cur.rowcount
        cur.close()
        return int(compte)

    def fetch_one(self, sql: str, params: Any = ()) -> "dict[str, Any] | None":
        cur = self._conn.cursor(dictionary=True)
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        row = cur.fetchone()
        cur.close()
        return row


@pytest.fixture
def deux_workers() -> Iterator[tuple[DbTotpReplayStore, DbTotpReplayStore]]:
    """Deux magasins sur deux connexions distinctes, une seule base.

    Deux connexions et non une seule : partager la connexion prouverait
    seulement que deux objets Python voient la même session, pas que deux
    processus voient le même registre.
    """
    try:
        import mariadb
    except ImportError:  # pragma: no cover
        pytest.skip("paquet python 'mariadb' non installé")

    params = _params()
    db_name = f"forge_it_mfa_replay_{uuid.uuid4().hex[:10]}"
    try:
        admin = mariadb.connect(**params)
    except Exception as error:  # noqa: BLE001
        message = f"MariaDB de test injoignable : {error}"
        if _REQUIRE_DB:
            pytest.fail(message + " (FORGE_REQUIRE_DB=1)")
        pytest.skip(message + " (test d'intégration sauté en local)")

    cur = admin.cursor()
    cur.execute(f"CREATE DATABASE `{db_name}`")
    cur.execute(f"USE `{db_name}`")
    for instruction in _rendered_ddl().split(";"):
        if instruction.strip():
            cur.execute(instruction)
    admin.commit()
    cur.close()

    second = mariadb.connect(**params)
    try:
        yield (
            DbTotpReplayStore(db=_ConnAdapter(admin, db_name)),
            DbTotpReplayStore(db=_ConnAdapter(second, db_name)),
        )
    finally:
        second.close()
        cur = admin.cursor()
        cur.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
        admin.commit()
        cur.close()
        admin.close()


def test_un_code_accepte_par_un_worker_est_refuse_par_l_autre(
    deux_workers: tuple[DbTotpReplayStore, DbTotpReplayStore],
) -> None:
    """LE test du ticket. Il échoue si l'on repasse au registre en mémoire."""
    worker_1, worker_2 = deux_workers

    assert worker_1.check_and_record(42, 1000) is True
    assert worker_2.check_and_record(42, 1000) is False
    assert worker_2.is_replay(42, 1000) is True


def test_une_fenetre_anterieure_est_refusee_entre_workers(
    deux_workers: tuple[DbTotpReplayStore, DbTotpReplayStore],
) -> None:
    """La règle `<=` du contrat traverse les processus, pas seulement l'égalité."""
    worker_1, worker_2 = deux_workers

    assert worker_1.check_and_record(7, 2000) is True
    assert worker_2.check_and_record(7, 1999) is False
    assert worker_2.is_replay(7, 1999) is True


def test_une_fenetre_posterieure_est_acceptee(
    deux_workers: tuple[DbTotpReplayStore, DbTotpReplayStore],
) -> None:
    """Sans quoi le registre bloquerait l'authentification suivante, pas le rejeu."""
    worker_1, worker_2 = deux_workers

    assert worker_1.check_and_record(7, 2000) is True
    assert worker_2.check_and_record(7, 2001) is True
    assert worker_1.is_replay(7, 2000) is True


def test_deux_facteurs_ne_se_genent_pas(
    deux_workers: tuple[DbTotpReplayStore, DbTotpReplayStore],
) -> None:
    worker_1, worker_2 = deux_workers

    assert worker_1.check_and_record(1, 500) is True
    assert worker_2.check_and_record(2, 500) is True


def test_un_identifiant_non_tracable_ne_bloque_pas_et_n_ecrit_pas(
    deux_workers: tuple[DbTotpReplayStore, DbTotpReplayStore],
) -> None:
    """Même contrat que le registre en mémoire, sans toucher la table."""
    worker_1, _ = deux_workers

    assert worker_1.check_and_record(0, 10) is True
    assert worker_1.check_and_record(0, 10) is True
    assert worker_1.is_replay(0, 10) is False


def test_record_used_n_avance_jamais_a_reculons(
    deux_workers: tuple[DbTotpReplayStore, DbTotpReplayStore],
) -> None:
    worker_1, worker_2 = deux_workers

    worker_1.record_used(9, 3000)
    worker_2.record_used(9, 2500)

    assert worker_1.is_replay(9, 2999) is True
    assert worker_1.is_replay(9, 3001) is False


def test_la_purge_retire_les_fenetres_anciennes(
    deux_workers: tuple[DbTotpReplayStore, DbTotpReplayStore],
) -> None:
    """La purge compare des numéros de fenêtre, jamais des dates.

    Aucune arithmétique de date n'entre dans le SQL, ce qui la rend portable
    sans effort sur les quatre backends.
    """
    worker_1, _ = deux_workers
    from forge_mvc_mfa.totp_replay import step_for_time

    maintenant = 1_800_000_000.0
    ancienne = step_for_time(maintenant - 48 * 3600)
    recente = step_for_time(maintenant)

    assert worker_1.check_and_record(11, ancienne) is True
    assert worker_1.check_and_record(12, recente) is True

    assert worker_1.purge_old(maintenant) == 1
    assert worker_1.is_replay(11, ancienne) is False
    assert worker_1.is_replay(12, recente) is True
