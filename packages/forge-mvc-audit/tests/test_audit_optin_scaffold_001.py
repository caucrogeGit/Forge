"""Scaffold du paquet forge-mvc-audit (AUDIT-OPTIN-SCAFFOLD-001).

Garde-fous structurels : indépendance du cœur, dépendances minimales, cohérence
entre le DDL rendu et la déclaration du paquet.
"""
from __future__ import annotations

from pathlib import Path

import pytest

forge_mvc_audit = pytest.importorskip("forge_mvc_audit")

from forge_mvc_audit import TABLE_NAME

PKG_ROOT = Path(forge_mvc_audit.__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]


def _rendered_ddl() -> str:
    """DDL de la table, rendu pour le backend actif.

    La constante de schéma du module est supprimée
    (`OPTIN-DDL-CONSTANTS-001`) : deux façons officielles de créer la même
    table contredisaient le principe 11. La source unique est la déclaration
    `forge_mvc_audit.tables`, rendue par le dialecte.
    """
    from core.database.backend import get_backend
    from core.database.table_ddl import render_create_table
    from forge_mvc_audit.tables import AUDIT_LOG

    return chr(10).join(render_create_table(AUDIT_LOG, get_backend().dialect))

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
    """Coherence entre la constante historique et le DDL rendu.

    La migration figee est remplacee par une declaration rendue par le
    dialecte (OPTIN-DDL-DIALECTAL) ; on compare donc au rendu MariaDB,
    dialecte de la constante. La constante elle-meme reste a convertir.
    """
    pytest.importorskip("forge_mvc_mariadb")
    from core.database.table_ddl import render_create_table
    from forge_mvc_mariadb.dialect import MariaDBDialect
    from forge_mvc_audit.tables import AUDIT_LOG

    sql = chr(10).join(render_create_table(AUDIT_LOG, MariaDBDialect()))
    assert f"CREATE TABLE IF NOT EXISTS {TABLE_NAME}" in sql
    assert f"CREATE TABLE IF NOT EXISTS {TABLE_NAME}" in _rendered_ddl()
    for column in ("actor", "action", "target_type", "target_id", "details", "created_at"):
        assert column in sql and column in _rendered_ddl()
