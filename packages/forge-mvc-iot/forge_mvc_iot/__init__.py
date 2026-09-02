# pyright: strict
"""Forge IoT — module opt-in pour la réception et l'exposition de données IoT.

L'API publique se construit ticket par ticket. À ce stade :

- ``forge_mvc_iot.config.load_iot_config`` — configuration MQTT
  (``IOT-CONFIG-001``).
- ``forge_mvc_iot.mqtt.subscriber.MqttSubscriber`` — subscriber MQTT
  (``IOT-MQTT-SUBSCRIBER-001``).
- ``forge_mvc_iot.storage.IotEventRepository`` — insertion + lectures
  (``IOT-STORAGE-REPOSITORY-001`` / ``IOT-STORAGE-REPOSITORY-READ-001``).
- ``forge_mvc_iot.http.register_iot_routes`` — branchement explicite
  des routes HTTP JSON (``IOT-HTTP-API-001``).
- ``forge_mvc_iot.tokens`` — jetons par site ou par équipement, le jeton
  d'environnement ouvrant seul TOUS les sites (``IOT-DEVICE-AUTH-001``).
- ``forge_mvc_iot.aggregates`` — moyenne, minimum et maximum sur une
  fenêtre (``IOT-AGGREGATES-001``).
- ``forge_mvc_iot.access`` — prise de contrôle d'accès applicatif, aucun
  opt-in n'important un autre (``IOT-RBAC-READ-001``).

Voir https://forgemvc.com/docs/forge/iot/architecture/ pour la
trajectoire d'ensemble.
"""

from __future__ import annotations

from forge_mvc_iot.access import (
    ACTION_READ_AGGREGATES,
    ACTION_READ_EVENTS,
    IOT_ACTIONS,
    clear_iot_permission_checks,
    is_read_allowed,
    register_iot_permission_check,
    registered_permission_checks,
    unregister_iot_permission_check,
)
from forge_mvc_iot.aggregates import (
    IotAggregate,
    IotAggregateError,
    aggregate_for_device,
    aggregate_for_site,
    window_start,
)
from forge_mvc_iot.http import register_iot_routes
from forge_mvc_iot.tokens import (
    GLOBAL_SCOPE,
    IotScope,
    IotTokenError,
    IotTokenRepository,
    generate_token,
    hash_token,
    looks_like_token,
)

__version__ = "1.0.0rc7"

__all__ = [
    "register_iot_routes",
    # Jetons par site ou par équipement (IOT-DEVICE-AUTH-001)
    "IotScope",
    "GLOBAL_SCOPE",
    "IotTokenRepository",
    "IotTokenError",
    "generate_token",
    "hash_token",
    "looks_like_token",
    # Agrégats sur une fenêtre (IOT-AGGREGATES-001)
    "IotAggregate",
    "IotAggregateError",
    "aggregate_for_device",
    "aggregate_for_site",
    "window_start",
    # Contrôle d'accès applicatif (IOT-RBAC-READ-001)
    "register_iot_permission_check",
    "unregister_iot_permission_check",
    "registered_permission_checks",
    "clear_iot_permission_checks",
    "is_read_allowed",
    "ACTION_READ_EVENTS",
    "ACTION_READ_AGGREGATES",
    "IOT_ACTIONS",
]
