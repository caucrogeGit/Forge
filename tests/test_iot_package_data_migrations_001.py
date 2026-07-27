"""Empaquetage de la migration IoT — OPTIN-DDL-IOT-001.

Ce fichier gardait auparavant l'empaquetage du `.sql` : présence sous
``forge_mvc_iot/migrations/``, déclaration dans
``[tool.setuptools.package-data]``, lisibilité via ``importlib.resources``
(ticket historique ``IOT-PACKAGE-DATA-MIGRATIONS-001``).

Le paquet ne livre plus de fichier SQL : il **déclare** sa table et le DDL est
rendu pour le backend installé. Le problème d'empaquetage disparaît donc de
lui-même, `tables.py` étant un module Python ordinaire, embarqué sans
configuration particulière. C'est une simplification, pas une régression : le
garde-fou historique visait précisément l'oubli de `package-data`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_iot")

PROJECT_ROOT = Path(__file__).parent.parent
IOT_PKG = PROJECT_ROOT / "packages" / "forge-mvc-iot"


def test_plus_aucun_sql_fige_livre() -> None:
    assert not list(IOT_PKG.rglob("*.sql")), (
        "forge-mvc-iot ne doit plus livrer de .sql (OPTIN-DDL-IOT-001)"
    )


def test_package_data_ne_declare_plus_de_sql() -> None:
    """Le besoin de `package-data` disparait avec le fichier."""
    content = (IOT_PKG / "pyproject.toml").read_text(encoding="utf-8")
    assert "migrations/*.sql" not in content


def test_la_declaration_voyage_comme_un_module_ordinaire() -> None:
    """Importable depuis la distribution, sans configuration d'empaquetage."""
    from forge_mvc_iot.tables import IOT_EVENTS, MIGRATIONS

    assert IOT_EVENTS.name == "iot_events"
    assert MIGRATIONS and MIGRATIONS[0][0].endswith("_create_iot_events.sql")


def test_le_doctor_trouve_la_declaration() -> None:
    from forge_mvc_iot.cli.doctor import check_migration_present

    result = check_migration_present()
    assert result.status == "ok", result.detail
