"""Tests du subscriber MQTT Forge IoT — IOT-MQTT-SUBSCRIBER-001.

Deux volets :

1. **Contrat pur** — ``forge_mvc_iot.mqtt.contract`` : parsing du topic
   et du payload, taxonomie d'erreurs stable. Aucun broker, aucun paho.
2. **Subscriber** — ``forge_mvc_iot.mqtt.subscriber.MqttSubscriber`` :
   pont vers ``paho.mqtt.client.Client``. Testé avec un client factice
   injecté via ``client_factory``, sans broker réel.

Hors périmètre vérifié : aucun stockage SQL, aucune route HTTP, aucune
intégration core, aucune intégration Forge Design.
"""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.config import IotConfig
from forge_mvc_iot.mqtt.contract import (
    CODE_PAYLOAD_FIELD_MISSING,
    CODE_PAYLOAD_FIELD_TYPE,
    CODE_PAYLOAD_PARSE,
    CODE_PAYLOAD_VALUE_FORMAT,
    CODE_TOPIC_PATTERN,
    ContractError,
    Measurement,
    parse_message,
    parse_payload,
    parse_topic,
)
from forge_mvc_iot.mqtt.subscriber import MqttSubscriber

PROJECT_ROOT = Path(__file__).parent.parent
IOT_PYPROJECT = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "pyproject.toml"
CORE_DIR = PROJECT_ROOT / "core"


# ─── Helpers ───────────────────────────────────────────────────────────────


def _make_config(**overrides) -> IotConfig:
    base = dict(
        mqtt_host="localhost",
        mqtt_port=1883,
        mqtt_topic="forge/+/+/telemetry",
        mqtt_client_id="forge-iot-test",
        mqtt_username=None,
        mqtt_password=None,
    )
    base.update(overrides)
    return IotConfig(**base)


VALID_TOPIC = "forge/atelier/esp32-001/telemetry"
VALID_PAYLOAD_MINIMAL = (
    '{"kind":"temperature","value":22.4,"unit":"°C",'
    '"timestamp":"2026-05-28T10:00:00Z"}'
)


# ═══════════════════════════════════════════════════════════════════════════
# Contrat — parsing topic
# ═══════════════════════════════════════════════════════════════════════════


class TestParseTopicValid:
    def test_simple_topic(self):
        site, device_id = parse_topic("forge/atelier/esp32-001/telemetry")
        assert site == "atelier"
        assert device_id == "esp32-001"

    def test_topic_with_hyphens(self):
        site, device_id = parse_topic("forge/salle-tp/raspi-04/telemetry")
        assert site == "salle-tp"
        assert device_id == "raspi-04"


class TestParseTopicInvalid:
    @pytest.mark.parametrize(
        "topic, reason",
        [
            ("atelier/esp32-001/telemetry", "racine forge/ manquante"),
            ("forge/Atelier/esp32-001/telemetry", "majuscule dans site"),
            ("forge/atelier/esp32 001/telemetry", "espace dans device_id"),
            ("forge/atelier/esp32-001/data", "suffixe différent"),
            ("forge/+/esp32-001/telemetry", "wildcard interdit"),
            ("forge/#/telemetry", "wildcard interdit"),
            ("forge//esp32-001/telemetry", "site vide"),
            ("forge/atelier//telemetry", "device_id vide"),
            ("forge/atelier/esp32-001", "telemetry manquant"),
            ("", "topic vide"),
            ("forge/atelier/esp_001/telemetry", "underscore interdit dans device_id"),
        ],
    )
    def test_invalid_topic_raises(self, topic, reason):
        with pytest.raises(ContractError) as excinfo:
            parse_topic(topic)
        assert excinfo.value.code == CODE_TOPIC_PATTERN, reason


# ═══════════════════════════════════════════════════════════════════════════
# Contrat — parsing payload
# ═══════════════════════════════════════════════════════════════════════════


class TestParsePayloadValid:
    def test_str_payload(self):
        data = parse_payload(VALID_PAYLOAD_MINIMAL)
        assert isinstance(data, dict)
        assert data["kind"] == "temperature"

    def test_bytes_payload(self):
        data = parse_payload(VALID_PAYLOAD_MINIMAL.encode("utf-8"))
        assert data["value"] == 22.4

    def test_empty_object(self):
        # parse_payload tolère un objet vide ; la validation des champs
        # requis intervient plus loin dans parse_message.
        assert parse_payload("{}") == {}


