"""Rendu de littéraux SQL PostgreSQL (ADR-075)."""
from __future__ import annotations

from datetime import date, datetime

import pytest

pytest.importorskip("forge_mvc_postgres")
from forge_mvc_postgres.dialect import PostgreSQLDialect  # noqa: E402
from core.database.literals import LiteralError  # noqa: E402

D = PostgreSQLDialect()


@pytest.mark.parametrize("value, expected", [
    (None, "NULL"),
    (True, "TRUE"),
    (False, "FALSE"),
    (42, "42"),
    ("l'ecole", "'l''ecole'"),
    (date(2026, 7, 11), "DATE '2026-07-11'"),
    (datetime(2026, 7, 11, 10, 0, 0), "TIMESTAMP '2026-07-11 10:00:00'"),
])
def test_render_literal(value: object, expected: str) -> None:
    assert D.render_literal(value) == expected


def test_unknown_type_raises() -> None:
    with pytest.raises(LiteralError):
        D.render_literal(object())
