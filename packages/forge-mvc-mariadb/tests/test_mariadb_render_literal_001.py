"""Rendu de littéraux SQL MariaDB (ADR-075)."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

pytest.importorskip("forge_mvc_mariadb")
from forge_mvc_mariadb.dialect import MariaDBDialect  # noqa: E402
from core.database.literals import LiteralError  # noqa: E402

D = MariaDBDialect()


@pytest.mark.parametrize("value, expected", [
    (None, "NULL"),
    (True, "1"),
    (False, "0"),
    (42, "42"),
    (Decimal("3.50"), "3.50"),
    ("l'ecole", "'l''ecole'"),
    (date(2026, 7, 11), "'2026-07-11'"),
    (datetime(2026, 7, 11, 10, 0, 0), "'2026-07-11 10:00:00'"),
])
def test_render_literal(value: object, expected: str) -> None:
    assert D.render_literal(value) == expected


def test_unknown_type_raises() -> None:
    with pytest.raises(LiteralError):
        D.render_literal(object())
