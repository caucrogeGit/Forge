"""Logique du store de paramètres (SETTINGS-OPTIN-SCAFFOLD-001).

Teste la sérialisation/coercition typée, l'upsert, la lecture, la suppression
et la validation des clés via un adapter DB **en mémoire** (pas de MariaDB).
Le contrat SQL réel est vérifié séparément par le test d'intégration `db`.
"""
from __future__ import annotations

from typing import Any

import pytest

forge_mvc_settings = pytest.importorskip("forge_mvc_settings")

from forge_mvc_settings import (
    SettingsError,
    delete_setting,
    get_all_settings,
    get_setting,
    set_setting,
)


class FakeDb:
    """Imite `core.database.db` (upsert ON DUPLICATE KEY) sur un dict."""

    def __init__(self) -> None:
        self.rows: dict[str, tuple[str, str]] = {}

    def execute(self, sql: str, params: Any = ()) -> int:
        if sql.startswith("INSERT INTO"):
            key, value, value_type = params
            self.rows[key] = (value, value_type)
            return 1
        if sql.startswith("DELETE FROM"):
            return 1 if self.rows.pop(params[0], None) is not None else 0
        return 0

    def fetch_one(self, sql: str, params: Any = ()) -> dict[str, Any] | None:
        row = self.rows.get(params[0])
        if row is None:
            return None
        return {"setting_value": row[0], "value_type": row[1]}

    def fetch_all(self, sql: str, params: Any = ()) -> list[dict[str, Any]]:
        return [
            {"setting_key": k, "setting_value": v, "value_type": t}
            for k, (v, t) in sorted(self.rows.items())
        ]


@pytest.fixture
def db() -> FakeDb:
    return FakeDb()


def test_set_then_get_str(db: FakeDb) -> None:
    set_setting("etablissement.nom", "Collège X", db=db)
    assert get_setting("etablissement.nom", db=db) == "Collège X"


@pytest.mark.parametrize(
    "value",
    [30, 0, -5, 3.14, True, False, "", "texte"],
)
def test_roundtrip_preserves_type_and_value(db: FakeDb, value: object) -> None:
    set_setting("k", value, db=db)  # type: ignore[arg-type]
    got = get_setting("k", db=db)
    assert got == value and type(got) is type(value)


def test_get_missing_returns_default(db: FakeDb) -> None:
    assert get_setting("absent", db=db) is None
    assert get_setting("absent", "repli", db=db) == "repli"


def test_set_is_upsert(db: FakeDb) -> None:
    set_setting("k", 1, db=db)
    set_setting("k", 2, db=db)
    assert get_setting("k", db=db) == 2
    assert len(db.rows) == 1


def test_get_all_settings_coerced_and_sorted(db: FakeDb) -> None:
    set_setting("b.int", 7, db=db)
    set_setting("a.bool", True, db=db)
    assert get_all_settings(db=db) == {"a.bool": True, "b.int": 7}


def test_delete_setting(db: FakeDb) -> None:
    set_setting("k", "v", db=db)
    assert delete_setting("k", db=db) is True
    assert delete_setting("k", db=db) is False
    assert get_setting("k", db=db) is None


@pytest.mark.parametrize("bad_key", ["", "1abc", "a b", "clé!", "_x", ".x", "x" * 200])
def test_invalid_key_raises(db: FakeDb, bad_key: str) -> None:
    with pytest.raises(SettingsError):
        set_setting(bad_key, "v", db=db)
    with pytest.raises(SettingsError):
        get_setting(bad_key, db=db)


@pytest.mark.parametrize("good_key", ["a", "qcm.session_duration", "x_y.z1", "A.B.C"])
def test_valid_keys_accepted(db: FakeDb, good_key: str) -> None:
    set_setting(good_key, "v", db=db)
    assert get_setting(good_key, db=db) == "v"


def test_unsupported_value_type_raises(db: FakeDb) -> None:
    with pytest.raises(SettingsError):
        set_setting("k", ["liste"], db=db)  # type: ignore[arg-type]
