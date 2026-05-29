"""Commande ``forge iot:listen`` — IOT-SUBSCRIBER-CLI-001.

Relie les briques existantes en un flux local utilisable ::

    Mosquitto → forge iot:listen → MqttSubscriber
    → IotEventRepository.insert() → iot_events

Elle :

- charge la configuration via ``load_iot_config()`` ;
- crée un ``IotEventRepository`` ;
- crée un ``MqttSubscriber`` branché sur ``repository.insert`` ;
- affiche chaque mesure reçue ;
- reste active jusqu'à ``Ctrl+C`` et s'arrête proprement.

C'est une commande de **développement / pédagogie**, pas un service de
production : pas de daemon, pas de retry/backoff, pas de batch, pas de
multi-thread storage. On s'arrête au **premier échec base** (plus simple
et plus parlant en atelier).

``paho-mqtt`` et ``core.database`` ne sont importés que lorsque la
commande est réellement lancée (imports paresseux via le subscriber et
le repository).
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

__all__ = [
    "run_listener",
    "main",
]

# Code d'erreur MariaDB « table absente » (ER_NO_SUCH_TABLE).
_MARIADB_TABLE_NOT_FOUND_ERRNO = 1146


def _is_storage_missing(exc: Exception) -> bool:
    """Détecte une erreur « table ``iot_events`` absente ».

    Reconnaît ``errno == 1146`` (MariaDB) ou ``"doesn't exist"`` dans le
    message (filet de sécurité si l'exception est wrappée).
    """
    if getattr(exc, "errno", None) == _MARIADB_TABLE_NOT_FOUND_ERRNO:
        return True
    return "doesn't exist" in str(exc).lower()


class _StorageListener:
    """Branche les mesures reçues sur ``repository.insert``.

    Affiche un ``[OK]`` par mesure persistée. Au premier échec base, émet
    un message pédagogique, mémorise l'erreur et **demande l'arrêt** du
    subscriber (``disconnect``) — la commande sort alors en erreur.
    """

    def __init__(self, repository: Any) -> None:
        self.repository = repository
        self.storage_error: Exception | None = None
        # Renseigné par ``run_listener`` après la construction du
        # subscriber (le callback a besoin d'une référence pour demander
        # l'arrêt depuis l'intérieur de la boucle réseau).
        self.subscriber: Any | None = None

    def on_measurement(self, measurement: Any) -> None:
        try:
            self.repository.insert(measurement)
        except Exception as exc:  # noqa: BLE001 — on classe ci-dessous
            self.storage_error = exc
            if _is_storage_missing(exc):
                print("[ERREUR] Stockage IoT indisponible.", file=sys.stderr)
                print(
                    "Conseil : lance forge iot:init puis forge migration:apply",
                    file=sys.stderr,
                )
            else:
                # Message sobre : type d'erreur, pas de stacktrace.
                print(
                    f"[ERREUR] Insertion en base impossible — "
                    f"{type(exc).__name__}",
                    file=sys.stderr,
                )
            if self.subscriber is not None:
                # Fait retourner loop_forever proprement.
                self.subscriber.disconnect()
            return

        print(
            f"[OK] {measurement.site}/{measurement.device_id} "
            f"{measurement.kind}={measurement.value} {measurement.unit}"
        )


def _default_subscriber_factory(*, config: Any, on_measurement: Callable) -> Any:
    """Construit un ``MqttSubscriber`` (import paresseux du subscriber).

    Le subscriber importe lui-même ``paho-mqtt`` paresseusement, donc rien
    n'est importé tant que ``forge iot:listen`` n'est pas lancée.
    """
    from forge_mvc_iot.mqtt.subscriber import MqttSubscriber  # noqa: PLC0415

    return MqttSubscriber(config, on_measurement)


def _print_banner(config: Any) -> None:
    print("")
    print("Forge IoT listen")
    print("")
    print(f"[INFO] Broker MQTT : {config.mqtt_host}:{config.mqtt_port}")
    print(f"[INFO] Topic       : {config.mqtt_topic}")
    print("[INFO] Stockage    : table iot_events via IotEventRepository")
    print("[INFO] En écoute. Ctrl+C pour arrêter.")
    print("")


def run_listener(
    *,
    config: Any,
    repository: Any,
    subscriber_factory: Callable[..., Any] | None = None,
) -> int:
    """Écoute le broker et insère les mesures reçues dans ``iot_events``.

    Les dépendances (``config``, ``repository``, ``subscriber_factory``)
    sont injectées pour permettre un test complet sans broker ni base.

    Retourne 0 à l'arrêt normal (``Ctrl+C``), 1 si la connexion MQTT est
    impossible ou si une insertion base a échoué.
    """
    factory = subscriber_factory or _default_subscriber_factory
    listener = _StorageListener(repository)
    subscriber = factory(config=config, on_measurement=listener.on_measurement)
    listener.subscriber = subscriber

    _print_banner(config)

    try:
        subscriber.connect()
    except Exception as exc:  # noqa: BLE001 — message sobre, pas de stacktrace
        # Les erreurs de connexion MQTT ne portent pas le mot de passe.
        print(f"[ERREUR] Connexion MQTT impossible : {exc}", file=sys.stderr)
        return 1

    try:
        subscriber.loop_forever()
    except KeyboardInterrupt:
        print("")
        print("[INFO] Arrêt demandé (Ctrl+C).")
    finally:
        subscriber.disconnect()

    return 1 if listener.storage_error is not None else 0


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge iot:listen``.

    ``--help`` est intercepté en amont par le dispatcher central
    (``forge_cli.help_dispatch``). Retourne 1 si la configuration est
    invalide, sinon délègue à ``run_listener``.
    """
    if argv is None:
        argv = []

    from forge_mvc_iot.config import load_iot_config  # noqa: PLC0415
    from forge_mvc_iot.storage import IotEventRepository  # noqa: PLC0415

    try:
        config = load_iot_config()
    except ValueError as exc:
        print(f"[ERREUR] Configuration IoT invalide : {exc}", file=sys.stderr)
        return 1

    repository = IotEventRepository()
    return run_listener(config=config, repository=repository)
