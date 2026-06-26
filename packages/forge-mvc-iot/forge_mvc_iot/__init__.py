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

Voir https://forgemvc.com/docs/forge/iot/architecture/ pour la
trajectoire d'ensemble.
"""

from __future__ import annotations

from forge_mvc_iot.http import register_iot_routes

__version__ = "1.0.0rc1"

__all__ = ["register_iot_routes"]
