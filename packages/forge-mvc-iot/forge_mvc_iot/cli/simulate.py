"""Commande ``forge iot:simulate`` — IOT-SIMULATOR-001.

Publie des mesures **factices** mais **conformes au contrat MQTT Forge
IoT** vers le broker configuré, sans capteur physique. But pédagogique :
tester le flux complet ::

    forge iot:doctor --mqtt   →   forge iot:simulate   →   subscriber MQTT
    →   iot_events   →   /api/iot/events

Responsabilité unique : **publier** des messages MQTT valides sur le
topic ``forge/{site}/{device_id}/telemetry``. Le simulateur ne lance pas
le subscriber, n'écrit pas en base et n'appelle pas l'API HTTP.

Règles (alignées sur le reste du module IoT) :

- configuration via ``load_iot_config()`` ;
- ``paho-mqtt`` importé **paresseusement** (rien tant que la commande
  n'est pas lancée) ;
- ``client_factory`` injectable pour tester sans broker réel ;
- timestamp UTC avec suffixe ``Z`` ;
- mot de passe **jamais** affiché ;
- pas de boucle infinie : ``--count`` borné (1..1000), ``--interval``
  borné (0..60 s) ;
- QoS 0, pas de ``retain`` — volontairement simple.

Chaque message est validé contre le contrat (``parse_message``) **avant**
toute connexion : on ne publie que des messages conformes, et une option
invalide (site/device/kind hors slug) est rejetée sans ouvrir de socket.
"""

from __future__ import annotations

import json
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from forge_mvc_iot.mqtt.contract import ContractError, parse_message
from forge_mvc_iot.mqtt.tls import configure_tls

__all__ = [
    "DEFAULT_SITE",
    "DEFAULT_DEVICE",
    "DEFAULT_KIND",
    "DEFAULT_VALUE",
    "DEFAULT_UNIT",
    "DEFAULT_SOURCE",
    "SIMULATION_PROFILES",
    "MIN_COUNT",
    "MAX_COUNT",
    "MIN_INTERVAL",
    "MAX_INTERVAL",
    "ArgumentError",
    "SimulateOptions",
    "build_topic",
    "build_payload",
    "utc_timestamp",
    "parse_args",
    "publish_measurements",
    "main",
]

DEFAULT_SITE = "atelier"
DEFAULT_DEVICE = "esp32-001"
DEFAULT_KIND = "temperature"
DEFAULT_VALUE = 22.4
DEFAULT_UNIT = "°C"
DEFAULT_SOURCE = "forge-iot-simulator"

MIN_COUNT = 1
MAX_COUNT = 1000
MIN_INTERVAL = 0.0
MAX_INTERVAL = 60.0

# Profils pédagogiques : valeurs par défaut prêtes à l'emploi pour générer
# plusieurs types de mesures sans capteur physique. Un profil ne fournit que
# des défauts (kind/value/unit) ; ``--kind`` / ``--value`` / ``--unit``
# peuvent encore les surcharger explicitement. Volontairement simple : pas de
# random-walk, pas de bruit statistique, pas de scénario multi-capteurs.
SIMULATION_PROFILES: dict[str, dict[str, Any]] = {
    "temperature": {"kind": "temperature", "value": 22.4, "unit": "°C"},
    "humidity": {"kind": "humidity", "value": 55.0, "unit": "%"},
    "presence": {"kind": "presence", "value": 1.0, "unit": "state"},
    "energy": {"kind": "energy", "value": 120.5, "unit": "W"},
}


class ArgumentError(Exception):
    """Option de ligne de commande invalide (message destiné à l'humain)."""


@dataclass(frozen=True)
class SimulateOptions:
    """Paramètres résolus d'une exécution ``forge iot:simulate``."""

    site: str = DEFAULT_SITE
    device: str = DEFAULT_DEVICE
    kind: str = DEFAULT_KIND
    value: int | float = DEFAULT_VALUE
    unit: str = DEFAULT_UNIT
    count: int = 1
    interval: float = 1.0
    # Nom du profil pédagogique appliqué (``None`` = aucun, comportement
    # historique). Renseigne ``metadata.profile`` dans le payload publié.
    profile: str | None = None


# ── Construction des messages ───────────────────────────────────────────────


def build_topic(site: str, device_id: str) -> str:
    """Topic canonique ``forge/{site}/{device_id}/telemetry``."""
    return f"forge/{site}/{device_id}/telemetry"


