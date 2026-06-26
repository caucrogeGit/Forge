"""Lecture CSV en lignes de dictionnaires (IMPORT-OPTIN-SCAFFOLD-001)."""
from __future__ import annotations

import pytest

forge_mvc_import_export = pytest.importorskip("forge_mvc_import_export")

from forge_mvc_import_export import CsvImportError, parse_csv


def test_parse_simple() -> None:
    rows = parse_csv("nom,age\nAlice,12\nBob,13\n")
    assert rows == [{"nom": "Alice", "age": "12"}, {"nom": "Bob", "age": "13"}]


def test_header_is_stripped() -> None:
    rows = parse_csv(" nom , age \nAlice,12\n")
    assert rows == [{"nom": "Alice", "age": "12"}]


def test_blank_lines_are_ignored() -> None:
    rows = parse_csv("nom\nAlice\n\n\nBob\n")
    assert rows == [{"nom": "Alice"}, {"nom": "Bob"}]


def test_short_row_is_padded() -> None:
    rows = parse_csv("a,b,c\n1,2\n")
    assert rows == [{"a": "1", "b": "2", "c": ""}]


def test_custom_delimiter() -> None:
    rows = parse_csv("nom;age\nAlice;12\n", delimiter=";")
    assert rows == [{"nom": "Alice", "age": "12"}]


@pytest.mark.parametrize("bad", ["", "   ", "\n\n"])
def test_empty_csv_raises(bad: str) -> None:
    with pytest.raises(CsvImportError):
        parse_csv(bad)


def test_empty_header_column_raises() -> None:
    with pytest.raises(CsvImportError):
        parse_csv("nom,,age\nA,B,C\n")


def test_duplicate_header_raises() -> None:
    with pytest.raises(CsvImportError):
        parse_csv("nom,nom\nA,B\n")
