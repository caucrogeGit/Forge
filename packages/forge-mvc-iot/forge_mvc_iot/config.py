"""Configuration Forge IoT — itération 1.

Charge la configuration MQTT du module IoT depuis un mapping
(``os.environ`` par défaut, ou un dict injecté pour les tests).

Ce module est **pur** : il ne se connecte à aucun broker, n'importe pas
``paho-mqtt`` et n'écrit nulle part. Il fixe uniquement le contrat de
configuration.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "DEFAULT_TOPIC",
    "DEFAULT_CLIENT_ID",
    "ENV_HOST",
    "ENV_PORT",
    "ENV_TOPIC",
    "ENV_CLIENT_ID",
    "ENV_USERNAME",
    "ENV_PASSWORD",
    "ENV_API_TOKEN",
    "IotConfig",
    "load_iot_config",
]

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 1883
DEFAULT_TOPIC = "forge/+/+/telemetry"
DEFAULT_CLIENT_ID = "forge-iot"

ENV_HOST = "FORGE_IOT_MQTT_HOST"
ENV_PORT = "FORGE_IOT_MQTT_PORT"
ENV_TOPIC = "FORGE_IOT_MQTT_TOPIC"
ENV_CLIENT_ID = "FORGE_IOT_MQTT_CLIENT_ID"
ENV_USERNAME = "FORGE_IOT_MQTT_USERNAME"
ENV_PASSWORD = "FORGE_IOT_MQTT_PASSWORD"
ENV_API_TOKEN = "FORGE_IOT_API_TOKEN"

_PASSWORD_MASK = "***"


@dataclass(frozen=True)
class IotConfig:
    """Configuration immuable du module Forge IoT.

    Le mot de passe MQTT est masqué dans ``repr()`` afin de ne pas
    fuiter dans les logs, les traces d'exception ou les sorties de
    debug accidentelles.
    """

    mqtt_host: str
    mqtt_port: int
    mqtt_topic: str
    mqtt_client_id: str
    mqtt_username: str | None
    mqtt_password: str | None
    # API HTTP : token Bearer optionnel. Champ avec défaut (dernier) pour
    # rester compatible avec les instanciations existantes à 6 champs.
    api_token: str | None = None

    def __repr__(self) -> str:
        password_repr = repr(_PASSWORD_MASK) if self.mqtt_password else repr(None)
        token_repr = repr(_PASSWORD_MASK) if self.api_token else repr(None)
        return (
            "IotConfig("
            f"mqtt_host={self.mqtt_host!r}, "
            f"mqtt_port={self.mqtt_port!r}, "
            f"mqtt_topic={self.mqtt_topic!r}, "
            f"mqtt_client_id={self.mqtt_client_id!r}, "
            f"mqtt_username={self.mqtt_username!r}, "
            f"mqtt_password={password_repr}, "
            f"api_token={token_repr}"
            ")"
        )


def load_iot_config(env: Mapping[str, str] | None = None) -> IotConfig:
    """Charge la configuration IoT depuis un mapping environnement.

    Si ``env`` vaut ``None``, lit ``os.environ``. Sinon, lit le mapping
    fourni — utile pour les tests, qui injectent un dict explicite.

    Règles :

    - ``FORGE_IOT_MQTT_HOST`` non défini → ``"localhost"`` ;
      défini mais vide → ``ValueError``.
    - ``FORGE_IOT_MQTT_PORT`` non défini ou vide → ``1883`` ;
      défini mais non convertible en entier → ``ValueError`` ;
      hors plage ``1..65535`` → ``ValueError``.
    - ``FORGE_IOT_MQTT_TOPIC`` non défini → ``"forge/+/+/telemetry"`` ;
      défini mais vide → ``ValueError``.
    - ``FORGE_IOT_MQTT_CLIENT_ID`` non défini ou vide → ``"forge-iot"``.
    - ``FORGE_IOT_MQTT_USERNAME`` non défini ou vide → ``None``.
    - ``FORGE_IOT_MQTT_PASSWORD`` non défini ou vide → ``None``.
    - ``FORGE_IOT_API_TOKEN`` non défini ou vide → ``None`` (API HTTP
      ouverte) ; défini → token Bearer requis sur les routes IoT.
    """
    if env is None:
        env = os.environ

    host = env.get(ENV_HOST, DEFAULT_HOST)
    if not host:
        raise ValueError(f"{ENV_HOST} ne peut pas être vide")

    port_raw = env.get(ENV_PORT)
    if port_raw is None or port_raw == "":
        port = DEFAULT_PORT
    else:
        try:
            port = int(port_raw)
        except ValueError as exc:
            raise ValueError(
                f"{ENV_PORT} doit être un entier (vu : {port_raw!r})"
            ) from exc
    if port < 1 or port > 65535:
        raise ValueError(f"{ENV_PORT} hors plage 1-65535 (vu : {port})")

    topic = env.get(ENV_TOPIC, DEFAULT_TOPIC)
    if not topic:
        raise ValueError(f"{ENV_TOPIC} ne peut pas être vide")

    client_id = env.get(ENV_CLIENT_ID) or DEFAULT_CLIENT_ID

    username = env.get(ENV_USERNAME) or None
    password = env.get(ENV_PASSWORD) or None
    api_token = env.get(ENV_API_TOKEN) or None

    return IotConfig(
        mqtt_host=host,
        mqtt_port=port,
        mqtt_topic=topic,
        mqtt_client_id=client_id,
        mqtt_username=username,
        mqtt_password=password,
        api_token=api_token,
    )
