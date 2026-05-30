"""Branchement des routes de l'opt-in Forge IoT.

Délègue à l'**API publique** du paquet `forge-mvc-iot` : le code métier
vit dans le paquet, ce fichier ne fait que le brancher localement. Appelé
par ``optins/registry.py``.
"""

from __future__ import annotations

from forge_mvc_iot import register_iot_routes


def register(router) -> None:
    """Expose l'API HTTP IoT officielle (lecture seule) :

    - ``GET /api/iot/events``
    - ``GET /api/iot/events/{site}/{device_id}``
    - ``GET /api/iot/devices/{site}/{device_id}/count``
    """
    register_iot_routes(router)
