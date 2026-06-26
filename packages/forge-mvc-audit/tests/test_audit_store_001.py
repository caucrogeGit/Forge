"""Logique du store d'audit (AUDIT-OPTIN-SCAFFOLD-001).

Teste record_audit et la construction de requête de get_audit_log via un adapter
DB en mémoire qui capture les appels (pas de MariaDB). Le contrat SQL réel
(filtrage, ordre) est vérifié par le test d'intégration `db`.
"""
from __future__ import annotations

from typing import Any

import pytest

forge_mvc_audit = pytest.importorskip("forge_mvc_audit")

from forge_mvc_audit import AuditEntry, AuditError, get_audit_log, record_audit


class FakeDb:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.inserted: list[tuple[str, tuple[Any, ...]]] = []
        self._rows = rows or []
        self.last_sql: str = ""
        self.last_params: list[Any] = []
        self._next = 1

    def insert(self, sql: str, params: Any = ()) -> int:
        self.inserted.append((sql, tuple(params)))
        rid = self._next
        self._next += 1
        return rid

    def fetch_all(self, sql: str, params: Any = ()) -> list[dict[str, Any]]:
        self.last_sql = sql
        self.last_params = list(params)
        return self._rows


def test_record_audit_returns_id_and_binds_params() -> None:
    db = FakeDb()
    rid = record_audit("eleve.cree", actor="prof", target_type="eleve", target_id=42, db=db)
    assert rid == 1
    sql, params = db.inserted[0]
    assert "INSERT INTO audit_log" in sql
    assert params == ("prof", "eleve.cree", "eleve", "42", None)  # target_id stringifié


def test_record_audit_empty_action_raises() -> None:
    db = FakeDb()
    for bad in ("", "   "):
        with pytest.raises(AuditError):
            record_audit(bad, db=db)
    assert db.inserted == []


def test_get_audit_log_builds_filtered_query() -> None:
    db = FakeDb(rows=[])
    get_audit_log(action="note.modifiee", actor="prof", limit=5, db=db)
    assert "action = ?" in db.last_sql and "actor = ?" in db.last_sql
    assert "ORDER BY id DESC" in db.last_sql
    # filtres puis limit en dernier
    assert db.last_params == ["prof", "note.modifiee", 5]


def test_get_audit_log_no_filter_has_no_where() -> None:
    db = FakeDb(rows=[])
    get_audit_log(limit=10, db=db)
    assert "WHERE" not in db.last_sql
    assert db.last_params == [10]


def test_get_audit_log_caps_limit_to_max() -> None:
    db = FakeDb(rows=[])
    get_audit_log(limit=999999, db=db)
    assert db.last_params == [1000]  # MAX_LIMIT


def test_get_audit_log_invalid_limit_raises() -> None:
    db = FakeDb()
    for bad in (0, -1):
        with pytest.raises(AuditError):
            get_audit_log(limit=bad, db=db)


def test_get_audit_log_maps_rows_to_entries() -> None:
    db = FakeDb(rows=[
        {
            "id": 7, "actor": "prof", "action": "eleve.cree", "target_type": "eleve",
            "target_id": "42", "details": None, "created_at": "2026-06-26 12:00:00",
        }
    ])
    entries = get_audit_log(db=db)
    assert entries == [
        AuditEntry(
            id=7, actor="prof", action="eleve.cree", target_type="eleve",
            target_id="42", details=None, created_at="2026-06-26 12:00:00",
        )
    ]
