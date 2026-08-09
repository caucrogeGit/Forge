"""Intégration du store d'audit sur les trois serveurs (AUDIT-DB-INTEGRATION-001).

Vérifie le contrat SQL réel face au moteur : la DDL dialectale, l'insertion,
l'ordre décroissant par id, le filtrage, le plafond `limit` et la rétention.

## Ce qui a changé (`TEST-PACKAGE-INTEGRATION-REAL-LAYER-001`)

Ce fichier montait sa propre connexion MariaDB dans un adaptateur écrit à la
main. Il ne tournait donc que sur MariaDB, et court-circuitait la vraie couche
d'accès `core.database.db`, celle que l'application utilise en production.
Les tests passent désormais par `real_backend_db` : chacun s'exécute trois
fois, une par serveur, à travers la couche réelle.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

pytest.importorskip("forge_mvc_audit")

from forge_mvc_audit import get_audit_log, record_audit

from forge_mvc_testing.real_db import tables_temporaires


@pytest.fixture
def audit_db(real_backend_db: str) -> Iterator[Any]:
    """Table d'audit créée par sa DDL dialectale, sur le serveur du cas."""
    from forge_mvc_audit.tables import AUDIT_LOG

    with tables_temporaires(AUDIT_LOG) as db:
        yield db


def test_record_and_read_most_recent_first(audit_db: Any) -> None:
    record_audit("eleve.cree", actor="prof", target_type="eleve", target_id=1)
    record_audit("note.modifiee", actor="prof", target_type="note", target_id=7)
    entries = get_audit_log()
    assert [e.action for e in entries] == ["note.modifiee", "eleve.cree"]  # id DESC
    assert entries[0].target_id == "7" and entries[0].actor == "prof"


def test_filter_by_action(audit_db: Any) -> None:
    record_audit("eleve.cree", actor="a")
    record_audit("eleve.supprime", actor="b")
    record_audit("eleve.cree", actor="c")
    entries = get_audit_log(action="eleve.cree")
    assert len(entries) == 2 and all(e.action == "eleve.cree" for e in entries)


def test_limit_is_applied(audit_db: Any) -> None:
    """La borne est rendue par le dialecte : T-SQL ne connaît pas `LIMIT`."""
    for i in range(5):
        record_audit("x", target_id=i)
    assert len(get_audit_log(limit=3)) == 3


def test_created_at_is_populated(audit_db: Any) -> None:
    record_audit("connexion", actor="prof")
    entry = get_audit_log(limit=1)[0]
    assert entry.created_at and entry.action == "connexion"


# ── Rétention (AUDIT-RETENTION-001) ──────────────────────────────────────────
#
# `record_audit` laisse `created_at` au défaut du moteur, donc toute ligne
# écrite par lui date de maintenant. Vieillir une entrée demande un INSERT qui
# pose la colonne explicitement, ce que fait `_inserer_datee`.


def _inserer_datee(db: Any, action: str, created_at: str) -> None:
    db.execute(
        "INSERT INTO audit_log (actor, action, created_at) VALUES (?, ?, ?)",
        ("systeme", action, created_at),
    )


def test_la_purge_ne_retire_que_les_entrees_anterieures(audit_db: Any) -> None:
    """LE test du ticket : la borne discrimine, elle ne vide pas la table."""
    from forge_mvc_audit.store import count_audit_before, purge_audit_before

    _inserer_datee(audit_db, "vieille", "2020-01-01 00:00:00")
    _inserer_datee(audit_db, "recente", "2026-08-01 00:00:00")
    borne = "2026-01-01 00:00:00"

    assert count_audit_before(borne) == 1
    assert purge_audit_before(borne) == 1

    restantes = [e.action for e in get_audit_log()]
    assert restantes == ["recente"]


def test_le_comptage_ne_supprime_rien(audit_db: Any) -> None:
    """`audit:gc` affiche avant d'effacer : le comptage doit être inoffensif."""
    from forge_mvc_audit.store import count_audit_before

    _inserer_datee(audit_db, "vieille", "2020-01-01 00:00:00")
    borne = "2026-01-01 00:00:00"

    assert count_audit_before(borne) == 1
    assert count_audit_before(borne) == 1
    assert len(get_audit_log()) == 1


def test_une_purge_sans_cible_ne_supprime_rien(audit_db: Any) -> None:
    from forge_mvc_audit.store import purge_audit_before

    _inserer_datee(audit_db, "recente", "2026-08-01 00:00:00")

    assert purge_audit_before("2020-01-01 00:00:00") == 0
    assert len(get_audit_log()) == 1


def test_la_borne_calculee_en_jours_s_applique_reellement(audit_db: Any) -> None:
    """Bout en bout : `cutoff_for_days` produit une borne que le SQL sait comparer.

    C'est le point de jonction entre le calcul Python et la colonne SQL. Un
    format d'horodatage divergent passerait les tests unitaires et échouerait
    seulement ici, et il peut diverger **par moteur** : c'est exactement ce que
    l'exécution sur les trois serveurs vient éprouver.
    """
    from datetime import datetime, timedelta, timezone

    from forge_mvc_audit.store import cutoff_for_days, purge_audit_before

    maintenant = datetime.now(timezone.utc)
    vieille = (maintenant - timedelta(days=120)).strftime("%Y-%m-%d %H:%M:%S")
    recente = (maintenant - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
    _inserer_datee(audit_db, "vieille", vieille)
    _inserer_datee(audit_db, "recente", recente)

    assert purge_audit_before(cutoff_for_days(90)) == 1
    assert [e.action for e in get_audit_log()] == ["recente"]