class TestParsePayloadInvalid:
    def test_invalid_utf8(self):
        with pytest.raises(ContractError) as exc:
            parse_payload(b"\xff\xfe\xfd")
        assert exc.value.code == CODE_PAYLOAD_PARSE

    def test_invalid_json(self):
        with pytest.raises(ContractError) as exc:
            parse_payload('{"kind": "temp",')
        assert exc.value.code == CODE_PAYLOAD_PARSE

    @pytest.mark.parametrize("payload", ["[1,2,3]", '"string"', "42", "null", "true"])
    def test_non_object_json(self, payload):
        with pytest.raises(ContractError) as exc:
            parse_payload(payload)
        assert exc.value.code == CODE_PAYLOAD_PARSE


# ═══════════════════════════════════════════════════════════════════════════
# Contrat — parse_message (intégration topic + payload)
# ═══════════════════════════════════════════════════════════════════════════


class TestParseMessageValid:
    def test_minimal(self):
        m = parse_message(VALID_TOPIC, VALID_PAYLOAD_MINIMAL)
        assert isinstance(m, Measurement)
        assert m.site == "atelier"
        assert m.device_id == "esp32-001"
        assert m.kind == "temperature"
        assert m.value == 22.4
        assert m.unit == "°C"
        assert m.timestamp == "2026-05-28T10:00:00Z"
        assert m.metadata is None

    def test_with_metadata(self):
        payload = (
            '{"kind":"temperature","value":22.4,"unit":"°C",'
            '"timestamp":"2026-05-28T10:00:00Z",'
            '"metadata":{"room":"atelier","sensor":"dht22"}}'
        )
        m = parse_message(VALID_TOPIC, payload)
        assert m.metadata == {"room": "atelier", "sensor": "dht22"}

    def test_integer_value(self):
        payload = (
            '{"kind":"humidity","value":47,"unit":"%",'
            '"timestamp":"2026-05-28T10:00:05Z"}'
        )
        m = parse_message("forge/salle-tp/raspi-04/telemetry", payload)
        assert m.value == 47
        assert isinstance(m.value, int)

    def test_float_value(self):
        m = parse_message(VALID_TOPIC, VALID_PAYLOAD_MINIMAL)
        assert isinstance(m.value, float)

    def test_timestamp_with_fractional_seconds(self):
        payload = (
            '{"kind":"temperature","value":22.4,"unit":"°C",'
            '"timestamp":"2026-05-28T10:00:00.123Z"}'
        )
        m = parse_message(VALID_TOPIC, payload)
        assert m.timestamp == "2026-05-28T10:00:00.123Z"

    def test_extra_payload_field_ignored(self):
        payload = (
            '{"kind":"temperature","value":22.4,"unit":"°C",'
            '"timestamp":"2026-05-28T10:00:00Z","extra":"ignored"}'
        )
        m = parse_message(VALID_TOPIC, payload)
        assert not hasattr(m, "extra")

    def test_site_in_payload_is_ignored(self):
        # Décision verrouillée : le topic est la source de vérité.
        payload = (
            '{"kind":"temperature","value":22.4,"unit":"°C",'
            '"timestamp":"2026-05-28T10:00:00Z","site":"AUTRE-SITE"}'
        )
        m = parse_message(VALID_TOPIC, payload)
        assert m.site == "atelier"  # du topic, pas du payload

    def test_device_id_in_payload_is_ignored(self):
        payload = (
            '{"kind":"temperature","value":22.4,"unit":"°C",'
            '"timestamp":"2026-05-28T10:00:00Z","device_id":"AUTRE-ID"}'
        )
        m = parse_message(VALID_TOPIC, payload)
        assert m.device_id == "esp32-001"

    def test_measurement_is_frozen(self):
        m = parse_message(VALID_TOPIC, VALID_PAYLOAD_MINIMAL)
        with pytest.raises((AttributeError, Exception)):
            m.value = 99  # type: ignore[misc]


class TestParseMessageMissingFields:
    @pytest.mark.parametrize("missing", ["kind", "value", "unit", "timestamp"])
    def test_missing_required_field(self, missing):
        full = {
            "kind": "temperature",
            "value": 22.4,
            "unit": "°C",
            "timestamp": "2026-05-28T10:00:00Z",
        }
        del full[missing]
        import json

        with pytest.raises(ContractError) as exc:
            parse_message(VALID_TOPIC, json.dumps(full))
        assert exc.value.code == CODE_PAYLOAD_FIELD_MISSING
        assert missing in exc.value.message


