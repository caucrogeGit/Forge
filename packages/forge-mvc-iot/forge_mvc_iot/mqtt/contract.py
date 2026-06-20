# pyright: strict
"""Parsing et validation du contrat MQTT Forge IoT — IOT-MQTT-CONTRACT-001.

Ce module est **pur** : il ne dépend pas de ``paho-mqtt``, il ne se
connecte à aucun broker, et il peut être testé entièrement hors ligne.

Contrat implémenté :

- topic ``forge/{site}/{device_id}/telemetry`` ;
- payload JSON avec quatre champs obligatoires
  (``kind``, ``value``, ``unit``, ``timestamp``) et un optionnel
  (``metadata``) ;
- ``site`` et ``device_id`` viennent du topic, jamais du payload.

Les erreurs de contrat lèvent une ``ContractError`` portant un ``code``
stable issu de la taxonomie documentée
(``docs/iot/mqtt-contract.md``).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast

__all__ = [
    "CODE_TOPIC_PATTERN",
    "CODE_PAYLOAD_PARSE",
    "CODE_PAYLOAD_FIELD_MISSING",
    "CODE_PAYLOAD_FIELD_TYPE",
    "CODE_PAYLOAD_VALUE_FORMAT",
    "ContractError",
    "Measurement",
    "parse_topic",
    "parse_payload",
    "parse_message",
]

# ── Codes d'erreur (taxonomie stable, alignée sur la page de contrat) ──────

CODE_TOPIC_PATTERN = "TOPIC_PATTERN"
CODE_PAYLOAD_PARSE = "PAYLOAD_PARSE"
CODE_PAYLOAD_FIELD_MISSING = "PAYLOAD_FIELD_MISSING"
CODE_PAYLOAD_FIELD_TYPE = "PAYLOAD_FIELD_TYPE"
CODE_PAYLOAD_VALUE_FORMAT = "PAYLOAD_VALUE_FORMAT"

# ── Regex de validation ─────────────────────────────────────────────────────

# Topic canonique forge/{site}/{device_id}/telemetry.
# site et device_id : slug [a-z0-9-]+ (interdits : majuscules, accents,
# espaces, wildcards MQTT '+' / '#'). Bornés à 64 caractères pour rester
# dans VARCHAR(64) du schéma et rejeter tôt (IOT-PAYLOAD-SLUG-BOUNDS-001).
_TOPIC_RE = re.compile(r"^forge/([a-z0-9-]{1,64})/([a-z0-9-]{1,64})/telemetry$")

# Plafond de taille du payload MQTT décodé : un message volumineux ne doit pas
# être chargé/parsé sans borne (vecteur DoS mémoire si le broker est exposé).
MAX_PAYLOAD_BYTES = 65536

# kind : slug [a-z0-9_-]+ (autorise '_' contrairement à site/device_id).
_KIND_RE = re.compile(r"^[a-z0-9_-]+$")

# ISO 8601 UTC avec suffixe Z obligatoire (pas d'espace séparateur,
# pas de fuseau implicite). On valide ensuite la sémantique avec
# datetime.fromisoformat (3.11+ accepte le Z).
_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


class ContractError(Exception):
    """Erreur de contrat MQTT.

    Porte un attribut ``code`` issu de la taxonomie documentée — utile
    pour les logs et les tests sans avoir à reparser le message.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


@dataclass(frozen=True)
class Measurement:
    """Mesure reçue, propre et typée, prête à être persistée ou exposée.

    Le ``timestamp`` est conservé en chaîne ISO 8601 UTC (suffixe ``Z``)
    pour rester proche du payload reçu. Le consommateur convertit en
    ``datetime`` s'il en a besoin — pas de pré-conversion ici qui
    perdrait des microsecondes ou imposerait un fuseau.
    """

    site: str
    device_id: str
    kind: str
    value: int | float
    unit: str
    timestamp: str
    metadata: dict[str, str] | None


def parse_topic(topic: str) -> tuple[str, str]:
    """Parse le topic. Retourne ``(site, device_id)``.

    Lève ``ContractError(CODE_TOPIC_PATTERN, ...)`` si le topic ne
    respecte pas ``forge/{site}/{device_id}/telemetry``.
    """
    match = _TOPIC_RE.match(topic)
    if not match:
        raise ContractError(
            CODE_TOPIC_PATTERN,
            f"Topic invalide : {topic!r} "
            "(attendu : forge/{site}/{device_id}/telemetry)",
        )
    return match.group(1), match.group(2)


