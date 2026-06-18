# pyright: strict
"""Subscriber MQTT Forge IoT — pont vers ``paho-mqtt``.

Ce module branche le contrat documenté (``contract.py``) sur un client
``paho.mqtt.client.Client``. Le code de transport est isolé du code de
parsing pour rester testable sans broker : la méthode publique
:py:meth:`MqttSubscriber.handle_message` peut être appelée directement
avec un topic et un payload, et les tests injectent un client factice
via ``client_factory``.

Hors périmètre de ce ticket : stockage SQL, route HTTP, TLS, downlink.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from forge_mvc_iot.config import IotConfig
from forge_mvc_iot.mqtt.contract import (
    ContractError,
    Measurement,
    parse_message,
)
from forge_mvc_iot.mqtt.tls import configure_tls

__all__ = [
    "OnMeasurement",
    "OnContractError",
    "MqttSubscriber",
]

logger = logging.getLogger(__name__)

OnMeasurement = Callable[[Measurement], None]
"""Callback appelé pour chaque mesure valide reçue."""

OnContractError = Callable[[ContractError, str, bytes], None]
"""Callback optionnel pour les violations de contrat — reçoit l'erreur,
le topic brut et le payload brut."""


def _default_client_factory(config: IotConfig) -> Any:
    """Construit le client paho-mqtt par défaut.

    Importé paresseusement pour que les tests qui injectent un autre
    ``client_factory`` n'aient pas besoin de ``paho-mqtt`` installé.
    """
    import paho.mqtt.client as mqtt  # noqa: PLC0415

    return mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,  # pyright: ignore[reportPrivateImportUsage]
        client_id=config.mqtt_client_id,
    )


class MqttSubscriber:
    """Subscriber MQTT Forge IoT.

    Branche un client ``paho-mqtt`` sur le topic configuré et délègue
    chaque message reçu à :py:meth:`handle_message`, qui applique le
    contrat (``forge_mvc_iot.mqtt.contract``) et appelle le callback
    fourni.

    Parameters
    ----------
    config:
        Configuration immuable produite par ``load_iot_config``.
    on_measurement:
        Callback appelé pour chaque mesure valide.
    on_contract_error:
        Callback optionnel pour les violations de contrat. Si ``None``,
        l'erreur est uniquement loguée (niveau ``WARNING``).
    client_factory:
        Fabrique de client MQTT. Par défaut, instancie un
        ``paho.mqtt.client.Client``. Les tests peuvent injecter une
        fabrique qui retourne un ``Mock`` pour vérifier les appels sans
        broker.
    """

    def __init__(
        self,
        config: IotConfig,
        on_measurement: OnMeasurement,
        on_contract_error: OnContractError | None = None,
        client_factory: Callable[[IotConfig], Any] | None = None,
    ) -> None:
        self.config = config
        self.on_measurement = on_measurement
        self.on_contract_error = on_contract_error

        factory = client_factory or _default_client_factory
        self.client = factory(config)

        # TLS (si activé) doit être configuré avant connect().
        configure_tls(self.client, config)

        if config.mqtt_username:
            self.client.username_pw_set(
                config.mqtt_username,
                config.mqtt_password,
            )

        self.client.on_connect = self._on_paho_connect
        self.client.on_message = self._on_paho_message

    # ── Méthode publique testable sans broker ───────────────────────────────

    def handle_message(self, topic: str, payload: bytes | str) -> None:
        """Applique le contrat sur un message reçu.

        Cette méthode est volontairement publique : elle constitue le
        point d'entrée testable du subscriber. Les tests appellent
        ``subscriber.handle_message(topic, payload)`` directement, sans
        instancier un broker.
        """
        try:
            measurement = parse_message(topic, payload)
        except ContractError as exc:
            logger.warning(
                "Forge IoT — violation de contrat MQTT [%s] sur %r : %s",
                exc.code,
                topic,
                exc.message,
            )
            if self.on_contract_error is not None:
                payload_bytes = (
                    payload if isinstance(payload, bytes)
                    else payload.encode("utf-8", errors="replace")
                )
                self.on_contract_error(exc, topic, payload_bytes)
            return

        self.on_measurement(measurement)

    # ── Callbacks paho-mqtt ─────────────────────────────────────────────────

    def _on_paho_connect(
        self,
        client: Any,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any = None,
    ) -> None:
        # paho-mqtt 2.x — CallbackAPIVersion.VERSION2.
        # reason_code 0 (ou Success) = OK.
        if int(reason_code) != 0:
            logger.warning(
                "Forge IoT — échec de connexion MQTT : reason_code=%s",
                reason_code,
            )
            return
        client.subscribe(self.config.mqtt_topic)
        logger.info(
            "Forge IoT — abonné à %r sur %s:%s",
            self.config.mqtt_topic,
            self.config.mqtt_host,
            self.config.mqtt_port,
        )

    def _on_paho_message(self, client: Any, userdata: Any, message: Any) -> None:
        self.handle_message(message.topic, message.payload)

    # ── Cycle de vie ────────────────────────────────────────────────────────

    def connect(self) -> None:
        """Ouvre la connexion vers le broker."""
        self.client.connect(self.config.mqtt_host, self.config.mqtt_port)

    def disconnect(self) -> None:
        """Ferme la connexion vers le broker."""
        self.client.disconnect()

    def loop_forever(self) -> None:
        """Boucle bloquante (utile pour un script ou un service)."""
        self.client.loop_forever()

    def loop_start(self) -> None:
        """Démarre la boucle réseau dans un thread séparé."""
        self.client.loop_start()

    def loop_stop(self) -> None:
        """Arrête la boucle réseau démarrée par ``loop_start``."""
        self.client.loop_stop()