class TestParseMessageWrongTypes:
    def test_value_as_string(self):
        payload = (
            '{"kind":"temperature","value":"22.4","unit":"°C",'
            '"timestamp":"2026-05-28T10:00:00Z"}'
        )
        with pytest.raises(ContractError) as exc:
            parse_message(VALID_TOPIC, payload)
        assert exc.value.code == CODE_PAYLOAD_FIELD_TYPE

    def test_value_as_bool_refused(self):
        payload = (
            '{"kind":"temperature","value":true,"unit":"°C",'
            '"timestamp":"2026-05-28T10:00:00Z"}'
        )
        with pytest.raises(ContractError) as exc:
            parse_message(VALID_TOPIC, payload)
        assert exc.value.code == CODE_PAYLOAD_FIELD_TYPE

    def test_kind_as_number(self):
        payload = (
            '{"kind":42,"value":22.4,"unit":"°C",'
            '"timestamp":"2026-05-28T10:00:00Z"}'
        )
        with pytest.raises(ContractError) as exc:
            parse_message(VALID_TOPIC, payload)
        assert exc.value.code == CODE_PAYLOAD_FIELD_TYPE

    def test_unit_as_number(self):
        payload = (
            '{"kind":"temperature","value":22.4,"unit":1,'
            '"timestamp":"2026-05-28T10:00:00Z"}'
        )
        with pytest.raises(ContractError) as exc:
            parse_message(VALID_TOPIC, payload)
        assert exc.value.code == CODE_PAYLOAD_FIELD_TYPE

    def test_timestamp_as_number(self):
        payload = (
            '{"kind":"temperature","value":22.4,"unit":"°C",'
            '"timestamp":1716895200}'
        )
        with pytest.raises(ContractError) as exc:
            parse_message(VALID_TOPIC, payload)
        assert exc.value.code == CODE_PAYLOAD_FIELD_TYPE

    def test_metadata_as_string(self):
        payload = (
            '{"kind":"temperature","value":22.4,"unit":"°C",'
            '"timestamp":"2026-05-28T10:00:00Z","metadata":"oops"}'
        )
        with pytest.raises(ContractError) as exc:
            parse_message(VALID_TOPIC, payload)
        assert exc.value.code == CODE_PAYLOAD_FIELD_TYPE

    def test_metadata_value_not_string(self):
        payload = (
            '{"kind":"temperature","value":22.4,"unit":"°C",'
            '"timestamp":"2026-05-28T10:00:00Z","metadata":{"firmware":42}}'
        )
        with pytest.raises(ContractError) as exc:
            parse_message(VALID_TOPIC, payload)
        assert exc.value.code == CODE_PAYLOAD_FIELD_TYPE


class TestParseMessageWrongFormats:
    def test_kind_with_uppercase(self):
        payload = (
            '{"kind":"Température","value":22.4,"unit":"°C",'
            '"timestamp":"2026-05-28T10:00:00Z"}'
        )
        with pytest.raises(ContractError) as exc:
            parse_message(VALID_TOPIC, payload)
        assert exc.value.code == CODE_PAYLOAD_VALUE_FORMAT

    def test_timestamp_with_space_separator(self):
        payload = (
            '{"kind":"temperature","value":22.4,"unit":"°C",'
            '"timestamp":"2026-05-28 12:00:00"}'
        )
        with pytest.raises(ContractError) as exc:
            parse_message(VALID_TOPIC, payload)
        assert exc.value.code == CODE_PAYLOAD_VALUE_FORMAT

    def test_timestamp_without_z(self):
        payload = (
            '{"kind":"temperature","value":22.4,"unit":"°C",'
            '"timestamp":"2026-05-28T10:00:00"}'
        )
        with pytest.raises(ContractError) as exc:
            parse_message(VALID_TOPIC, payload)
        assert exc.value.code == CODE_PAYLOAD_VALUE_FORMAT

    def test_timestamp_with_offset(self):
        # Le contrat exige Z, pas +00:00 ni autre offset.
        payload = (
            '{"kind":"temperature","value":22.4,"unit":"°C",'
            '"timestamp":"2026-05-28T10:00:00+02:00"}'
        )
        with pytest.raises(ContractError) as exc:
            parse_message(VALID_TOPIC, payload)
        assert exc.value.code == CODE_PAYLOAD_VALUE_FORMAT

    def test_timestamp_invalid_calendar(self):
        # Syntaxe OK mais date impossible (99 février).
        payload = (
            '{"kind":"temperature","value":22.4,"unit":"°C",'
            '"timestamp":"2026-02-99T10:00:00Z"}'
        )
        with pytest.raises(ContractError) as exc:
            parse_message(VALID_TOPIC, payload)
        assert exc.value.code == CODE_PAYLOAD_VALUE_FORMAT