def parse_payload(payload: str | bytes) -> dict[str, Any]:
    """Décode et parse le payload JSON. Retourne le dict brut.

    Lève ``ContractError(CODE_PAYLOAD_PARSE, ...)`` si :

    - le payload n'est pas du UTF-8 valide ;
    - le payload n'est pas un JSON valide ;
    - le JSON décodé n'est pas un objet (mais un tableau, un nombre, etc.).
    """
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ContractError(
            CODE_PAYLOAD_PARSE,
            f"Payload trop volumineux : {len(payload)} octets "
            f"(maximum {MAX_PAYLOAD_BYTES})",
        )

    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ContractError(
                CODE_PAYLOAD_PARSE,
                f"Payload non décodable en UTF-8 : {exc}",
            ) from exc

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ContractError(
            CODE_PAYLOAD_PARSE,
            f"JSON invalide : {exc.msg}",
        ) from exc

    if not isinstance(data, dict):
        raise ContractError(
            CODE_PAYLOAD_PARSE,
            f"Le payload doit être un objet JSON "
            f"(reçu : {type(data).__name__})",
        )
    return cast("dict[str, Any]", data)


def _validate_required_fields(data: dict[str, Any]) -> None:
    for field in ("kind", "value", "unit", "timestamp"):
        if field not in data:
            raise ContractError(
                CODE_PAYLOAD_FIELD_MISSING,
                f"Champ obligatoire absent : {field!r}",
            )


def _validate_types(data: dict[str, Any]) -> None:
    kind = data["kind"]
    if not isinstance(kind, str):
        raise ContractError(
            CODE_PAYLOAD_FIELD_TYPE,
            f"kind doit être string (reçu : {type(kind).__name__})",
        )

    value = data["value"]
    # bool est sous-classe de int en Python : on l'exclut explicitement,
    # une mesure booléenne n'est pas un "number" au sens du contrat.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(
            CODE_PAYLOAD_FIELD_TYPE,
            f"value doit être number (reçu : {type(value).__name__})",
        )

    unit = data["unit"]
    if not isinstance(unit, str):
        raise ContractError(
            CODE_PAYLOAD_FIELD_TYPE,
            f"unit doit être string (reçu : {type(unit).__name__})",
        )

    timestamp = data["timestamp"]
    if not isinstance(timestamp, str):
        raise ContractError(
            CODE_PAYLOAD_FIELD_TYPE,
            f"timestamp doit être string (reçu : {type(timestamp).__name__})",
        )

    if "metadata" in data and data["metadata"] is not None:
        metadata = data["metadata"]
        if not isinstance(metadata, dict):
            raise ContractError(
                CODE_PAYLOAD_FIELD_TYPE,
                f"metadata doit être un objet "
                f"(reçu : {type(metadata).__name__})",
            )
        for key, mvalue in cast("dict[Any, Any]", metadata).items():
            if not isinstance(mvalue, str):
                raise ContractError(
                    CODE_PAYLOAD_FIELD_TYPE,
                    f"metadata.{key} doit être string "
                    f"(reçu : {type(mvalue).__name__})",
                )


def _validate_formats(data: dict[str, Any]) -> None:
    kind = data["kind"]
    if not _KIND_RE.match(kind):
        raise ContractError(
            CODE_PAYLOAD_VALUE_FORMAT,
            f"kind n'est pas un slug [a-z0-9_-]+ : {kind!r}",
        )

    timestamp = data["timestamp"]
    if not _TIMESTAMP_RE.match(timestamp):
        raise ContractError(
            CODE_PAYLOAD_VALUE_FORMAT,
            f"timestamp doit être ISO 8601 UTC avec suffixe Z : "
            f"{timestamp!r}",
        )
    try:
        datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise ContractError(
            CODE_PAYLOAD_VALUE_FORMAT,
            f"timestamp ISO 8601 invalide : {timestamp!r} ({exc})",
        ) from exc


def parse_message(topic: str, payload: str | bytes) -> Measurement:
    """Parse un message complet (topic + payload) en ``Measurement``.

    Pipeline :

    1. ``parse_topic(topic)`` → ``(site, device_id)`` ;
    2. ``parse_payload(payload)`` → dict ;
    3. validation des champs requis, types, formats ;
    4. construction de la ``Measurement`` immuable.

    Les éventuels champs ``site`` ou ``device_id`` dans le payload sont
    **ignorés** : la vérité est dans le topic.
    """
    site, device_id = parse_topic(topic)
    data = parse_payload(payload)
    _validate_required_fields(data)
    _validate_types(data)
    _validate_formats(data)

    # On normalise l'absence et la valeur None à None pour avoir un
    # comportement stable côté consommateur ; un objet présent a déjà été
    # validé (clés/valeurs str) par ``_validate_types``.
    raw_metadata = data.get("metadata")
    metadata: dict[str, str] | None = (
        cast("dict[str, str]", raw_metadata) if isinstance(raw_metadata, dict) else None
    )

    return Measurement(
        site=site,
        device_id=device_id,
        kind=data["kind"],
        value=data["value"],
        unit=data["unit"],
        timestamp=data["timestamp"],
        metadata=metadata,
    )
