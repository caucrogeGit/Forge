"""Garde-fou IOT-PAYLOAD-SLUG-BOUNDS-001.

Le contrat MQTT borne les slugs `site`/`device_id` à 64 caractères (alignés sur
VARCHAR(64)) et plafonne la taille du payload décodé, pour rejeter tôt et fermer
le vecteur DoS mémoire d'un broker exposé.
"""

from __future__ import annotations

import json

import pytest

pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.mqtt.contract import (
    CODE_PAYLOAD_PARSE,
    CODE_TOPIC_PATTERN,
    MAX_PAYLOAD_BYTES,
    ContractError,
    parse_payload,
    parse_topic,
)


def test_slug_de_64_caracteres_accepte() -> None:
    device = "d" * 64
    site, parsed_device = parse_topic(f"forge/atelier/{device}/telemetry")
    assert site == "atelier"
    assert parsed_device == device


def test_slug_de_65_caracteres_rejete() -> None:
    device = "d" * 65
    with pytest.raises(ContractError) as exc:
        parse_topic(f"forge/atelier/{device}/telemetry")
    assert exc.value.code == CODE_TOPIC_PATTERN


def test_payload_au_dela_du_plafond_rejete() -> None:
    gros = ("x" * (MAX_PAYLOAD_BYTES + 1)).encode("utf-8")
    with pytest.raises(ContractError) as exc:
        parse_payload(gros)
    assert exc.value.code == CODE_PAYLOAD_PARSE


def test_payload_normal_accepte() -> None:
    data = parse_payload(json.dumps({"kind": "temp", "value": 21}).encode("utf-8"))
    assert data["kind"] == "temp"