class TestContractError:
    def test_code_attribute_exposed(self):
        err = ContractError(CODE_TOPIC_PATTERN, "test")
        assert err.code == CODE_TOPIC_PATTERN
        assert err.message == "test"

    def test_str_contains_code(self):
        err = ContractError(CODE_PAYLOAD_PARSE, "bad json")
        assert "PAYLOAD_PARSE" in str(err)
        assert "bad json" in str(err)


# ═══════════════════════════════════════════════════════════════════════════
# Subscriber — wiring sans broker
# ═══════════════════════════════════════════════════════════════════════════


class TestMqttSubscriberConstruction:
    def test_uses_injected_client_factory(self):
        fake_client = MagicMock()
        factory = MagicMock(return_value=fake_client)

        cfg = _make_config()
        sub = MqttSubscriber(cfg, on_measurement=lambda m: None, client_factory=factory)

        factory.assert_called_once_with(cfg)
        assert sub.client is fake_client

    def test_assigns_paho_callbacks(self):
        fake_client = MagicMock()
        cfg = _make_config()
        MqttSubscriber(
            cfg,
            on_measurement=lambda m: None,
            client_factory=lambda c: fake_client,
        )
        # paho 2.x callbacks attendus.
        assert fake_client.on_connect is not None
        assert fake_client.on_message is not None

    def test_no_auth_when_username_none(self):
        fake_client = MagicMock()
        cfg = _make_config(mqtt_username=None, mqtt_password=None)
        MqttSubscriber(
            cfg,
            on_measurement=lambda m: None,
            client_factory=lambda c: fake_client,
        )
        fake_client.username_pw_set.assert_not_called()

    def test_auth_set_when_username_provided(self):
        fake_client = MagicMock()
        cfg = _make_config(mqtt_username="forge", mqtt_password="s3cr3t")
        MqttSubscriber(
            cfg,
            on_measurement=lambda m: None,
            client_factory=lambda c: fake_client,
        )
        fake_client.username_pw_set.assert_called_once_with("forge", "s3cr3t")


class TestHandleMessageDispatch:
    def test_valid_message_calls_on_measurement(self):
        received: list[Measurement] = []
        cfg = _make_config()
        sub = MqttSubscriber(
            cfg,
            on_measurement=received.append,
            client_factory=lambda c: MagicMock(),
        )
        sub.handle_message(VALID_TOPIC, VALID_PAYLOAD_MINIMAL.encode("utf-8"))

        assert len(received) == 1
        assert received[0].site == "atelier"
        assert received[0].device_id == "esp32-001"
        assert received[0].kind == "temperature"

    def test_handles_str_payload(self):
        received: list[Measurement] = []
        cfg = _make_config()
        sub = MqttSubscriber(
            cfg,
            on_measurement=received.append,
            client_factory=lambda c: MagicMock(),
        )
        sub.handle_message(VALID_TOPIC, VALID_PAYLOAD_MINIMAL)
        assert len(received) == 1

    def test_invalid_topic_calls_error_callback(self):
        errors: list[tuple] = []
        cfg = _make_config()
        sub = MqttSubscriber(
            cfg,
            on_measurement=lambda m: None,
            on_contract_error=lambda exc, topic, payload: errors.append(
                (exc.code, topic, payload)
            ),
            client_factory=lambda c: MagicMock(),
        )
        sub.handle_message("bad/topic", VALID_PAYLOAD_MINIMAL.encode("utf-8"))

        assert len(errors) == 1
        code, topic, payload = errors[0]
        assert code == CODE_TOPIC_PATTERN
        assert topic == "bad/topic"
        assert payload == VALID_PAYLOAD_MINIMAL.encode("utf-8")

    def test_invalid_payload_calls_error_callback(self):
        errors: list[str] = []
        cfg = _make_config()
        sub = MqttSubscriber(
            cfg,
            on_measurement=lambda m: None,
            on_contract_error=lambda exc, t, p: errors.append(exc.code),
            client_factory=lambda c: MagicMock(),
        )
        sub.handle_message(VALID_TOPIC, b"not json")
        assert errors == [CODE_PAYLOAD_PARSE]

    def test_error_without_callback_just_logs(self, caplog):
        cfg = _make_config()
        sub = MqttSubscriber(
            cfg,
            on_measurement=lambda m: None,
            on_contract_error=None,
            client_factory=lambda c: MagicMock(),
        )
        with caplog.at_level(logging.WARNING, logger="forge_mvc_iot.mqtt.subscriber"):
            sub.handle_message(VALID_TOPIC, b"not json")
        assert any(
            "PAYLOAD_PARSE" in rec.getMessage() for rec in caplog.records
        ), "Une erreur de contrat sans callback doit être loguée"

    def test_valid_message_does_not_trigger_error_callback(self):
        errors: list = []
        cfg = _make_config()
        sub = MqttSubscriber(
            cfg,
            on_measurement=lambda m: None,
            on_contract_error=lambda *a: errors.append(a),
            client_factory=lambda c: MagicMock(),
        )
        sub.handle_message(VALID_TOPIC, VALID_PAYLOAD_MINIMAL)
        assert errors == []


