"""Scaffold du paquet forge-mvc-notifications (NOTIFICATIONS-OPTIN-SCAFFOLD-001)."""
from __future__ import annotations

from pathlib import Path

import pytest

forge_mvc_notifications = pytest.importorskip("forge_mvc_notifications")

from forge_mvc_notifications import CREATE_TABLE_SQL, TABLE_NAME

PKG_ROOT = Path(forge_mvc_notifications.__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]


def test_core_n_importe_pas_le_paquet_notifications() -> None:
    core_dir = REPO_ROOT / "core"
    offenders: list[str] = []
    for path in core_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "import forge_mvc_notifications" in text or "from forge_mvc_notifications" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, f"le cœur ne doit pas importer forge_mvc_notifications : {offenders}"


def test_dependances_minimales() -> None:
    pyproject = (PKG_ROOT.parent / "pyproject.toml").read_text(encoding="utf-8")
    assert "forge-mvc>=" in pyproject
    # Stockage in-app pur : pas de dépendance sur jobs/mail au niveau paquet.
    assert "forge-mvc-jobs" not in pyproject and "forge-mvc-mail" not in pyproject


def test_create_table_sql_coherent_avec_la_migration() -> None:
    migrations = list((PKG_ROOT / "migrations").glob("*.sql"))
    assert migrations, "au moins une migration .sql attendue"
    sql = migrations[0].read_text(encoding="utf-8")
    assert f"CREATE TABLE IF NOT EXISTS {TABLE_NAME}" in sql
    assert f"CREATE TABLE IF NOT EXISTS {TABLE_NAME}" in CREATE_TABLE_SQL
    for column in ("recipient", "type", "message", "data", "read_at", "created_at"):
        assert column in sql and column in CREATE_TABLE_SQL
