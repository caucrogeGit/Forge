"""Scaffold du paquet forge-mvc-audit (AUDIT-OPTIN-SCAFFOLD-001).

Garde-fous structurels : indépendance du cœur, dépendances minimales, cohérence
entre `CREATE_TABLE_SQL` et la migration embarquée.
"""
from __future__ import annotations

from pathlib import Path

import pytest

forge_mvc_audit = pytest.importorskip("forge_mvc_audit")

from forge_mvc_audit import CREATE_TABLE_SQL, TABLE_NAME

PKG_ROOT = Path(forge_mvc_audit.__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]


def test_core_n_importe_pas_le_paquet_audit() -> None:
    core_dir = REPO_ROOT / "core"
    offenders: list[str] = []
    for path in core_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "import forge_mvc_audit" in text or "from forge_mvc_audit" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, f"le cœur ne doit pas importer forge_mvc_audit : {offenders}"


def test_dependances_minimales() -> None:
    pyproject = (PKG_ROOT.parent / "pyproject.toml").read_text(encoding="utf-8")
    assert "forge-mvc>=" in pyproject
    assert "segno" not in pyproject and "Pillow" not in pyproject


def test_create_table_sql_coherent_avec_la_migration() -> None:
    migrations = list((PKG_ROOT / "migrations").glob("*.sql"))
    assert migrations, "au moins une migration .sql attendue"
    sql = migrations[0].read_text(encoding="utf-8")
    assert f"CREATE TABLE IF NOT EXISTS {TABLE_NAME}" in sql
    assert f"CREATE TABLE IF NOT EXISTS {TABLE_NAME}" in CREATE_TABLE_SQL
    for column in ("actor", "action", "target_type", "target_id", "details", "created_at"):
        assert column in sql and column in CREATE_TABLE_SQL
