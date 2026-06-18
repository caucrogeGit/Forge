# pyright: strict
"""Application de la configuration TLS MQTT — IOT-MQTT-TLS-CLIENTS-001.

Helper **centralisé** consommé par les trois clients MQTT Forge IoT
(``MqttSubscriber``, ``forge iot:doctor --mqtt``, ``forge iot:simulate``)
afin de brancher la configuration TLS préparée par ``IOT-CONFIG-TLS-001``
(``mqtt_tls_enabled`` / ``mqtt_tls_ca_file``) une seule fois et de la
tester une seule fois.

Ce module est **pur** : il ne dépend pas de ``paho-mqtt`` (le client est
injecté), ne se connecte à aucun broker et n'écrit rien. Il appelle
seulement ``client.tls_set(...)`` quand TLS est activé.

Règles (alignées sur le ticket) :

- TLS désactivé (``mqtt_tls_enabled is False``) → **rien** n'est fait,
  le comportement historique (connexion en clair) est strictement
  préservé ;
- TLS activé + ``mqtt_tls_ca_file`` défini → ``client.tls_set(ca_certs=...)``
  (le broker est validé contre ce CA) ;
- TLS activé sans CA explicite → ``client.tls_set()`` (paho utilise les
  certificats système si disponibles) ;
- **jamais** de ``tls_insecure_set(True)``, pas de certificat client
  (mTLS), pas de forçage du port — l'utilisateur configure
  ``FORGE_IOT_MQTT_PORT=8883`` lui-même ;
- le chemin du CA n'est **pas** journalisé ici (politique de masquage du
  ``repr(IotConfig)`` conservée).

``configure_tls`` doit être appelée **avant** ``client.connect(...)``.
"""

from __future__ import annotations

from typing import Any

from forge_mvc_iot.config import IotConfig

__all__ = ["configure_tls"]


def configure_tls(client: Any, config: IotConfig) -> None:
    """Applique la configuration TLS de ``config`` sur ``client`` paho.

    No-op si ``config.mqtt_tls_enabled`` est faux. Sinon appelle
    ``client.tls_set`` (avec ``ca_certs`` si un fichier CA est configuré).
    À appeler avant ``client.connect(...)``.
    """
    if not config.mqtt_tls_enabled:
        return

    if config.mqtt_tls_ca_file:
        client.tls_set(ca_certs=config.mqtt_tls_ca_file)
    else:
        client.tls_set()
