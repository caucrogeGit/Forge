# pyright: strict
"""Commande ``forge iot:listen`` — IOT-SUBSCRIBER-CLI-001 /
IOT-LISTEN-RESILIENCE-001.

Relie les briques existantes en un flux local utilisable ::

    Mosquitto → forge iot:listen → MqttSubscriber
    → IotEventRepository.insert() → iot_events

Elle :

- charge la configuration via ``load_iot_config()`` ;
- crée un ``IotEventRepository`` ;
- crée un ``MqttSubscriber`` branché sur ``repository.insert`` **et** sur
  un handler d'erreurs de contrat (un message MQTT invalide est ignoré,
  pas fatal) ;
- affiche chaque mesure reçue ;
- tient un petit ``ListenStats`` (reçues / stockées / erreurs de contrat /
  erreurs de stockage) restitué en fin de session ;
- reste active jusqu'à ``Ctrl+C`` et s'arrête proprement
  (``disconnect`` garanti dans un ``finally``).

C'est une commande de **développement / pédagogie**, pas un service de
production : pas de daemon, pas de retry/backoff, pas de batch, pas de
multi-thread storage, pas de file d'attente. On s'arrête au **premier
échec base** (plus simple et plus parlant en atelier) ; en revanche une
erreur de **contrat** MQTT n'arrête jamais l'écoute.

``paho-mqtt`` et ``core.database`` ne sont importés que lorsque la
commande est réellement lancée (imports paresseux via le subscriber et
le repository).
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from forge_mvc_iot.mqtt.contract import ContractError, Measurement

__all__ = [
    "ListenStats",
    "run_listener",
    "main",
]

# Code d'erreur MariaDB « table absente » (ER_NO_SUCH_TABLE).
_MARIADB_TABLE_NOT_FOUND_ERRNO = 1146

# Codes d'erreur MariaDB qui signifient « la base est injoignable / refuse
# la connexion » (par opposition à une erreur SQL applicative).
# Référence : https://mariadb.com/kb/en/mariadb-error-codes/
# - 1044 ER_DBACCESS_DENIED_ERROR     - accès refusé à la base
# - 1045 ER_ACCESS_DENIED_ERROR       - identifiants refusés
# - 1049 ER_BAD_DB_ERROR              - base inconnue
# - 2002 CR_CONNECTION_ERROR          - socket local injoignable
# - 2003 CR_CONN_HOST_ERROR           - hôte TCP injoignable
# - 2005 CR_UNKNOWN_HOST              - hôte inconnu
# - 2006 CR_SERVER_GONE_ERROR         - serveur parti
_MARIADB_CONNECTION_ERRNOS = frozenset({1044, 1045, 1049, 2002, 2003, 2005, 2006})

_CONNECTION_TEXT_MARKERS = (
    "can't connect",
    "connection refused",
    "access denied",
    "unknown database",
    "unknown mysql server host",
    "server has gone away",
)


@dataclass
class ListenStats:
    """État de session d'une écoute ``forge iot:listen``.

    Compteurs simples mis à jour par ``_StorageListener`` :

    - ``received``        : mesures reçues et conformes au contrat ;
    - ``stored``          : mesures réellement insérées en base ;
    - ``contract_errors`` : messages MQTT ignorés (contrat invalide) ;
    - ``storage_errors``  : échecs d'insertion en base.
    """

    received: int = 0
    stored: int = 0
    contract_errors: int = 0
    storage_errors: int = 0


def _is_storage_missing(exc: Exception) -> bool:
    """Détecte une erreur « table ``iot_events`` absente ».

    Reconnaît ``errno == 1146`` (MariaDB) ou ``"doesn't exist"`` dans le
    message (filet de sécurité si l'exception est wrappée).
    """
    if getattr(exc, "errno", None) == _MARIADB_TABLE_NOT_FOUND_ERRNO:
        return True
    return "doesn't exist" in str(exc).lower()


def _is_connection_error(exc: Exception) -> bool:
    """Détecte une erreur « connexion base impossible ».

    Reconnaît les ``errno`` de connexion / accès MariaDB, ou des marqueurs
    textuels (filet de sécurité si l'exception est wrappée et perd son
    ``errno``).
    """
    if getattr(exc, "errno", None) in _MARIADB_CONNECTION_ERRNOS:
        return True
    message = str(exc).lower()
    return any(marker in message for marker in _CONNECTION_TEXT_MARKERS)


class _StorageListener:
    """Branche les mesures reçues sur ``repository.insert``.

    Tient un ``ListenStats`` et affiche un ``[OK]`` par mesure persistée.

    - Une **erreur de contrat** MQTT (``on_contract_error``) est comptée et
      signalée par un ``[WARN]``, mais **n'arrête pas** l'écoute.
    - Au **premier échec base** (``on_measurement``), émet un message
      pédagogique selon la nature de l'erreur, mémorise l'erreur et
      **demande l'arrêt** du subscriber (``disconnect``) — la commande sort
      alors en erreur.
    """

    def __init__(self, repository: Any) -> None:
        self.repository = repository
        self.stats = ListenStats()
        self.storage_error: Exception | None = None
        # Renseigné par ``run_listener`` après la construction du
        # subscriber (le callback a besoin d'une référence pour demander
        # l'arrêt depuis l'intérieur de la boucle réseau).
        self.subscriber: Any | None = None

    def on_measurement(self, measurement: Any) -> None:
        self.stats.received += 1
        try:
            self.repository.insert(measurement)
        except Exception as exc:  # noqa: BLE001 — on classe ci-dessous
            self.stats.storage_errors += 1
            self.storage_error = exc
            self._report_storage_error(exc)
            if self.subscriber is not None:
                # Fait retourner loop_forever proprement.
                self.subscriber.disconnect()
            return

        self.stats.stored += 1
        print(
            f"[OK] {measurement.site}/{measurement.device_id} "
            f"{measurement.kind}={measurement.value} {measurement.unit}"
        )

    def on_contract_error(self, error: Any, topic: str, payload: bytes) -> None:
        """Compte et signale un message MQTT invalide — sans arrêter l'écoute.

        ``error`` est une ``ContractError`` portant un ``code`` issu de la
        taxonomie documentée (``TOPIC_PATTERN``, ``PAYLOAD_FIELD_MISSING``…).
        On n'affiche que le code : ni le payload brut ni le détail technique,
        pour rester sobre et ne pas inonder la sortie en atelier.
        """
        self.stats.contract_errors += 1
        code = getattr(error, "code", None) or "CONTRAT_INVALIDE"
        print(f"[WARN] Message MQTT ignoré — {code}", file=sys.stderr)

    def _report_storage_error(self, exc: Exception) -> None:
        """Affiche un message pédagogique selon la nature de l'erreur base.

        Trois cas distingués, message **sobre** (pas de stacktrace) :

        - table ``iot_events`` absente → conseiller ``forge iot:init`` +
          ``forge migration:apply`` ;
        - connexion base impossible → conseiller ``forge db:init`` +
          ``forge iot:doctor --db`` ;
        - toute autre erreur SQL → message générique.
        """
        if _is_storage_missing(exc):
            print("[ERREUR] Table iot_events absente.", file=sys.stderr)
            print(
                "Conseil : lance forge iot:init puis forge migration:apply.",
                file=sys.stderr,
            )
        elif _is_connection_error(exc):
            print("[ERREUR] Connexion base impossible.", file=sys.stderr)
            print(
                "Conseil : vérifie forge db:init et forge iot:doctor --db.",
                file=sys.stderr,
            )
        else:
            print("[ERREUR] Stockage IoT impossible.", file=sys.stderr)


def _default_subscriber_factory(
    *,
    config: Any,
    on_measurement: Callable[[Measurement], None],
    on_contract_error: Callable[[ContractError, str, bytes], None],
) -> Any:
    """Construit un ``MqttSubscriber`` (import paresseux du subscriber).

    Le subscriber importe lui-même ``paho-mqtt`` paresseusement, donc rien
    n'est importé tant que ``forge iot:listen`` n'est pas lancée.
    """
    from forge_mvc_iot.mqtt.subscriber import MqttSubscriber  # noqa: PLC0415

    return MqttSubscriber(
        config,
        on_measurement,
        on_contract_error=on_contract_error,
    )


def _print_banner(config: Any) -> None:
    print("")
    print("Forge IoT listen")
    print("")
    print(f"[INFO] Broker MQTT : {config.mqtt_host}:{config.mqtt_port}")
    print(f"[INFO] Topic       : {config.mqtt_topic}")
    print("[INFO] Stockage    : table iot_events via IotEventRepository")
    print("[INFO] En écoute. Ctrl+C pour arrêter.")
    print("")


def _print_summary(stats: ListenStats) -> None:
    print("")
    print("Résumé :")
    print(f"  mesures reçues       : {stats.received}")
    print(f"  mesures stockées     : {stats.stored}")
    print(f"  erreurs de contrat   : {stats.contract_errors}")
    print(f"  erreurs de stockage  : {stats.storage_errors}")


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
    impossible ou si une insertion base a échoué. Un résumé de session est
    affiché dès que l'écoute a démarré (même en cas d'échec base).
    """
    factory = subscriber_factory or _default_subscriber_factory
    listener = _StorageListener(repository)
    subscriber = factory(
        config=config,
        on_measurement=listener.on_measurement,
        on_contract_error=listener.on_contract_error,
    )
    listener.subscriber = subscriber

    _print_banner(config)

    try:
        subscriber.connect()
    except Exception as exc:  # noqa: BLE001 — message sobre, pas de stacktrace
        # Les erreurs de connexion MQTT ne portent pas le mot de passe.
        print(f"[ERREUR] Connexion MQTT impossible : {exc}", file=sys.stderr)
        return 1

    interrupted = False
    try:
        subscriber.loop_forever()
    except KeyboardInterrupt:
        interrupted = True
        print("")
        print("[INFO] Arrêt demandé.")
    finally:
        # disconnect() est toujours appelé, même si la boucle a levé.
        try:
            subscriber.disconnect()
        except Exception:  # noqa: BLE001 — défensif : ne pas masquer l'arrêt
            pass

    if interrupted:
        print("[OK] Écoute MQTT arrêtée proprement.")

    _print_summary(listener.stats)

    return 1 if listener.storage_error is not None else 0


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge iot:listen``.

    ``--help`` est intercepté en amont par le dispatcher central
    (``cli.help_dispatch``). Retourne 1 si la configuration est
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