def utc_timestamp(now: Callable[[], datetime] | None = None) -> str:
    """Horodatage ISO 8601 UTC avec suffixe ``Z`` (précision seconde).

    ``now`` est injectable pour les tests ; par défaut, l'heure courante
    UTC. Un ``datetime`` aware dans un autre fuseau est converti en UTC ;
    un ``datetime`` naïf est supposé UTC.
    """
    moment = now() if now is not None else datetime.now(timezone.utc)
    if moment.tzinfo is not None:
        moment = moment.astimezone(timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_payload(
    *,
    kind: str,
    value: int | float,
    unit: str,
    timestamp: str,
    source: str = DEFAULT_SOURCE,
    profile: str | None = None,
) -> dict[str, Any]:
    """Construit le payload JSON conforme au contrat MQTT Forge IoT.

    ``profile`` (s'il est fourni) est ajouté à ``metadata`` sous la clé
    ``profile`` — une string, comme l'exige le contrat (toutes les valeurs
    de ``metadata`` doivent être des chaînes). Sans profil, le payload est
    inchangé (``metadata = {"source": ...}``).
    """
    metadata: dict[str, str] = {"source": source}
    if profile is not None:
        metadata["profile"] = profile
    return {
        "kind": kind,
        "value": value,
        "unit": unit,
        "timestamp": timestamp,
        "metadata": metadata,
    }


# ── Parsing des arguments ────────────────────────────────────────────────────


def _expect_value(args: list[str], index: int, flag: str) -> str:
    if index + 1 >= len(args):
        raise ArgumentError(f"valeur manquante pour {flag}")
    return args[index + 1]


def parse_args(args: list[str]) -> SimulateOptions:
    """Parse les arguments en ``SimulateOptions``.

    Lève ``ArgumentError`` (message clair) pour une option inconnue, une
    valeur manquante, un nombre invalide ou une borne dépassée.
    """
    site = DEFAULT_SITE
    device = DEFAULT_DEVICE
    count = 1
    interval = 1.0
    profile: str | None = None

    # Surcharges explicites kind/value/unit : ``None`` tant que l'utilisateur
    # ne les a pas fournies, pour distinguer « non précisé » de « précisé ».
    # On résout l'ordre profil → surcharge **après** la boucle, pour que
    # ``--kind``/``--value``/``--unit`` gagnent quel que soit leur ordre vs
    # ``--profile``.
    kind_override: str | None = None
    value_override: int | float | None = None
    unit_override: str | None = None

    i = 0
    while i < len(args):
        flag = args[i]
        if flag == "--site":
            site = _expect_value(args, i, flag)
        elif flag == "--device":
            device = _expect_value(args, i, flag)
        elif flag == "--profile":
            profile = _expect_value(args, i, flag)
        elif flag == "--kind":
            kind_override = _expect_value(args, i, flag)
        elif flag == "--unit":
            unit_override = _expect_value(args, i, flag)
        elif flag == "--value":
            raw = _expect_value(args, i, flag)
            try:
                value_override = float(raw)
            except ValueError as exc:
                raise ArgumentError(
                    f"--value doit être un nombre (vu : {raw!r})"
                ) from exc
        elif flag == "--count":
            raw = _expect_value(args, i, flag)
            try:
                count = int(raw)
            except ValueError as exc:
                raise ArgumentError(
                    f"--count doit être un entier (vu : {raw!r})"
                ) from exc
            if count < MIN_COUNT or count > MAX_COUNT:
                raise ArgumentError(
                    f"--count hors plage {MIN_COUNT}-{MAX_COUNT} (vu : {count})"
                )
        elif flag == "--interval":
            raw = _expect_value(args, i, flag)
            try:
                interval = float(raw)
            except ValueError as exc:
                raise ArgumentError(
                    f"--interval doit être un nombre (vu : {raw!r})"
                ) from exc
            if interval < MIN_INTERVAL or interval > MAX_INTERVAL:
                raise ArgumentError(
                    f"--interval hors plage {MIN_INTERVAL}-{MAX_INTERVAL} s "
                    f"(vu : {interval})"
                )
        else:
            raise ArgumentError(f"option inconnue : {flag}")
        i += 2

    # Résolution kind/value/unit : défauts globaux → profil → surcharges
    # explicites (premier match gagne au profit du plus spécifique).
    kind = DEFAULT_KIND
    value: int | float = DEFAULT_VALUE
    unit = DEFAULT_UNIT
    if profile is not None:
        if profile not in SIMULATION_PROFILES:
            available = ", ".join(SIMULATION_PROFILES)
            raise ArgumentError(
                f"Profil inconnu : {profile}\n"
                f"Profils disponibles : {available}"
            )
        preset = SIMULATION_PROFILES[profile]
        kind = preset["kind"]
        value = preset["value"]
        unit = preset["unit"]
    if kind_override is not None:
        kind = kind_override
    if value_override is not None:
        value = value_override
    if unit_override is not None:
        unit = unit_override

    return SimulateOptions(
        site=site,
        device=device,
        kind=kind,
        value=value,
        unit=unit,
        count=count,
        interval=interval,
        profile=profile,
    )


# ── Client MQTT (import paho paresseux) ──────────────────────────────────────


def _default_client_factory(config) -> Any:
    """Construit le client ``paho-mqtt`` par défaut (import paresseux).

    Aligné sur ``forge_mvc_iot.mqtt.subscriber`` et le doctor : ``paho``
    n'est importé que lorsque la commande est réellement lancée.
    """
    import paho.mqtt.client as mqtt  # noqa: PLC0415

    return mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=config.mqtt_client_id,
    )


