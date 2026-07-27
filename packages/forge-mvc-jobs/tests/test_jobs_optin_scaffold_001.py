"""Scaffold du paquet forge-mvc-jobs (JOBS-OPTIN-SCAFFOLD-001).

Garde-fous structurels : indépendance du cœur, dépendances minimales, cohérence
entre `CREATE_TABLE_SQL` et la migration embarquée.
"""
from __future__ import annotations

from pathlib import Path

import pytest

forge_mvc_jobs = pytest.importorskip("forge_mvc_jobs")

from forge_mvc_jobs import CREATE_TABLE_SQL, TABLE_NAME

PKG_ROOT = Path(forge_mvc_jobs.__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]


def test_core_n_importe_pas_le_paquet_jobs() -> None:
    core_dir = REPO_ROOT / "core"
    offenders: list[str] = []
    for path in core_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "import forge_mvc_jobs" in text or "from forge_mvc_jobs" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, f"le cœur ne doit pas importer forge_mvc_jobs : {offenders}"


def test_dependances_minimales() -> None:
    pyproject = (PKG_ROOT.parent / "pyproject.toml").read_text(encoding="utf-8")
    assert "forge-mvc>=" in pyproject
    # File pur MariaDB : pas de broker ni de dépendance lourde.
    for heavy in ("celery", "redis", "rq", "kombu"):
        assert heavy not in pyproject, f"dépendance lourde inattendue : {heavy}"


def test_create_table_sql_coherent_avec_la_migration() -> None:
    """Coherence entre la constante historique et le DDL rendu.

    La migration figee est remplacee par une declaration rendue par le
    dialecte (OPTIN-DDL-DIALECTAL) ; on compare donc au rendu MariaDB,
    dialecte de la constante. La constante elle-meme reste a convertir.
    """
    pytest.importorskip("forge_mvc_mariadb")
    from core.database.table_ddl import render_create_table
    from forge_mvc_mariadb.dialect import MariaDBDialect
    from forge_mvc_jobs.tables import JOBS

    sql = chr(10).join(render_create_table(JOBS, MariaDBDialect()))
    assert f"CREATE TABLE IF NOT EXISTS {TABLE_NAME}" in sql
    assert f"CREATE TABLE IF NOT EXISTS {TABLE_NAME}" in CREATE_TABLE_SQL
    for column in ("queue", "task", "payload", "status", "attempts", "claim_token", "available_at"):
        assert column in sql and column in CREATE_TABLE_SQL
