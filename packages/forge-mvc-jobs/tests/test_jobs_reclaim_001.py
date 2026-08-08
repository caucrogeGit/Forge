"""JOBS-STALE-RECLAIM-001 : les tâches orphelines sont reprises.

Ces tests ne touchent pas la base. Ils portent sur la formule du délai
croissant, sur le refus d'un bail absurde, et surtout sur **la forme du SQL
engendré**, qui est ici le vrai risque.

Le piège mesuré. `interval_seconds_expression()` compose son modificateur par
concaténation dans le dialecte SQLite, `'+' || ? || ' seconds'`, et rend `NULL`
pour une valeur négative. Une reprise écrite `started_at < maintenant - bail`
aurait donc comparé à `NULL`, ce qui est faux, et n'aurait **rien repris du
tout sur SQLite, sans lever la moindre erreur**. L'inégalité est donc écrite
`started_at + bail < maintenant`, qui n'emploie que des secondes positives.

Un garde-fou vérifie que personne ne réintroduira la forme négative.

La preuve que la reprise déplace réellement les bonnes lignes est ailleurs,
elle exige un serveur : `test_jobs_db_integration_001.py`.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_jobs")

from forge_mvc_jobs.errors import JobError
from forge_mvc_jobs.queue import (
    BACKOFF_BASE_SECONDS,
    BACKOFF_CAP_SECONDS,
    backoff_seconds,
    reclaim_stale,
)


@pytest.mark.parametrize(
    ("tentatives", "attendu"),
    [(1, 10), (2, 20), (3, 40), (4, 80), (5, 160), (6, 320), (7, 600), (20, 600)],
)
def test_le_delai_double_puis_plafonne(tentatives: int, attendu: int) -> None:
    assert backoff_seconds(tentatives) == attendu


def test_le_delai_est_borne_par_le_plafond() -> None:
    """Sans plafond, la huitième tentative attendrait plus de vingt minutes."""
    assert backoff_seconds(50) == BACKOFF_CAP_SECONDS
    assert backoff_seconds(1) == BACKOFF_BASE_SECONDS


def test_le_delai_d_un_compteur_absurde_est_nul() -> None:
    assert backoff_seconds(0) == 0
    assert backoff_seconds(-3) == 0


@pytest.mark.parametrize("bail", [0, -1, -900])
def test_un_bail_nul_ou_negatif_est_refuse(bail: int) -> None:
    """Il reprendrait des tâches en cours d'exécution, donc les doublerait."""
    with pytest.raises(JobError, match="en cours d'exécution"):
        reclaim_stale(lease_seconds=bail)


def test_le_sql_de_reprise_n_emploie_aucune_seconde_negative() -> None:
    """Garde-fou du piège : la soustraction doit rester du côté de `started_at`.

    Le test lit le SQL rendu pour le backend actif et vérifie que l'intervalle
    porte sur `started_at`, jamais sur l'instant courant. Écrire
    `maintenant - bail` exigerait un paramètre négatif, que SQLite rendrait
    `NULL` en silence.
    """
    from forge_mvc_jobs.queue import _stale_predicate  # pyright: ignore[reportPrivateUsage]

    predicat = _stale_predicate()

    assert "started_at" in predicat
    assert "-" not in predicat.replace("--", ""), (
        "un signe moins dans le prédicat trahit une soustraction de date : "
        f"{predicat!r}"
    )


def test_le_predicat_ignore_les_taches_jamais_reservees() -> None:
    """`started_at IS NULL` désigne une tâche en attente, pas une orpheline."""
    from forge_mvc_jobs.queue import _stale_predicate  # pyright: ignore[reportPrivateUsage]

    predicat = _stale_predicate()

    assert "started_at IS NOT NULL" in predicat
    assert "status='running'" in predicat


def test_les_deux_sorts_de_reprise_sont_disjoints() -> None:
    """Une tâche reprise part en file OU en échec, jamais les deux."""
    from forge_mvc_jobs.queue import (
        _reclaim_fail_sql,  # pyright: ignore[reportPrivateUsage]
        _reclaim_requeue_sql,  # pyright: ignore[reportPrivateUsage]
    )

    assert "attempts < max_attempts" in _reclaim_requeue_sql()
    assert "attempts >= max_attempts" in _reclaim_fail_sql()


def test_l_echec_de_reprise_se_distingue_d_une_exception() -> None:
    """Confondre les deux ferait chercher un bogue là où il y a eu une panne."""
    from forge_mvc_jobs.queue import RECLAIM_FAILURE_MESSAGE

    assert "bail" in RECLAIM_FAILURE_MESSAGE
    assert "verdict" in RECLAIM_FAILURE_MESSAGE
