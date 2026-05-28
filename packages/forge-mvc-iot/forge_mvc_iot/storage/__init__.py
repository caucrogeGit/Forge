"""Stockage des événements IoT.

API publique du sous-package :

- ``COLUMNS``, ``TABLE_NAME``, ``INSERT_IOT_EVENT_SQL`` — constantes du
  contrat SQL (``IOT-STORAGE-EVENTS-001``).
- ``serialize_measurement_for_storage``, ``build_insert_iot_event_sql``
  — fonctions pures de sérialisation (``IOT-STORAGE-EVENTS-001``).
- ``IotEventRepository``, ``DbAdapter`` — repository et protocole
  d'adapter (``IOT-STORAGE-REPOSITORY-001``).
"""

from __future__ import annotations

from forge_mvc_iot.storage.events import (
    COLUMNS,
    INSERT_IOT_EVENT_SQL,
    TABLE_NAME,
    build_insert_iot_event_sql,
    serialize_measurement_for_storage,
)
from forge_mvc_iot.storage.repository import (
    COUNT_IOT_EVENTS_BY_DEVICE_SQL,
    DEFAULT_LIMIT,
    MAX_LIMIT,
    SELECT_IOT_EVENTS_BY_DEVICE_SQL,
    SELECT_IOT_EVENTS_RECENT_SQL,
    DbAdapter,
    IotEventRepository,
)

__all__ = [
    "COLUMNS",
    "COUNT_IOT_EVENTS_BY_DEVICE_SQL",
    "DEFAULT_LIMIT",
    "DbAdapter",
    "INSERT_IOT_EVENT_SQL",
    "IotEventRepository",
    "MAX_LIMIT",
    "SELECT_IOT_EVENTS_BY_DEVICE_SQL",
    "SELECT_IOT_EVENTS_RECENT_SQL",
    "TABLE_NAME",
    "build_insert_iot_event_sql",
    "serialize_measurement_for_storage",
]
