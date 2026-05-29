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
    "DEFAULT_TLS_ENABLED",
    "ENV_HOST",
    "ENV_PORT",
    "ENV_TOPIC",
    "ENV_CLIENT_ID",
    "ENV_USERNAME",
    "ENV_PASSWORD",
    "ENV_API_TOKEN",
    "ENV_TLS_ENABLED",
    "ENV_TLS_CA_FILE",
    "IotConfig",
    "load_iot_config",
]

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 1883
DEFAULT_TOPIC = "forge/+/+/telemetry"
DEFAULT_CLIENT_ID = "forge-iot"
DEFAULT_TLS_ENABLED = False

ENV_HOST = "FORGE_IOT_MQTT_HOST"
ENV_PORT = "FORGE_IOT_MQTT_PORT"
ENV_TOPIC = "FORGE_IOT_MQTT_TOPIC"
ENV_CLIENT_ID = "FORGE_IOT_MQTT_CLIENT_ID"
ENV_USERNAME = "FORGE_IOT_MQTT_USERNAME"
ENV_PASSWORD = "FORGE_IOT_MQTT_PASSWORD"
ENV_API_TOKEN = "FORGE_IOT_API_TOKEN"
ENV_TLS_ENABLED = "FORGE_IOT_MQTT_TLS_ENABLED"
ENV_TLS_CA_FILE = "FORGE_IOT_MQTT_TLS_CA_FILE"

_PASSWORD_MASK = "***"

# Valeurs booléennes acceptées pour FORGE_IOT_MQTT_TLS_ENABLED (insensible
# à la casse). Une valeur vide vaut False ; toute autre valeur → ValueError.
_BOOL_TRUE_VALUES = frozenset({"true", "1", "yes", "on"})
_BOOL_FALSE_VALUES = frozenset({"false", "0", "no", "off"})


def _parse_bool(raw: str | None, *, var: str) -> bool:
    """Parse une variable booléenne d'environnement de façon stable.

    - ``None`` ou chaîne vide / espaces → ``False`` ;
    - ``true``/``1``/``yes``/``on`` (toute casse) → ``True`` ;
    - ``false``/``0``/``no``/``off`` (toute casse) → ``False`` ;
    - toute autre valeur → ``ValueError`` (message clair, sans la valeur
      brute si elle pouvait être sensible — ici ce n'est qu'un drapeau).
    """
    if raw is None:
        return False
    normalized = raw.strip().lower()
    if normalized == "":
        return False
    if normalized in _BOOL_TRUE_VALUES:
        return True
    if normalized in _BOOL_FALSE_VALUES:
        return False
    raise ValueError(
        f"{var} doit valoir true/1/yes/on ou false/0/no/off (vu : {raw!r})"
    )


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
    # MQTT over TLS (IOT-CONFIG-TLS-001). Désactivé par défaut : le mode
    # local pédagogique (Mosquitto en clair sur 1883) reste inchangé. Ces
    # champs ne sont **pas encore branchés** dans les clients MQTT — ce
    # ticket prépare uniquement la configuration ; le câblage paho
    # (``client.tls_set``) viendra dans IOT-MQTT-TLS-CLIENTS-001.
    mqtt_tls_enabled: bool = DEFAULT_TLS_ENABLED
    mqtt_tls_ca_file: str | None = None

    def __repr__(self) -> str:
        password_repr = repr(_PASSWORD_MASK) if self.mqtt_password else repr(None)
        token_repr = repr(_PASSWORD_MASK) if self.api_token else repr(None)
        # Le chemin du fichier CA peut désigner du matériel cryptographique :
        # on ne l'affiche pas en clair (masqué comme le mot de passe). Les
        # clients lisent l'attribut directement, pas le repr.
        ca_repr = repr(_PASSWORD_MASK) if self.mqtt_tls_ca_file else repr(None)
        return (
            "IotConfig("
            f"mqtt_host={self.mqtt_host!r}, "
            f"mqtt_port={self.mqtt_port!r}, "
            f"mqtt_topic={self.mqtt_topic!r}, "
            f"mqtt_client_id={self.mqtt_client_id!r}, "
            f"mqtt_username={self.mqtt_username!r}, "
            f"mqtt_password={password_repr}, "
            f"api_token={token_repr}, "
            f"mqtt_tls_enabled={self.mqtt_tls_enabled!r}, "
            f"mqtt_tls_ca_file={ca_repr}"
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
    - ``FORGE_IOT_MQTT_TLS_ENABLED`` non défini ou vide → ``False`` ;
      ``true``/``1``/``yes``/``on`` → ``True`` ; ``false``/``0``/``no``/
      ``off`` → ``False`` ; toute autre valeur → ``ValueError``.
    - ``FORGE_IOT_MQTT_TLS_CA_FILE`` non défini ou vide → ``None`` ;
      défini → chemin du certificat CA conservé tel quel.

    Note : ``mqtt_tls_enabled`` / ``mqtt_tls_ca_file`` sont **préparés**
    ici mais pas encore consommés par les clients MQTT
    (doctor/listen/simulate/subscriber) — voir IOT-MQTT-TLS-CLIENTS-001.
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

    tls_enabled = _parse_bool(env.get(ENV_TLS_ENABLED), var=ENV_TLS_ENABLED)
    tls_ca_file = env.get(ENV_TLS_CA_FILE) or None

    return IotConfig(
        mqtt_host=host,
        mqtt_port=port,
        mqtt_topic=topic,
        mqtt_client_id=client_id,
        mqtt_username=username,
        mqtt_password=password,
        api_token=api_token,
        mqtt_tls_enabled=tls_enabled,
        mqtt_tls_ca_file=tls_ca_file,
    )
