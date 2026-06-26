"""Scaffold du paquet forge-mvc-import (IMPORT-OPTIN-SCAFFOLD-001).

Garde-fous structurels : indépendance du cœur et dépendances minimales.
"""
from __future__ import annotations

from pathlib import Path

import pytest

forge_mvc_import = pytest.importorskip("forge_mvc_import")

PKG_ROOT = Path(forge_mvc_import.__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]


def test_core_n_importe_pas_le_paquet_import() -> None:
    core_dir = REPO_ROOT / "core"
    offenders: list[str] = []
    for path in core_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "import forge_mvc_import" in text or "from forge_mvc_import" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, f"le cœur ne doit pas importer forge_mvc_import : {offenders}"


def test_dependances_minimales() -> None:
    pyproject = (PKG_ROOT.parent / "pyproject.toml").read_text(encoding="utf-8")
    assert "forge-mvc>=" in pyproject
    # Import CSV pur stdlib : aucune dépendance lourde.
    for heavy in ("pandas", "openpyxl", "segno", "Pillow"):
        assert heavy not in pyproject, f"dépendance lourde inattendue : {heavy}"
