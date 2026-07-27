"""Intégration réelle de IotEventRepository contre MariaDB (audit tests).

Le repository d'événements IoT n'était testé qu'avec un faux connecteur capturant
le SQL. Ces tests exercent le VRAI repository (INSERT/SELECT/COUNT via
`core.database.db`) contre une MariaDB réelle : insertion d'une mesure, lecture
récente, filtre par device, comptage. La table `iot_events` est provisionnée
depuis le DDL réellement livré par la migration du paquet.

Marqués `db` : sautés en local sans base, imposés en CI.
"""
from __future__ import annotations


import pytest

pytestmark = pytest.mark.db

forge_mvc_iot = pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.mqtt.contract import Measurement
from forge_mvc_iot.storage.repository import IotEventRepository


def _ddl_statements() -> list[str]:
    """DDL de la table iot_events, rendu pour le backend actif.

    Le paquet ne livre plus de .sql fige (OPTIN-DDL-IOT-001) : la table est
    declaree une fois et rendue par le dialecte. Le test d'integration profite
    au passage d'un DDL correct sur les quatre backends.
    """
    from core.database.backend import get_backend
    from core.database.table_ddl import render_create_table
    from forge_mvc_iot.tables import IOT_EVENTS

    statements = render_create_table(IOT_EVENTS, get_backend().dialect)
    return [stmt.strip().rstrip(";") for stmt in statements if stmt.strip()]


@pytest.fixture()
def iot_table(real_db):
    from core.database import db

    db.execute("DROP TABLE IF EXISTS iot_events", ())
    for statement in _ddl_statements():
        db.execute(statement, ())
    yield db
    db.execute("DROP TABLE IF EXISTS iot_events", ())


def _measure(**over) -> Measurement:
    base = dict(site="atelier", device_id="esp32-001", kind="temperature",
                value=22.4, unit="C", timestamp="2026-05-28T10:00:00Z", metadata=None)
    base.update(over)
    return Measurement(**base)


def test_insert_and_read_recent(iot_table):
    repo = IotEventRepository()
    repo.insert(_measure(value=21.0))
    repo.insert(_measure(device_id="esp32-002", value=25.5))
    recent = repo.list_recent(limit=10)
    assert len(recent) == 2
    assert {e["value"] for e in recent} == {21.0, 25.5}


def test_find_and_count_by_device(iot_table):
    repo = IotEventRepository()
    repo.insert(_measure(device_id="esp32-001"))
    repo.insert(_measure(device_id="esp32-001", value=23.0))
    repo.insert(_measure(device_id="esp32-002"))
    assert repo.count_by_device("atelier", "esp32-001") == 2
    assert repo.count_by_device("atelier", "esp32-002") == 1
    found = repo.find_by_device("atelier", "esp32-001", limit=10)
    assert len(found) == 2
    assert all(e["device_id"] == "esp32-001" for e in found)


def test_row_columns_persisted(iot_table):
    db = iot_table
    IotEventRepository().insert(_measure(kind="humidity", value=48.0, unit="pct"))
    row = db.fetch_one("SELECT site, device_id, kind, value, unit FROM iot_events LIMIT 1", ())
    assert row["site"] == "atelier"
    assert row["kind"] == "humidity"
    assert row["value"] == 48.0
    assert row["unit"] == "pct"
