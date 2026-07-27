"""Scaffold du paquet forge-mvc-settings (SETTINGS-OPTIN-SCAFFOLD-001).

Garde-fous structurels : indépendance du cœur, dépendances minimales,
cohérence entre le DDL rendu et la déclaration du paquet.
"""
from __future__ import annotations

from pathlib import Path

import pytest

forge_mvc_settings = pytest.importorskip("forge_mvc_settings")

from forge_mvc_settings import TABLE_NAME

PKG_ROOT = Path(forge_mvc_settings.__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]


def _rendered_ddl() -> str:
    """DDL de la table, rendu pour le backend actif.

    La constante de schéma du module est supprimée
    (`OPTIN-DDL-CONSTANTS-001`) : deux façons officielles de créer la même
    table contredisaient le principe 11. La source unique est la déclaration
    `forge_mvc_settings.tables`, rendue par le dialecte.
    """
    from core.database.backend import get_backend
    from core.database.table_ddl import render_create_table
    from forge_mvc_settings.tables import APP_SETTINGS

    return chr(10).join(render_create_table(APP_SETTINGS, get_backend().dialect))

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
    """Coherence entre la constante historique et le DDL rendu.

    La migration figee est remplacee par une declaration rendue par le
    dialecte (OPTIN-DDL-DIALECTAL) ; on compare donc au rendu MariaDB,
    dialecte de la constante. La constante elle-meme reste a convertir.
    """
    pytest.importorskip("forge_mvc_mariadb")
    from core.database.table_ddl import render_create_table
    from forge_mvc_mariadb.dialect import MariaDBDialect
    from forge_mvc_settings.tables import APP_SETTINGS

    sql = chr(10).join(render_create_table(APP_SETTINGS, MariaDBDialect()))
    assert f"CREATE TABLE IF NOT EXISTS {TABLE_NAME}" in sql
    # La constante publique décrit la même table que la migration.
    assert f"CREATE TABLE IF NOT EXISTS {TABLE_NAME}" in _rendered_ddl()
    for column in ("setting_key", "setting_value", "value_type", "updated_at"):
        assert column in sql and column in _rendered_ddl()
