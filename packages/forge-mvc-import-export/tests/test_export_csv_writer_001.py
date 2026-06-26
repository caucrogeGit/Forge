"""Export programmatique en CSV (IMPORT-OPTIN-SCAFFOLD-001). Tout en mémoire."""
from __future__ import annotations

import pytest

mod = pytest.importorskip("forge_mvc_import_export")

from forge_mvc_import_export import CsvImportError, parse_csv, to_csv


def test_to_csv_basic() -> None:
    rows = [{"nom": "Alice", "age": 12}, {"nom": "Bob", "age": 13}]
    out = to_csv(rows, ["nom", "age"])
    assert out == "nom,age\nAlice,12\nBob,13\n"


def test_column_order_is_respected() -> None:
    rows = [{"a": 1, "b": 2}]
    assert to_csv(rows, ["b", "a"]) == "b,a\n2,1\n"


def test_missing_or_none_becomes_empty() -> None:
    rows = [{"nom": "Alice", "age": None}, {"nom": "Bob"}]
    assert to_csv(rows, ["nom", "age"]) == "nom,age\nAlice,\nBob,\n"


def test_custom_delimiter() -> None:
    assert to_csv([{"a": 1}], ["a"], delimiter=";") == "a\n1\n"


def test_empty_columns_raises() -> None:
    with pytest.raises(CsvImportError):
        to_csv([{"a": 1}], [])


def test_roundtrip_parse_then_export() -> None:
    text = "nom,classe\nAlice,6A\nBob,6B\n"
    rows = parse_csv(text)
    assert to_csv(rows, ["nom", "classe"]) == text
