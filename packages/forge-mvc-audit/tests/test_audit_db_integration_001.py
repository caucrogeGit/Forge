"""Intégration MariaDB du store d'audit (AUDIT-DB-INTEGRATION-001).

Vérifie le contrat SQL réel : `CREATE_TABLE_SQL`, l'insertion, l'ordre
décroissant par id, le filtrage et le plafond `limit`. Marqué `db` : sauté en
local sans base, requis en CI. Connexion auto-suffisante via `FORGE_TEST_DB_*`.
"""
from __future__ import annotations

import os
import uuid
from typing import Any

import pytest

pytestmark = pytest.mark.db

forge_mvc_audit = pytest.importorskip("forge_mvc_audit")

from forge_mvc_audit import get_audit_log, record_audit

from forge_mvc_testing.db_probe import connection_failure_message

_REQUIRE_DB = os.environ.get("FORGE_REQUIRE_DB") == "1"


def _rendered_ddl() -> str:
    """DDL de la table, rendu pour le backend actif.

    La constante de schéma du module est supprimée
    (`OPTIN-DDL-CONSTANTS-001`) : deux façons officielles de créer la même
    table contredisaient le principe 11. La source unique est la déclaration
    `forge_mvc_audit.tables`, rendue par le dialecte.
    """
    from core.database.backend import get_backend
    from core.database.table_ddl import render_create_table
    from forge_mvc_audit.tables import AUDIT_LOG

    return chr(10).join(render_create_table(AUDIT_LOG, get_backend().dialect))

