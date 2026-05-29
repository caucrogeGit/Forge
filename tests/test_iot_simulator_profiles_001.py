"""Profils pédagogiques de ``forge iot:simulate`` — IOT-SIMULATOR-PROFILES-001.

Le simulateur gagne une option ``--profile`` qui fournit des valeurs par
défaut prêtes à l'emploi (kind / value / unit) pour quatre profils :
``temperature``, ``humidity``, ``presence``, ``energy``. Les tests
vérifient :

- chaque profil produit le bon ``kind`` / ``unit`` ;
- chaque payload reste accepté par ``parse_message`` (contrat MQTT) ;
- ``metadata.profile`` est présent quand un profil est actif ;
- ``--kind`` / ``--value`` / ``--unit`` surchargent le profil (quel que
  soit l'ordre) ;
- un profil inconnu → exit 2 avec la liste des profils ;
- le comportement **sans** ``--profile`` reste inchangé ;
- le mot de passe n'est jamais affiché ;
- aucune autre brique IoT (subscriber / repository / API) n'est modifiée.

Aucun broker requis : ``publish_measurements`` accepte ``client_factory``,
``now`` et ``sleep`` injectables.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.cli import simulate as simulate_module
from forge_mvc_iot.cli.simulate import (
    DEFAULT_SOURCE,
    SIMULATION_PROFILES,
    SimulateOptions,
    build_payload,
    main,
    parse_args,
    publish_measurements,
)
from forge_mvc_iot.config import IotConfig
from forge_mvc_iot.mqtt.contract import parse_message

PROJECT_ROOT = Path(__file__).parent.parent
SIMULATE_FILE = (
    PROJECT_ROOT / "packages" / "forge-mvc-iot" / "forge_mvc_iot"
    / "cli" / "simulate.py"
)


FIXED_NOW = lambda: datetime(2026, 5, 29, 10, 0, 0, tzinfo=timezone.utc)  # noqa: E731


# ── Helpers ──────────────────────────────────────────────────────────────────


def _config(**overrides) -> IotConfig:
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


class _FakeClient:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.published: list[tuple[str, bytes, int]] = []

    def username_pw_set(self, username, password=None):
        self.calls.append("username_pw_set")

    def connect(self, host, port):
        self.calls.append("connect")

    def loop_start(self):
        self.calls.append("loop_start")

    def publish(self, topic, payload, qos=0):
        self.calls.append("publish")
        self.published.append((topic, payload, qos))
        return None

    def loop_stop(self):
        self.calls.append("loop_stop")

    def disconnect(self):
        self.calls.append("disconnect")


def _factory(client: _FakeClient):
    def _make(_config):
        return client
    return _make


# ═══════════════════════════════════════════════════════════════════════════
# parse_args — profils
# ═══════════════════════════════════════════════════════════════════════════


class TestProfileDefaults:
    @pytest.mark.parametrize(
        "name,kind,unit",
        [
            ("temperature", "temperature", "°C"),
            ("humidity", "humidity", "%"),
            ("presence", "presence", "state"),
            ("energy", "energy", "W"),
        ],
    )
    def test_profile_sets_kind_and_unit(self, name, kind, unit):
        opts = parse_args(["--profile", name])
        assert opts.kind == kind
        assert opts.unit == unit
        assert opts.profile == name

    def test_profile_sets_value(self):
        assert parse_args(["--profile", "energy"]).value == 120.5
        assert parse_args(["--profile", "presence"]).value == 1.0

    def test_all_four_profiles_exist(self):
        assert set(SIMULATION_PROFILES) == {
            "temperature", "humidity", "presence", "energy",
        }


class TestProfileOverrides:
    def test_value_overrides_profile(self):
        opts = parse_args(["--profile", "temperature", "--value", "24.8"])
        assert opts.kind == "temperature"
        assert opts.value == 24.8
        assert opts.unit == "°C"

    def test_kind_and_unit_override_profile(self):
        opts = parse_args([
            "--profile", "humidity", "--kind", "co2", "--unit", "ppm",
        ])
        assert opts.kind == "co2"
        assert opts.unit == "ppm"
        # value reste celle du profil humidity tant qu'on ne la surcharge pas.
        assert opts.value == 55.0

    def test_override_wins_regardless_of_order(self):
        # --kind avant --profile : la surcharge explicite doit gagner.
        before = parse_args(["--kind", "co2", "--profile", "humidity"])
        after = parse_args(["--profile", "humidity", "--kind", "co2"])
        assert before.kind == "co2"
        assert after.kind == "co2"


class TestUnknownProfile:
    def test_unknown_profile_message_lists_available(self):
        from forge_mvc_iot.cli.simulate import ArgumentError
        with pytest.raises(ArgumentError) as excinfo:
            parse_args(["--profile", "unknown"])
        msg = str(excinfo.value)
        assert "Profil inconnu : unknown" in msg
        for name in ("temperature", "humidity", "presence", "energy"):
            assert name in msg

    def test_unknown_profile_exit_2(self, capsys):
        rc = main(["--profile", "unknown"])
        err = capsys.readouterr().err
        assert rc == 2
        assert "Profil inconnu : unknown" in err
        assert "Profils disponibles" in err


class TestNoProfileUnchanged:
    def test_defaults_unchanged_without_profile(self):
        opts = parse_args([])
        assert opts == SimulateOptions()
        assert opts.profile is None
        assert opts.kind == "temperature"
        assert opts.unit == "°C"

    def test_payload_without_profile_has_no_profile_metadata(self):
        payload = build_payload(
            kind="temperature", value=22.4, unit="°C",
            timestamp="2026-05-29T10:00:00Z",
        )
        assert payload["metadata"] == {"source": DEFAULT_SOURCE}
        assert "profile" not in payload["metadata"]


# ═══════════════════════════════════════════════════════════════════════════
# build_payload — metadata.profile
# ═══════════════════════════════════════════════════════════════════════════


class TestProfileMetadata:
    def test_profile_added_to_metadata(self):
        payload = build_payload(
            kind="temperature", value=22.4, unit="°C",
            timestamp="2026-05-29T10:00:00Z", profile="temperature",
        )
        assert payload["metadata"]["source"] == DEFAULT_SOURCE
        assert payload["metadata"]["profile"] == "temperature"

    def test_profile_metadata_is_string(self):
        # Le contrat exige des valeurs string dans metadata.
        payload = build_payload(
            kind="energy", value=120.5, unit="W",
            timestamp="2026-05-29T10:00:00Z", profile="energy",
        )
        assert isinstance(payload["metadata"]["profile"], str)


# ═══════════════════════════════════════════════════════════════════════════
# Conformité au contrat MQTT
# ═══════════════════════════════════════════════════════════════════════════


class TestProfilesAreContractValid:
    @pytest.mark.parametrize("name", ["temperature", "humidity", "presence", "energy"])
    def test_each_profile_payload_parses(self, name):
        opts = parse_args(["--profile", name])
        payload = build_payload(
            kind=opts.kind, value=opts.value, unit=opts.unit,
            timestamp="2026-05-29T10:00:00Z", profile=opts.profile,
        )
        m = parse_message(
            "forge/atelier/esp32-001/telemetry", json.dumps(payload),
        )
        assert m.kind == SIMULATION_PROFILES[name]["kind"]
        assert m.unit == SIMULATION_PROFILES[name]["unit"]
        assert m.metadata["profile"] == name


# ═══════════════════════════════════════════════════════════════════════════
# Bout-en-bout via main / publish_measurements
# ═══════════════════════════════════════════════════════════════════════════


class TestMainWithProfile:
    def test_profile_humidity_publishes_count(self, monkeypatch, capsys):
        client = _FakeClient()
        monkeypatch.setattr(
            "forge_mvc_iot.config.load_iot_config", lambda env=None: _config(),
        )
        monkeypatch.setattr(
            simulate_module, "_default_client_factory", _factory(client),
        )
        rc = main(["--profile", "humidity", "--count", "3", "--interval", "0"])
        out = capsys.readouterr().out
        assert rc == 0
        assert client.calls.count("publish") == 3
        # Les messages publiés sont conformes et portent kind=humidity.
        topic, body, _qos = client.published[0]
        m = parse_message(topic, body)
        assert m.kind == "humidity"
        assert m.unit == "%"
        assert m.metadata["profile"] == "humidity"
        assert "publiée(s)" in out

    def test_publish_carries_profile_metadata(self, capsys):
        client = _FakeClient()
        published = publish_measurements(
            _config(), parse_args(["--profile", "presence"]),
            client_factory=_factory(client), now=FIXED_NOW,
            sleep=lambda _s: None,
        )
        capsys.readouterr()
        _topic, payload = published[0]
        assert payload["metadata"]["profile"] == "presence"
        assert payload["kind"] == "presence"

    def test_password_never_leaked_with_profile(self, capsys):
        client = _FakeClient()
        publish_measurements(
            _config(mqtt_username="forge", mqtt_password="supersecret-xyz"),
            parse_args(["--profile", "energy"]),
            client_factory=_factory(client), sleep=lambda _s: None,
        )
        out = capsys.readouterr().out
        assert "supersecret-xyz" not in out


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous périmètre — aucune autre brique modifiée
# ═══════════════════════════════════════════════════════════════════════════


class TestScopeGuards:
    def test_simulator_does_not_touch_other_bricks(self):
        src = SIMULATE_FILE.read_text(encoding="utf-8")
        # Pas de subscriber, repository, API HTTP, ni écriture base.
        assert "MqttSubscriber" not in src
        assert "IotEventRepository" not in src
        assert "register_iot_routes" not in src
        assert "forge_mvc_iot.http" not in src

    def test_no_complex_simulation_engine(self):
        # Profils simples : pas de random, pas de fichier de scénario YAML.
        src = SIMULATE_FILE.read_text(encoding="utf-8")
        assert "import random" not in src
        assert "yaml" not in src.lower()
