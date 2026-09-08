"""`JOBS-CLAIM-OWNERSHIP-001` — la possession d'une réservation est respectée.

Les écritures de fin filtraient sur le seul identifiant. Scénario mesuré, sur
SQLite et sur le code inchangé :

    A réserve la tâche 1
    le bail de A expire
    `reclaim_stale` la remet en file
    B la réserve
    le gestionnaire de A finit
    A passe la tâche à `done` et efface le jeton de B

B croyait travailler sur une tâche que personne ne lui reprendrait, et son
propre résultat n'aurait eu nulle part où aller.

C'est distinct du contrat « au moins une fois », qui autorise une réexécution
après incident. Ici, ce n'est pas l'effet applicatif qui est rejoué, c'est la
**possession** qui n'est pas vérifiée.

Zéro ligne mise à jour veut dire « réservation perdue ». Se rabattre est
acceptable, se taire ne l'est pas : l'écriture est refusée et le journal dit
pourquoi.
"""
from __future__ import annotations

import logging
import sqlite3
from typing import Any

import pytest

pytest.importorskip("forge_mvc_jobs")
pytest.importorskip("forge_mvc_sqlite")

from forge_mvc_jobs import queue as q  # noqa: E402
from forge_mvc_sqlite.dialect import SQLiteDialect  # noqa: E402

COLONNES = (
    "id INTEGER PRIMARY KEY, queue TEXT, task TEXT, payload TEXT, status TEXT, "
    "available_at TEXT, priority INTEGER, claim_token TEXT, started_at TEXT, "
    "attempts INTEGER, max_attempts INTEGER, last_error TEXT, finished_at TEXT"
)


class Base:
    """Une vraie base SQLite : les gardes SQL doivent être exercées par SQL."""

    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(f"CREATE TABLE {q.TABLE_NAME} ({COLONNES})")

    def execute(self, sql: str, params: Any = ()) -> int:
        curseur = self.conn.execute(sql, params)
        self.conn.commit()
        return curseur.rowcount

    def fetch_one(self, sql: str, params: Any = ()) -> "dict[str, Any] | None":
        ligne = self.conn.execute(sql, params).fetchone()
        return dict(ligne) if ligne is not None else None

    def fetch_all(self, sql: str, params: Any = ()) -> "list[dict[str, Any]]":
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]


@pytest.fixture
def base(monkeypatch: pytest.MonkeyPatch) -> Base:
    db = Base()
    db.execute(
        f"INSERT INTO {q.TABLE_NAME} VALUES "
        "(1,'default','work','{}','pending','2000-01-01',0,NULL,NULL,0,3,NULL,NULL)"
    )
    monkeypatch.setattr(q, "_dialect", lambda: SQLiteDialect())
    return db


def _voler_la_tache(db: Base) -> str:
    """Fait expirer le bail, reprend la tâche et la réserve pour un autre."""
    db.execute(f"UPDATE {q.TABLE_NAME} SET started_at='2000-01-01' WHERE id=1")
    assert q.reclaim_stale(lease_seconds=1, db=db).requeued == 1
    assert db.execute(q._claim_sql(), ("worker-B", 1)) == 1
    return "worker-B"


class TestUnOuvrierPerimeNEcrasePlusRien:
    """Le scénario mesuré, dans ses trois issues."""

    def test_un_succes_tardif_ne_prend_pas_la_tache_d_un_autre(self, base: Base) -> None:
        def handler(_payload: dict[str, Any]) -> None:
            _voler_la_tache(base)

        assert q.process_one({"work": handler}, db=base) is True

        etat = base.fetch_one(f"SELECT status, claim_token FROM {q.TABLE_NAME}")
        assert etat["status"] == "running", "B travaille encore sur cette tâche"
        assert etat["claim_token"] == "worker-B", "le jeton de B doit survivre"

    def test_un_echec_tardif_non_plus(self, base: Base) -> None:
        def handler(_payload: dict[str, Any]) -> None:
            _voler_la_tache(base)
            raise RuntimeError("oups")

        assert q.process_one({"work": handler}, db=base) is True

        etat = base.fetch_one(f"SELECT status, claim_token, last_error FROM {q.TABLE_NAME}")
        assert etat["status"] == "running"
        assert etat["claim_token"] == "worker-B"
        assert etat["last_error"] is None

    def test_une_tache_inconnue_tardive_non_plus(self, base: Base) -> None:
        """Le chemin « pas de gestionnaire » écrivait aussi sans garde."""
        _voler_la_tache_apres_reservation = None  # lisibilité : rien à faire ici
        assert _voler_la_tache_apres_reservation is None

        # La tâche est réservée par process_one, puis volée avant l'écriture :
        # on rejoue la garde directement, le chemin n'ayant pas de point d'accroche.
        base.execute(q._claim_sql(), ("worker-A", 1))
        _voler_la_tache(base)

        assert base.execute(q._fail_sql(), ("tâche inconnue", 1, "worker-A")) == 0
        assert base.fetch_one(f"SELECT claim_token FROM {q.TABLE_NAME}")["claim_token"] == "worker-B"


class TestLeCasNominalNEstPasCasse:
    """Une garde qui refuserait tout ne protégerait rien non plus."""

    def test_un_succes_ordinaire_termine_la_tache(self, base: Base) -> None:
        assert q.process_one({"work": lambda p: None}, db=base) is True

        etat = base.fetch_one(f"SELECT status, claim_token FROM {q.TABLE_NAME}")
        assert etat["status"] == "done"
        assert etat["claim_token"] is None

    def test_un_echec_ordinaire_remet_en_file(self, base: Base) -> None:
        def boum(_payload: dict[str, Any]) -> None:
            raise RuntimeError("oups")

        assert q.process_one({"work": boum}, db=base) is True

        etat = base.fetch_one(f"SELECT status, claim_token FROM {q.TABLE_NAME}")
        assert etat["status"] == "pending"
        assert etat["claim_token"] is None


class TestLaPerteEstDite:
    """Se rabattre est acceptable, se taire ne l'est pas."""

    def test_le_journal_nomme_la_tache_et_la_cause(
        self, base: Base, caplog: pytest.LogCaptureFixture
    ) -> None:
        def handler(_payload: dict[str, Any]) -> None:
            _voler_la_tache(base)

        with caplog.at_level(logging.WARNING, logger="forge.jobs"):
            q.process_one({"work": handler}, db=base)

        assert "réservation perdue" in caplog.text
        assert "bail" in caplog.text