def _params() -> dict[str, Any]:
    return {
        "host": os.environ.get("FORGE_TEST_DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("FORGE_TEST_DB_PORT", "3306")),
        "user": os.environ.get("FORGE_TEST_DB_USER", "root"),
        "password": os.environ.get("FORGE_TEST_DB_PASSWORD", ""),
    }


class _ConnAdapter:
    def __init__(self, conn: Any, database: str) -> None:
        self._conn = conn
        self._database = database

    def insert(self, sql: str, params: Any = ()) -> int:
        cur = self._conn.cursor()
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        self._conn.commit()
        rid = cur.lastrowid
        cur.close()
        return int(rid)

    def fetch_all(self, sql: str, params: Any = ()) -> list[dict[str, Any]]:
        cur = self._conn.cursor(dictionary=True)
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        cur.close()
        return rows

    def fetch_one(self, sql: str, params: Any = ()) -> "dict[str, Any] | None":
        cur = self._conn.cursor(dictionary=True)
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        row = cur.fetchone()
        cur.close()
        return row

    def execute(self, sql: str, params: Any = ()) -> int:
        cur = self._conn.cursor()
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        self._conn.commit()
        compte = cur.rowcount
        cur.close()
        return int(compte)


@pytest.fixture
def audit_db() -> Any:
    try:
        import mariadb
    except ImportError:  # pragma: no cover
        pytest.skip("paquet python 'mariadb' non installé")

    params = _params()
    db_name = f"forge_it_audit_{uuid.uuid4().hex[:10]}"
    try:
        admin = mariadb.connect(**params)
    except Exception as error:  # noqa: BLE001
        message = connection_failure_message(
            "MariaDB", error, env_prefix="FORGE_TEST_DB"
        )
        if _REQUIRE_DB:
            pytest.fail(message + " (FORGE_REQUIRE_DB=1)")
        pytest.skip(message + " (test d'intégration sauté en local)")

    cur = admin.cursor()
    cur.execute(f"CREATE DATABASE `{db_name}`")
    cur.execute(f"USE `{db_name}`")
    cur.execute(_rendered_ddl())
    admin.commit()
    cur.close()
    try:
        yield _ConnAdapter(admin, db_name)
    finally:
        cur = admin.cursor()
        cur.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
        admin.commit()
        cur.close()
        admin.close()


def test_record_and_read_most_recent_first(audit_db: _ConnAdapter) -> None:
    record_audit("eleve.cree", actor="prof", target_type="eleve", target_id=1, db=audit_db)
    record_audit("note.modifiee", actor="prof", target_type="note", target_id=7, db=audit_db)
    entries = get_audit_log(db=audit_db)
    assert [e.action for e in entries] == ["note.modifiee", "eleve.cree"]  # id DESC
    assert entries[0].target_id == "7" and entries[0].actor == "prof"


def test_filter_by_action(audit_db: _ConnAdapter) -> None:
    record_audit("eleve.cree", actor="a", db=audit_db)
    record_audit("eleve.supprime", actor="b", db=audit_db)
    record_audit("eleve.cree", actor="c", db=audit_db)
    entries = get_audit_log(action="eleve.cree", db=audit_db)
    assert len(entries) == 2 and all(e.action == "eleve.cree" for e in entries)


def test_limit_is_applied(audit_db: _ConnAdapter) -> None:
    for i in range(5):
        record_audit("x", target_id=i, db=audit_db)
    assert len(get_audit_log(limit=3, db=audit_db)) == 3


def test_created_at_is_populated(audit_db: _ConnAdapter) -> None:
    record_audit("connexion", actor="prof", db=audit_db)
    entry = get_audit_log(limit=1, db=audit_db)[0]
    assert entry.created_at and entry.action == "connexion"


# ── Rétention (AUDIT-RETENTION-001) ──────────────────────────────────────────
#
# `record_audit` laisse `created_at` au DEFAULT CURRENT_TIMESTAMP, donc toute
# ligne écrite par lui date de maintenant. Vieillir une entrée demande un INSERT
# qui pose la colonne explicitement, ce que fait `_inserer_datee`.


def _inserer_datee(db: _ConnAdapter, action: str, created_at: str) -> None:
    db.execute(
        "INSERT INTO audit_log (actor, action, created_at) VALUES (?, ?, ?)",
        ("systeme", action, created_at),
    )


def test_la_purge_ne_retire_que_les_entrees_anterieures(audit_db: _ConnAdapter) -> None:
    """LE test du ticket : la borne discrimine, elle ne vide pas la table."""
    from forge_mvc_audit.store import count_audit_before, purge_audit_before

    _inserer_datee(audit_db, "vieille", "2020-01-01 00:00:00")
    _inserer_datee(audit_db, "recente", "2026-08-01 00:00:00")
    borne = "2026-01-01 00:00:00"

    assert count_audit_before(borne, db=audit_db) == 1
    assert purge_audit_before(borne, db=audit_db) == 1

    restantes = [e.action for e in get_audit_log(db=audit_db)]
    assert restantes == ["recente"]


def test_le_comptage_ne_supprime_rien(audit_db: _ConnAdapter) -> None:
    """`audit:gc` affiche avant d'effacer : le comptage doit être inoffensif."""
    from forge_mvc_audit.store import count_audit_before

    _inserer_datee(audit_db, "vieille", "2020-01-01 00:00:00")
    borne = "2026-01-01 00:00:00"

    assert count_audit_before(borne, db=audit_db) == 1
    assert count_audit_before(borne, db=audit_db) == 1
    assert len(get_audit_log(db=audit_db)) == 1


def test_une_purge_sans_cible_ne_supprime_rien(audit_db: _ConnAdapter) -> None:
    from forge_mvc_audit.store import purge_audit_before

    _inserer_datee(audit_db, "recente", "2026-08-01 00:00:00")

    assert purge_audit_before("2020-01-01 00:00:00", db=audit_db) == 0
    assert len(get_audit_log(db=audit_db)) == 1


def test_la_borne_calculee_en_jours_s_applique_reellement(audit_db: _ConnAdapter) -> None:
    """Bout en bout : `cutoff_for_days` produit une borne que le SQL sait comparer.

    C'est le point de jonction entre le calcul Python et la colonne SQL. Un
    format d'horodatage divergent passerait les tests unitaires et échouerait
    seulement ici.
    """
    from datetime import datetime, timedelta, timezone

    from forge_mvc_audit.store import cutoff_for_days, purge_audit_before

    maintenant = datetime.now(timezone.utc)
    vieille = (maintenant - timedelta(days=120)).strftime("%Y-%m-%d %H:%M:%S")
    recente = (maintenant - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
    _inserer_datee(audit_db, "vieille", vieille)
    _inserer_datee(audit_db, "recente", recente)

    assert purge_audit_before(cutoff_for_days(90), db=audit_db) == 1
    assert [e.action for e in get_audit_log(db=audit_db)] == ["recente"]
