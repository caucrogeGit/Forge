"""Contrat de rendu de littéraux SQL (DIALECT-LITERAL-001, ADR-075).

Teste les primitives cœur (`escape_string`, `render_literal_value`) et vérifie
que le contrat `Dialect` déclare `render_literal`. Le rendu propre à chaque
backend est testé dans son paquet.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from core.database.backend import Dialect
from core.database.literals import LiteralError, escape_string, render_literal_value


class TestEscapeString:

    def test_simple(self) -> None:
        assert escape_string("Lyon") == "'Lyon'"

    def test_doubles_single_quote(self) -> None:
        assert escape_string("l'ecole") == "'l''ecole'"

    def test_national_prefix(self) -> None:
        assert escape_string("Lyon", national=True) == "N'Lyon'"


def _render(value: object) -> str:
    return render_literal_value(
        value,
        bool_true="TRUE",
        bool_false="FALSE",
        render_string=escape_string,
        render_date=lambda d: f"D{d.isoformat()}",
        render_datetime=lambda dt: f"T{dt.isoformat()}",
    )


class TestRenderLiteralValue:

    def test_none_is_null(self) -> None:
        assert _render(None) == "NULL"

    def test_bool_before_int(self) -> None:
        # bool est un int : il doit être rendu comme booléen, pas comme 1/0 entier.
        assert _render(True) == "TRUE"
        assert _render(False) == "FALSE"

    def test_int(self) -> None:
        assert _render(42) == "42"

    def test_float_and_decimal(self) -> None:
        assert _render(3.5) == "3.5"
        assert _render(Decimal("3.50")) == "3.50"

    def test_string(self) -> None:
        assert _render("l'x") == "'l''x'"

    def test_datetime_before_date(self) -> None:
        # datetime est un date : le rendu datetime doit primer.
        assert _render(datetime(2026, 7, 11, 10, 0, 0)) == "T2026-07-11T10:00:00"
        assert _render(date(2026, 7, 11)) == "D2026-07-11"

    def test_unknown_type_raises(self) -> None:
        with pytest.raises(LiteralError):
            _render({"x": 1})


def test_dialect_protocol_declares_render_literal() -> None:
    assert hasattr(Dialect, "render_literal")
