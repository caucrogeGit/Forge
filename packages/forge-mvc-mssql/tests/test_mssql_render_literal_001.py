"""Rendu de littéraux SQL SQL Server (ADR-075)."""
from __future__ import annotations

from datetime import date, datetime

import pytest

pytest.importorskip("forge_mvc_mssql")
from forge_mvc_mssql.dialect import MSSQLDialect  # noqa: E402
from core.database.literals import LiteralError  # noqa: E402

D = MSSQLDialect()


@pytest.mark.parametrize("value, expected", [
    (None, "NULL"),
    (True, "1"),
    (False, "0"),
    (42, "42"),
    ("l'ecole", "N'l''ecole'"),
    (date(2026, 7, 11), "'2026-07-11'"),
    (datetime(2026, 7, 11, 10, 0, 0), "'2026-07-11 10:00:00'"),
])
def test_render_literal(value: object, expected: str) -> None:
    assert D.render_literal(value) == expected


def test_unknown_type_raises() -> None:
    with pytest.raises(LiteralError):
        D.render_literal(object())
