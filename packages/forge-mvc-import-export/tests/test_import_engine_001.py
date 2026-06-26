"""Moteur d'import : validation, rapport, insertion (IMPORT-OPTIN-SCAFFOLD-001).

Tout en mémoire (insert simulé par une liste), aucune base requise.
"""
from __future__ import annotations

import pytest

forge_mvc_import_export = pytest.importorskip("forge_mvc_import_export")

from forge_mvc_import_export import (
    CsvImportError,
    FieldSpec,
    coerce_bool,
    coerce_int,
    import_rows,
)


def _collector() -> tuple[list[dict[str, object]], object]:
    rows: list[dict[str, object]] = []
    return rows, rows.append


def test_all_valid_rows_are_inserted() -> None:
    inserted, insert = _collector()
    rows = [{"nom": "Alice", "age": "12"}, {"nom": "Bob", "age": "13"}]
    specs = [FieldSpec("nom"), FieldSpec("age", coerce=coerce_int)]
    report = import_rows(rows, specs, insert)
    assert report.ok and report.imported == 2
    assert inserted == [{"nom": "Alice", "age": 12}, {"nom": "Bob", "age": 13}]


def test_missing_required_blocks_everything_by_default() -> None:
    inserted, insert = _collector()
    rows = [{"nom": "Alice"}, {"nom": ""}]
    report = import_rows(rows, [FieldSpec("nom")], insert)
    assert report.imported == 0          # tout ou rien
    assert inserted == []
    assert [(e.row, e.field) for e in report.errors] == [(2, "nom")]


def test_partial_inserts_valid_rows_despite_errors() -> None:
    inserted, insert = _collector()
    rows = [{"nom": "Alice"}, {"nom": ""}, {"nom": "Carol"}]
    report = import_rows(rows, [FieldSpec("nom")], insert, partial=True)
    assert report.imported == 2
    assert inserted == [{"nom": "Alice"}, {"nom": "Carol"}]
    assert len(report.errors) == 1 and report.errors[0].row == 2


def test_bad_coercion_is_reported() -> None:
    inserted, insert = _collector()
    rows = [{"nom": "Alice", "age": "douze"}]
    report = import_rows(rows, [FieldSpec("nom"), FieldSpec("age", coerce=coerce_int)], insert)
    assert report.imported == 0
    assert report.errors[0].field == "age" and "invalide" in report.errors[0].message


def test_optional_empty_becomes_none() -> None:
    inserted, insert = _collector()
    rows = [{"nom": "Alice", "age": ""}]
    report = import_rows(rows, [FieldSpec("nom"), FieldSpec("age", required=False, coerce=coerce_int)], insert)
    assert report.ok and inserted == [{"nom": "Alice", "age": None}]


def test_insert_exception_is_captured() -> None:
    def boom(_row: dict[str, object]) -> object:
        raise RuntimeError("doublon")

    rows = [{"nom": "Alice"}]
    report = import_rows(rows, [FieldSpec("nom")], boom)
    assert report.imported == 0
    assert report.errors[0].row == 1 and "insertion échouée" in report.errors[0].message


def test_bool_coercion() -> None:
    inserted, insert = _collector()
    rows = [{"actif": "oui"}, {"actif": "0"}]
    report = import_rows(rows, [FieldSpec("actif", coerce=coerce_bool)], insert)
    assert report.ok and inserted == [{"actif": True}, {"actif": False}]


def test_empty_specs_raises() -> None:
    with pytest.raises(CsvImportError):
        import_rows([{"a": "1"}], [], lambda _row: None)
