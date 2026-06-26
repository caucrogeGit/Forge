"""Scaffold du paquet forge-mvc-settings (SETTINGS-OPTIN-SCAFFOLD-001).

Garde-fous structurels : indépendance du cœur, dépendances minimales,
cohérence entre `CREATE_TABLE_SQL` et la migration embarquée.
"""
from __future__ import annotations

from pathlib import Path

import pytest

forge_mvc_settings = pytest.importorskip("forge_mvc_settings")

from forge_mvc_settings import CREATE_TABLE_SQL, TABLE_NAME

PKG_ROOT = Path(forge_mvc_settings.__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]


def test_core_n_importe_pas_le_paquet_settings() -> None:
    core_dir = REPO_ROOT / "core"
    offenders: list[str] = []
    for path in core_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "import forge_mvc_settings" in text or "from forge_mvc_settings" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, f"le cœur ne doit pas importer forge_mvc_settings : {offenders}"


def test_dependances_minimales() -> None:
    pyproject = (PKG_ROOT.parent / "pyproject.toml").read_text(encoding="utf-8")
    # Seul forge-mvc est requis au runtime (pas de dépendance lourde).
    assert "forge-mvc>=" in pyproject
    assert "segno" not in pyproject and "Pillow" not in pyproject


def test_create_table_sql_coherent_avec_la_migration() -> None:
    migrations = list((PKG_ROOT / "migrations").glob("*.sql"))
    assert migrations, "au moins une migration .sql attendue"
    sql = migrations[0].read_text(encoding="utf-8")
    assert f"CREATE TABLE IF NOT EXISTS {TABLE_NAME}" in sql
    # La constante publique décrit la même table que la migration.
    assert f"CREATE TABLE IF NOT EXISTS {TABLE_NAME}" in CREATE_TABLE_SQL
    for column in ("setting_key", "setting_value", "value_type", "updated_at"):
        assert column in sql and column in CREATE_TABLE_SQL