class TestPahoMessageCallback:
    """_on_paho_message route correctement vers handle_message."""

    def test_paho_callback_routes_to_handle_message(self):
        received: list[Measurement] = []
        cfg = _make_config()
        sub = MqttSubscriber(
            cfg,
            on_measurement=received.append,
            client_factory=lambda c: MagicMock(),
        )

        # Simuler le message paho.
        fake_paho_message = Mock()
        fake_paho_message.topic = VALID_TOPIC
        fake_paho_message.payload = VALID_PAYLOAD_MINIMAL.encode("utf-8")
        sub._on_paho_message(client=Mock(), userdata=None, message=fake_paho_message)

        assert len(received) == 1


class TestSubscribeOnConnect:
    """_on_paho_connect s'abonne au topic configuré uniquement si OK."""

    def test_subscribes_on_success(self):
        fake_client = MagicMock()
        cfg = _make_config(mqtt_topic="forge/atelier/+/telemetry")
        sub = MqttSubscriber(
            cfg,
            on_measurement=lambda m: None,
            client_factory=lambda c: fake_client,
        )
        sub._on_paho_connect(
            client=fake_client, userdata=None, flags=None,
            reason_code=0,
        )
        fake_client.subscribe.assert_called_once_with("forge/atelier/+/telemetry")

    def test_does_not_subscribe_on_failure(self, caplog):
        fake_client = MagicMock()
        cfg = _make_config()
        sub = MqttSubscriber(
            cfg,
            on_measurement=lambda m: None,
            client_factory=lambda c: fake_client,
        )
        with caplog.at_level(logging.WARNING):
            sub._on_paho_connect(
                client=fake_client, userdata=None, flags=None,
                reason_code=5,  # not authorised
            )
        fake_client.subscribe.assert_not_called()


class TestLifecycleDelegation:
    """connect/disconnect/loop_* délèguent au client paho."""

    @pytest.mark.parametrize(
        "method, expected",
        [
            ("disconnect", "disconnect"),
            ("loop_forever", "loop_forever"),
            ("loop_start", "loop_start"),
            ("loop_stop", "loop_stop"),
        ],
    )
    def test_method_delegates(self, method, expected):
        fake_client = MagicMock()
        cfg = _make_config()
        sub = MqttSubscriber(
            cfg,
            on_measurement=lambda m: None,
            client_factory=lambda c: fake_client,
        )
        getattr(sub, method)()
        getattr(fake_client, expected).assert_called_once()

    def test_connect_passes_host_and_port(self):
        fake_client = MagicMock()
        cfg = _make_config(mqtt_host="broker.lan", mqtt_port=8883)
        sub = MqttSubscriber(
            cfg,
            on_measurement=lambda m: None,
            client_factory=lambda c: fake_client,
        )
        sub.connect()
        fake_client.connect.assert_called_once_with("broker.lan", 8883)


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous périmètre
# ═══════════════════════════════════════════════════════════════════════════


class TestPyprojectDeclaresPaho:
    """Le ticket IOT-MQTT-SUBSCRIBER-001 ouvre la dépendance paho-mqtt."""

    def test_paho_mqtt_listed_in_dependencies(self):
        data = tomllib.loads(IOT_PYPROJECT.read_text(encoding="utf-8"))
        deps = data["project"]["dependencies"]
        assert any("paho-mqtt" in d for d in deps), (
            "forge-mvc-iot doit déclarer paho-mqtt parmi ses dépendances"
        )

    def test_forge_mvc_still_in_dependencies(self):
        data = tomllib.loads(IOT_PYPROJECT.read_text(encoding="utf-8"))
        deps = data["project"]["dependencies"]
        assert any(
            d.startswith("forge-mvc") and "iot" not in d for d in deps
        ), "forge-mvc-iot doit continuer à dépendre de forge-mvc"


class TestNoCoreImportsIot:
    """Garde-fou : core/ ne dépend toujours pas de forge_mvc_iot."""

    def test_no_core_module_imports_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(PROJECT_ROOT))
        assert not offenders, offenders
