"""Le registre anti-rejeu adossé à la base est partagé (MFA-TOTP-REPLAY-SHARED-001).

Le test central pose **deux magasins distincts** sur la même base, ce qui
reproduit deux workers gunicorn. Un code accepté par le premier doit être refusé
par le second. C'est la propriété que le registre en mémoire ne peut pas offrir,
et le seul motif de ce ticket.

## Ce qui a changé (`TEST-PACKAGE-INTEGRATION-REAL-LAYER-001`)

Ce fichier ouvrait deux connexions MariaDB à la main et posait un adaptateur sur
chacune. Il ne tournait donc que sur MariaDB, et surtout il court-circuitait la
**qualification d'erreur** de Forge : une violation d'unicité y remontait sous
sa forme pilote, jamais sous la forme portable `UniqueViolationError`. C'est
exactement cet écart qui a caché deux défauts du magasin pendant tout un cycle,
un interblocage InnoDB et un doublon non reconnu, tous deux trouvés seulement en
mettant le magasin en course réelle.

Les deux magasins passent maintenant par `core.database.db`. La preuve du
partage en est renforcée, pas affaiblie : chaque opération emprunte une
connexion au pool, donc deux appels successifs du même magasin peuvent déjà
tomber sur deux connexions différentes.

Le pendant sous concurrence est `tests/db/test_mfa_replay_concurrency_real_server_001.py`.
"""
from __future__ import annotations

from collections.abc import Iterator

import pytest

pytest.importorskip("forge_mvc_mfa")

from forge_mvc_mfa.replay_store_db import DbTotpReplayStore

from forge_mvc_testing.real_db import tables_temporaires


@pytest.fixture
def deux_workers(
    real_backend_db: str,
) -> Iterator[tuple[DbTotpReplayStore, DbTotpReplayStore]]:
    """Deux magasins distincts sur la même base, sur le serveur du cas."""
    from forge_mvc_mfa.tables import TOTP_REPLAY

    with tables_temporaires(TOTP_REPLAY):
        yield (DbTotpReplayStore(), DbTotpReplayStore())


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
    sans effort sur les quatre backends. Ce fichier le vérifie maintenant sur
    trois d'entre eux, au lieu de l'affirmer depuis un seul.
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
