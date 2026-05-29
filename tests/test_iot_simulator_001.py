"""Tests du simulateur MQTT Forge IoT — IOT-SIMULATOR-001.

`forge iot:simulate` publie des mesures **factices** mais **conformes au
contrat** `forge/{site}/{device_id}/telemetry`, sans capteur ni broker
réel. Les tests vérifient :

- topic et payload conformes (validés par `parse_message`) ;
- timestamp UTC suffixe `Z` ;
- bornes `--count` (1..1000) et `--interval` (0..60) ;
- le client MQTT mocké reçoit connect / publish / disconnect ;
- le mot de passe n'apparaît jamais dans la sortie ;
- `paho` n'est importé que lorsque la commande publie réellement ;
- `forge iot:simulate --help` fonctionne et `forge help` liste la
  commande ;
- aucun import IoT dans `core/`.

Aucun broker requis : `publish_measurements` accepte `client_factory`,
`now` et `sleep` injectables.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from forge_mvc_iot.cli import simulate as simulate_module
from forge_mvc_iot.cli.simulate import (
    ArgumentError,
    DEFAULT_SOURCE,
    MAX_COUNT,
    MAX_INTERVAL,
    SimulateOptions,
    build_payload,
    build_topic,
    main,
    parse_args,
    publish_measurements,
    utc_timestamp,
)
from forge_mvc_iot.config import IotConfig
from forge_mvc_iot.mqtt.contract import parse_message

PROJECT_ROOT = Path(__file__).parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"
SIMULATE_FILE = (
    PROJECT_ROOT / "packages" / "forge-mvc-iot" / "forge_mvc_iot"
    / "cli" / "simulate.py"
)
CORE_DIR = PROJECT_ROOT / "core"
HELP_FILE = PROJECT_ROOT / "forge_cli" / "help.py"


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
    """Faux client MQTT : enregistre les appels, ne touche aucun réseau."""

    def __init__(self, *, connect_raises: Exception | None = None) -> None:
        self.calls: list[str] = []
        self.published: list[tuple[str, bytes, int]] = []
        self.credentials: tuple[str, str | None] | None = None
        self.connect_target: tuple[str, int] | None = None
        self._connect_raises = connect_raises

    def username_pw_set(self, username, password=None):
        self.calls.append("username_pw_set")
        self.credentials = (username, password)

    def connect(self, host, port):
        self.calls.append("connect")
        self.connect_target = (host, port)
        if self._connect_raises is not None:
            raise self._connect_raises

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


FIXED_NOW = lambda: datetime(2026, 5, 29, 10, 0, 0, tzinfo=timezone.utc)  # noqa: E731


# ═══════════════════════════════════════════════════════════════════════════
# Construction des messages
# ═══════════════════════════════════════════════════════════════════════════


class TestBuildTopic:
    def test_default_topic(self):
        assert build_topic("atelier", "esp32-001") == (
            "forge/atelier/esp32-001/telemetry"
        )


class TestBuildPayload:
    def test_payload_shape(self):
        payload = build_payload(
            kind="temperature", value=22.4, unit="°C",
            timestamp="2026-05-29T10:00:00Z",
        )
        assert payload["kind"] == "temperature"
        assert payload["value"] == 22.4
        assert payload["unit"] == "°C"
        assert payload["timestamp"] == "2026-05-29T10:00:00Z"
        assert payload["metadata"] == {"source": DEFAULT_SOURCE}


class TestUtcTimestamp:
    def test_ends_with_z(self):
        ts = utc_timestamp(now=FIXED_NOW)
        assert ts == "2026-05-29T10:00:00Z"
        assert ts.endswith("Z")

    def test_converts_other_timezone_to_utc(self):
        plus_two = timezone(timedelta(hours=2))
        ts = utc_timestamp(now=lambda: datetime(2026, 5, 29, 12, 0, 0, tzinfo=plus_two))
        assert ts == "2026-05-29T10:00:00Z"

    def test_default_now_is_utc_z(self):
        ts = utc_timestamp()
        assert ts.endswith("Z")
        # Doit être parsable par le contrat.
        assert ts[4] == "-" and ts[10] == "T"


class TestPayloadIsContractValid:
    def test_default_payload_parses(self):
        ts = utc_timestamp(now=FIXED_NOW)
        payload = build_payload(
            kind="temperature", value=22.4, unit="°C", timestamp=ts,
        )
        m = parse_message(
            "forge/atelier/esp32-001/telemetry", json.dumps(payload),
        )
        assert m.site == "atelier"
        assert m.device_id == "esp32-001"
        assert m.kind == "temperature"
        assert m.value == 22.4
        assert m.unit == "°C"
        assert m.timestamp == ts
        assert m.metadata == {"source": DEFAULT_SOURCE}

    def test_custom_payload_parses(self):
        ts = utc_timestamp(now=FIXED_NOW)
        payload = build_payload(kind="humidity", value=55, unit="%", timestamp=ts)
        m = parse_message("forge/labo/capteur-2/telemetry", json.dumps(payload))
        assert m.kind == "humidity"
        assert m.value == 55
        assert m.unit == "%"


# ═══════════════════════════════════════════════════════════════════════════
# parse_args
# ═══════════════════════════════════════════════════════════════════════════


class TestParseArgsDefaults:
    def test_defaults(self):
        opts = parse_args([])
        assert opts == SimulateOptions()
        assert opts.site == "atelier"
        assert opts.device == "esp32-001"
        assert opts.kind == "temperature"
        assert opts.value == 22.4
        assert opts.unit == "°C"
        assert opts.count == 1
        assert opts.interval == 1.0


class TestParseArgsOptions:
    def test_all_string_options(self):
        opts = parse_args([
            "--site", "labo", "--device", "esp32-009",
            "--kind", "humidity", "--unit", "%",
        ])
        assert opts.site == "labo"
        assert opts.device == "esp32-009"
        assert opts.kind == "humidity"
        assert opts.unit == "%"

    def test_value_parsed_as_float(self):
        assert parse_args(["--value", "55"]).value == 55.0
        assert parse_args(["--value", "12.5"]).value == 12.5

    def test_value_invalid_raises(self):
        with pytest.raises(ArgumentError):
            parse_args(["--value", "abc"])

    def test_unknown_option_raises(self):
        with pytest.raises(ArgumentError):
            parse_args(["--nope", "x"])

    def test_missing_value_raises(self):
        with pytest.raises(ArgumentError):
            parse_args(["--site"])


class TestCountBounds:
    @pytest.mark.parametrize("bad", ["0", "-1", str(MAX_COUNT + 1), "abc"])
    def test_invalid_count_rejected(self, bad):
        with pytest.raises(ArgumentError):
            parse_args(["--count", bad])

    @pytest.mark.parametrize("ok", ["1", "10", str(MAX_COUNT)])
    def test_valid_count_accepted(self, ok):
        assert parse_args(["--count", ok]).count == int(ok)


class TestIntervalBounds:
    @pytest.mark.parametrize("bad", ["-1", str(MAX_INTERVAL + 1), "abc"])
    def test_invalid_interval_rejected(self, bad):
        with pytest.raises(ArgumentError):
            parse_args(["--interval", bad])

    @pytest.mark.parametrize("ok", ["0", "1", str(MAX_INTERVAL)])
    def test_valid_interval_accepted(self, ok):
        assert parse_args(["--interval", ok]).interval == float(ok)


# ═══════════════════════════════════════════════════════════════════════════
# publish_measurements
# ═══════════════════════════════════════════════════════════════════════════


class TestPublishMeasurements:
    def test_connect_publish_disconnect(self, capsys):
        client = _FakeClient()
        published = publish_measurements(
            _config(), SimulateOptions(count=1),
            client_factory=_factory(client), sleep=lambda _s: None,
        )
        capsys.readouterr()
        assert "connect" in client.calls
        assert "publish" in client.calls
        assert "disconnect" in client.calls
        assert len(published) == 1

    def test_topic_is_contractual(self, capsys):
        client = _FakeClient()
        publish_measurements(
            _config(), SimulateOptions(site="labo", device="capteur-3"),
            client_factory=_factory(client), sleep=lambda _s: None,
        )
        capsys.readouterr()
        topic = client.published[0][0]
        assert topic == "forge/labo/capteur-3/telemetry"

    def test_count_messages_published(self, capsys):
        client = _FakeClient()
        publish_measurements(
            _config(), SimulateOptions(count=5, interval=0),
            client_factory=_factory(client), sleep=lambda _s: None,
        )
        capsys.readouterr()
        assert client.calls.count("publish") == 5

    def test_sleep_called_between_messages(self, capsys):
        sleeps: list[float] = []
        client = _FakeClient()
        publish_measurements(
            _config(), SimulateOptions(count=3, interval=1.0),
            client_factory=_factory(client), sleep=sleeps.append,
        )
        capsys.readouterr()
        # count-1 intervalles entre 3 messages.
        assert sleeps == [1.0, 1.0]

    def test_no_sleep_for_single_message(self, capsys):
        sleeps: list[float] = []
        client = _FakeClient()
        publish_measurements(
            _config(), SimulateOptions(count=1, interval=1.0),
            client_factory=_factory(client), sleep=sleeps.append,
        )
        capsys.readouterr()
        assert sleeps == []

    def test_username_pw_set_when_username(self, capsys):
        client = _FakeClient()
        publish_measurements(
            _config(mqtt_username="forge", mqtt_password="s3cr3t"),
            SimulateOptions(count=1),
            client_factory=_factory(client), sleep=lambda _s: None,
        )
        capsys.readouterr()
        assert client.credentials == ("forge", "s3cr3t")

    def test_published_payload_is_contract_valid(self, capsys):
        client = _FakeClient()
        publish_measurements(
            _config(), SimulateOptions(count=1),
            client_factory=_factory(client), now=FIXED_NOW,
            sleep=lambda _s: None,
        )
        capsys.readouterr()
        topic, body, _qos = client.published[0]
        # Le message réellement publié doit passer le contrat.
        m = parse_message(topic, body)
        assert m.kind == "temperature"
        assert m.timestamp.endswith("Z")


class TestPasswordNeverLeaked:
    def test_password_absent_from_output(self, capsys):
        client = _FakeClient()
        publish_measurements(
            _config(mqtt_username="forge", mqtt_password="supersecret-pwd-xyz"),
            SimulateOptions(count=1),
            client_factory=_factory(client), sleep=lambda _s: None,
        )
        out = capsys.readouterr().out
        assert "supersecret-pwd-xyz" not in out


# ═══════════════════════════════════════════════════════════════════════════
# main
# ═══════════════════════════════════════════════════════════════════════════


class TestMain:
    def test_success_exit_0(self, monkeypatch, capsys):
        client = _FakeClient()
        monkeypatch.setattr(
            "forge_mvc_iot.config.load_iot_config", lambda env=None: _config(),
        )
        monkeypatch.setattr(
            simulate_module, "_default_client_factory", _factory(client),
        )
        rc = main(["--count", "2", "--interval", "0"])
        out = capsys.readouterr().out
        assert rc == 0
        assert client.calls.count("publish") == 2
        assert "connect" in client.calls and "disconnect" in client.calls
        assert "publiée(s)" in out

    def test_invalid_count_exit_2(self, capsys):
        rc = main(["--count", "0"])
        err = capsys.readouterr().err
        assert rc == 2
        assert "ERREUR" in err

    def test_non_contractual_site_exit_2_without_connection(
        self, monkeypatch, capsys,
    ):
        client = _FakeClient()
        monkeypatch.setattr(
            "forge_mvc_iot.config.load_iot_config", lambda env=None: _config(),
        )
        monkeypatch.setattr(
            simulate_module, "_default_client_factory", _factory(client),
        )
        # 'Atelier' contient une majuscule : hors slug topic.
        rc = main(["--site", "Atelier"])
        err = capsys.readouterr().err
        assert rc == 2
        assert "contrat" in err.lower()
        # Aucune connexion ne doit avoir été ouverte.
        assert "connect" not in client.calls

    def test_config_invalid_exit_1(self, monkeypatch, capsys):
        def _raise(env=None):
            raise ValueError("FORGE_IOT_MQTT_HOST ne peut pas être vide")

        monkeypatch.setattr("forge_mvc_iot.config.load_iot_config", _raise)
        rc = main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "configuration" in err.lower()

    def test_connection_failure_exit_1_sober(self, monkeypatch, capsys):
        client = _FakeClient(connect_raises=ConnectionRefusedError(111))
        monkeypatch.setattr(
            "forge_mvc_iot.config.load_iot_config", lambda env=None: _config(),
        )
        monkeypatch.setattr(
            simulate_module, "_default_client_factory", _factory(client),
        )
        rc = main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "Traceback" not in err
        assert "publication MQTT impossible" in err


# ═══════════════════════════════════════════════════════════════════════════
# Aide CLI (--help et listing)
# ═══════════════════════════════════════════════════════════════════════════


class TestCliHelp:
    def test_simulate_help_renders(self):
        result = subprocess.run(
            [sys.executable, str(FORGE_PY), "iot:simulate", "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "iot:simulate" in result.stdout
        assert "--count" in result.stdout

    def test_forge_help_lists_simulate(self):
        result = subprocess.run(
            [sys.executable, str(FORGE_PY), "help"],
            capture_output=True, text=True, timeout=30,
        )
        assert "iot:simulate" in result.stdout

    def test_help_py_lists_simulate(self):
        assert "iot:simulate" in HELP_FILE.read_text(encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous périmètre
# ═══════════════════════════════════════════════════════════════════════════


class TestPahoLazyImport:
    def test_paho_not_imported_at_module_level(self):
        src = SIMULATE_FILE.read_text(encoding="utf-8")
        head = src.split("\ndef ", 1)[0]
        head_imports = [
            line for line in head.splitlines()
            if line.lstrip().startswith(("import ", "from "))
        ]
        offenders = [line for line in head_imports if "paho" in line.lower()]
        assert not offenders, offenders

    def test_paho_absent_from_sys_modules_without_publishing(self):
        code = (
            "import sys\n"
            "from forge_mvc_iot.cli import simulate\n"
            "simulate.parse_args(['--count', '5'])\n"
            "simulate.build_payload(kind='t', value=1, unit='C',"
            " timestamp='2026-01-01T00:00:00Z')\n"
            "print('paho' in sys.modules)\n"
        )
        out = subprocess.check_output(
            [sys.executable, "-c", code], stderr=subprocess.STDOUT,
        )
        assert out.strip().endswith(b"False"), out


class TestNoCoreImportsIot:
    def test_no_core_module_imports_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(PROJECT_ROOT))
        assert not offenders, offenders
