"""Garde-fou — ENTITIES-DEAD-CODE-REMOVE-001 : code mort retiré de relations.py.

L'audit 2026-07 a relevé que `packages/forge-mvc-entities/.../relations.py`
portait une directive `# pyright: reportUnusedFunction=false` masquant trois
fonctions jamais appelées (`_normalize_sql_type_for_fk`, `_resolve_entity_field`,
`_is_safe_sql_type`) et, avec elles, la dataclass `ResolvedEntityField` devenue
orpheline. Retrait pré-1.0. Ce garde interdit leur réapparition et vérifie que
la directive de suppression pyright n'est pas revenue (sinon du code mort
pourrait se réaccumuler sans que pyright ne le signale).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

pytest.importorskip("forge_mvc_entities")

import forge_mvc_entities.relations as relations

_SOURCE = Path(relations.__file__).read_text(encoding="utf-8")

_REMOVED_SYMBOLS = (
    "_normalize_sql_type_for_fk",
    "_resolve_entity_field",
    "_is_safe_sql_type",
    "ResolvedEntityField",
)


@pytest.mark.parametrize("symbol", _REMOVED_SYMBOLS)
def test_symbole_mort_absent_du_module(symbol: str):
    assert not hasattr(relations, symbol), (
        f"{symbol} doit rester supprimé de relations.py (ENTITIES-DEAD-CODE-REMOVE-001)."
    )


@pytest.mark.parametrize("symbol", _REMOVED_SYMBOLS)
def test_symbole_mort_absent_de_la_source(symbol: str):
    assert f"def {symbol}" not in _SOURCE and f"class {symbol}" not in _SOURCE, (
        f"la définition de {symbol} ne doit pas réapparaître dans relations.py."
    )


def test_directive_report_unused_function_absente():
    assert "reportUnusedFunction=false" not in _SOURCE, (
        "la directive pyright reportUnusedFunction=false ne doit pas revenir : "
        "elle masquerait une nouvelle accumulation de code mort."
    )