def publish_measurements(
    config,
    options: SimulateOptions,
    *,
    client_factory: Callable[..., Any] | None = None,
    now: Callable[[], datetime] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    """Publie ``options.count`` mesures sur le topic configuré.

    Connexion brève : ``connect`` → boucle réseau → ``publish`` (× count,
    espacés de ``interval`` s) → arrêt de la boucle → ``disconnect``. Pas
    de ``loop_forever``, pas d'abonnement, pas de DB.

    Le mot de passe éventuel est transmis à paho via ``username_pw_set``
    mais n'apparaît dans aucune sortie. Retourne la liste des messages
    publiés (topic, payload) — utile pour les tests.
    """
    factory = client_factory or _default_client_factory
    do_sleep = sleep if sleep is not None else time.sleep

    client = factory(config)
    # TLS (si activé) doit être configuré avant connect(). No-op sinon :
    # la publication en clair reste strictement identique.
    configure_tls(client, config)
    if config.mqtt_username:
        client.username_pw_set(config.mqtt_username, config.mqtt_password)

    topic = build_topic(options.site, options.device)
    published: list[tuple[str, dict[str, Any]]] = []

    client.connect(config.mqtt_host, config.mqtt_port)
    client.loop_start()
    try:
        for index in range(options.count):
            payload = build_payload(
                kind=options.kind,
                value=options.value,
                unit=options.unit,
                timestamp=utc_timestamp(now),
                profile=options.profile,
            )
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            info = client.publish(topic, body, qos=0)
            # Forcer l'envoi avant de fermer (le vrai client paho renvoie
            # un MQTTMessageInfo ; un mock peut renvoyer autre chose).
            wait_for_publish = getattr(info, "wait_for_publish", None)
            if callable(wait_for_publish):
                try:
                    wait_for_publish(timeout=2.0)
                except Exception:  # pragma: no cover — défensif
                    pass
            published.append((topic, payload))
            print(
                f"[OK] publié {index + 1}/{options.count} → {topic} "
                f"({options.kind}={options.value}{options.unit})"
            )
            if index < options.count - 1 and options.interval > 0:
                do_sleep(options.interval)
    finally:
        client.loop_stop()
        client.disconnect()

    return published


# ── Point d'entrée CLI ───────────────────────────────────────────────────────


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge iot:simulate``.

    Retourne 0 si la publication réussit, 2 si une option est invalide,
    1 pour une configuration invalide ou une erreur de connexion /
    publication (message sobre, jamais de mot de passe ni de stacktrace).
    """
    if args is None:
        args = []

    try:
        options = parse_args(args)
    except ArgumentError as exc:
        print(f"[ERREUR] {exc}", file=sys.stderr)
        print(
            "Aide : forge iot:simulate --help", file=sys.stderr,
        )
        return 2

    from forge_mvc_iot.config import load_iot_config  # noqa: PLC0415

    try:
        config = load_iot_config()
    except ValueError as exc:
        print(f"[ERREUR] configuration IoT invalide : {exc}", file=sys.stderr)
        return 1

    # On ne publie que des messages conformes : valider AVANT de se
    # connecter, pour rejeter proprement un site/device/kind hors slug.
    sample = build_payload(
        kind=options.kind,
        value=options.value,
        unit=options.unit,
        timestamp=utc_timestamp(),
        profile=options.profile,
    )
    try:
        parse_message(build_topic(options.site, options.device), json.dumps(sample))
    except ContractError as exc:
        print(
            f"[ERREUR] message non conforme au contrat MQTT — {exc.message}",
            file=sys.stderr,
        )
        return 2

    print(
        f"[INFO] publication de {options.count} mesure(s) vers "
        f"{config.mqtt_host}:{config.mqtt_port}"
    )
    try:
        publish_measurements(config, options)
    except Exception as exc:
        # Message sobre : pas de stacktrace, jamais le mot de passe.
        print(
            f"[ERREUR] publication MQTT impossible — {type(exc).__name__}",
            file=sys.stderr,
        )
        return 1

    print(f"[OK] {options.count} mesure(s) publiée(s).")
    return 0
