"""Branchement TLS dans les clients MQTT Forge IoT — IOT-MQTT-TLS-CLIENTS-001.

Vérifie que la configuration TLS (``IOT-CONFIG-TLS-001``) est réellement
consommée par les trois clients MQTT — ``MqttSubscriber``,
``forge iot:doctor --mqtt`` (``check_mqtt_broker``) et
``forge iot:simulate`` (``publish_measurements``) — via le helper
centralisé ``forge_mvc_iot.mqtt.tls.configure_tls`` :

- TLS désactivé → ``tls_set`` **jamais** appelé (comportement inchangé) ;
- TLS activé sans CA → ``tls_set()`` (sans ``ca_certs``) ;
- TLS activé avec CA → ``tls_set(ca_certs=...)`` ;
- ``tls_set`` appelé **avant** ``connect`` ;
- jamais de ``tls_insecure_set`` ;
- ni le chemin CA ni le mot de passe ne fuient dans la sortie utilisateur.

Aucun broker requis : les clients sont injectés via ``client_factory``.
"""

from __future__ import annotations

from pathlib import Path

from forge_mvc_iot.cli.doctor import check_mqtt_broker
from forge_mvc_iot.cli.simulate import SimulateOptions, publish_measurements
from forge_mvc_iot.config import load_iot_config
from forge_mvc_iot.mqtt.subscriber import MqttSubscriber
from forge_mvc_iot.mqtt.tls import configure_tls

PROJECT_ROOT = Path(__file__).parent.parent
PKG = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "forge_mvc_iot"
TLS_FILE = PKG / "mqtt" / "tls.py"
SUBSCRIBER_FILE = PKG / "mqtt" / "subscriber.py"
DOCTOR_FILE = PKG / "cli" / "doctor.py"
SIMULATE_FILE = PKG / "cli" / "simulate.py"

CA_PATH = "/etc/ssl/certs/mosquitto-ca-secret-xyz.crt"
SECRET_PWD = "supersecret-tls-pwd-123"


# ── Faux client MQTT (aucun broker, aucun paho) ─────────────────────────────


class _FakeTlsClient:
    """Faux client paho : enregistre les appels (dont ``tls_set``)."""

    def __init__(self, *, reason_code=0, fire_connack: bool = True) -> None:
        self.calls: list[str] = []
        self.tls_kwargs: dict | None = None
        self.tls_args: tuple | None = None
        self.on_connect = None
        self.on_message = None
        self._reason_code = reason_code
        self._fire_connack = fire_connack

    def tls_set(self, *args, **kwargs):
        self.calls.append("tls_set")
        self.tls_args = args
        self.tls_kwargs = kwargs

    def tls_insecure_set(self, *args, **kwargs):  # ne doit jamais être appelé
        self.calls.append("tls_insecure_set")

    def username_pw_set(self, username, password=None):
        self.calls.append("username_pw_set")

    def connect(self, host, port):
        self.calls.append("connect")

    def loop_start(self):
        self.calls.append("loop_start")
        if self._fire_connack and self.on_connect is not None:
            self.on_connect(self, None, None, self._reason_code)

    def loop_forever(self):
        self.calls.append("loop_forever")

    def subscribe(self, topic):
        self.calls.append("subscribe")

    def publish(self, topic, payload, qos=0):
        self.calls.append("publish")
        return None

    def loop_stop(self):
        self.calls.append("loop_stop")

    def disconnect(self):
        self.calls.append("disconnect")


def _config(*, tls=None, ca=None, **overrides):
    env = {
        "FORGE_IOT_MQTT_HOST": "mqtt.example.net",
        "FORGE_IOT_MQTT_PORT": "8883",
    }
    if tls is not None:
        env["FORGE_IOT_MQTT_TLS_ENABLED"] = tls
    if ca is not None:
        env["FORGE_IOT_MQTT_TLS_CA_FILE"] = ca
    env.update(overrides)
    return load_iot_config(env)


def _factory(client: _FakeTlsClient):
    def _make(_config):
        return client
    return _make


def _index(client: _FakeTlsClient, call: str) -> int:
    return client.calls.index(call)


# ═══════════════════════════════════════════════════════════════════════════
# Helper configure_tls — unitaire
# ═══════════════════════════════════════════════════════════════════════════


class TestConfigureTlsHelper:
    def test_disabled_does_not_call_tls_set(self):
        client = _FakeTlsClient()
        configure_tls(client, _config(tls="false"))
        assert "tls_set" not in client.calls

    def test_default_config_does_not_call_tls_set(self):
        # Sans variable TLS → désactivé → comportement historique.
        client = _FakeTlsClient()
        configure_tls(client, _config())
        assert client.calls == []

    def test_enabled_without_ca_calls_bare_tls_set(self):
        client = _FakeTlsClient()
        configure_tls(client, _config(tls="true"))
        assert client.calls == ["tls_set"]
        assert client.tls_kwargs == {}  # pas de ca_certs
        assert client.tls_args == ()

    def test_enabled_with_ca_passes_ca_certs(self):
        client = _FakeTlsClient()
        configure_tls(client, _config(tls="true", ca=CA_PATH))
        assert "tls_set" in client.calls
        assert client.tls_kwargs == {"ca_certs": CA_PATH}

    def test_never_calls_tls_insecure_set(self):
        client = _FakeTlsClient()
        configure_tls(client, _config(tls="true", ca=CA_PATH))
        assert "tls_insecure_set" not in client.calls


# ═══════════════════════════════════════════════════════════════════════════
# MqttSubscriber
# ═══════════════════════════════════════════════════════════════════════════


class TestSubscriberTls:
    def _build(self, config):
        client = _FakeTlsClient()
        sub = MqttSubscriber(
            config, on_measurement=lambda m: None,
            client_factory=_factory(client),
        )
        return sub, client

    def test_tls_disabled_no_tls_set(self):
        _sub, client = self._build(_config())
        assert "tls_set" not in client.calls

    def test_tls_enabled_calls_tls_set(self):
        _sub, client = self._build(_config(tls="true", ca=CA_PATH))
        assert client.tls_kwargs == {"ca_certs": CA_PATH}

    def test_tls_set_before_connect(self):
        sub, client = self._build(_config(tls="true"))
        sub.connect()
        assert "tls_set" in client.calls
        assert _index(client, "tls_set") < _index(client, "connect")


# ═══════════════════════════════════════════════════════════════════════════
# doctor --mqtt (check_mqtt_broker)
# ═══════════════════════════════════════════════════════════════════════════


class TestDoctorMqttTls:
    def test_tls_disabled_no_tls_set(self):
        client = _FakeTlsClient()
        check_mqtt_broker(_config(), client_factory=_factory(client))
        assert "tls_set" not in client.calls

    def test_tls_enabled_with_ca_before_connect(self):
        client = _FakeTlsClient()
        check_mqtt_broker(
            _config(tls="true", ca=CA_PATH), client_factory=_factory(client),
        )
        assert client.tls_kwargs == {"ca_certs": CA_PATH}
        assert _index(client, "tls_set") < _index(client, "connect")

    def test_tls_enabled_without_ca(self):
        client = _FakeTlsClient()
        check_mqtt_broker(_config(tls="true"), client_factory=_factory(client))
        assert client.calls.count("tls_set") == 1
        assert client.tls_kwargs == {}

    def test_ca_and_password_absent_from_result(self):
        client = _FakeTlsClient()
        result = check_mqtt_broker(
            _config(
                tls="true", ca=CA_PATH,
                FORGE_IOT_MQTT_USERNAME="forge",
                FORGE_IOT_MQTT_PASSWORD=SECRET_PWD,
            ),
            client_factory=_factory(client),
        )
        blob = result.detail + " " + " ".join(result.lines)
        assert CA_PATH not in blob
        assert SECRET_PWD not in blob


# ═══════════════════════════════════════════════════════════════════════════
# simulate (publish_measurements)
# ═══════════════════════════════════════════════════════════════════════════


class TestSimulateTls:
    def test_tls_disabled_no_tls_set(self, capsys):
        client = _FakeTlsClient()
        publish_measurements(
            _config(), SimulateOptions(count=1),
            client_factory=_factory(client), sleep=lambda _s: None,
        )
        capsys.readouterr()
        assert "tls_set" not in client.calls

    def test_tls_enabled_with_ca_before_connect(self, capsys):
        client = _FakeTlsClient()
        publish_measurements(
            _config(tls="true", ca=CA_PATH), SimulateOptions(count=1),
            client_factory=_factory(client), sleep=lambda _s: None,
        )
        capsys.readouterr()
        assert client.tls_kwargs == {"ca_certs": CA_PATH}
        assert _index(client, "tls_set") < _index(client, "connect")

    def test_tls_enabled_without_ca(self, capsys):
        client = _FakeTlsClient()
        publish_measurements(
            _config(tls="true"), SimulateOptions(count=1),
            client_factory=_factory(client), sleep=lambda _s: None,
        )
        capsys.readouterr()
        assert client.tls_kwargs == {}

    def test_ca_and_password_absent_from_output(self, capsys):
        client = _FakeTlsClient()
        publish_measurements(
            _config(
                tls="true", ca=CA_PATH,
                FORGE_IOT_MQTT_USERNAME="forge",
                FORGE_IOT_MQTT_PASSWORD=SECRET_PWD,
            ),
            SimulateOptions(count=2, interval=0),
            client_factory=_factory(client), sleep=lambda _s: None,
        )
        out = capsys.readouterr().out
        assert CA_PATH not in out
        assert SECRET_PWD not in out


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous périmètre
# ═══════════════════════════════════════════════════════════════════════════


class TestScopeGuards:
    def test_no_tls_insecure_call_in_sources(self):
        # On cherche un *appel* `.tls_insecure_set(` — pas la mention en
        # prose dans la docstring de tls.py (qui dit qu'on ne l'utilise pas).
        for path in (TLS_FILE, SUBSCRIBER_FILE, DOCTOR_FILE, SIMULATE_FILE):
            src = path.read_text(encoding="utf-8")
            assert ".tls_insecure_set" not in src, path

    def test_helper_does_not_connect(self):
        # Le helper applique seulement tls_set : il ne se connecte pas et
        # ne touche pas au port (l'utilisateur configure FORGE_IOT_MQTT_PORT).
        client = _FakeTlsClient()
        configure_tls(client, _config(tls="true", ca=CA_PATH))
        assert "connect" not in client.calls

    def test_no_client_certificate_args(self):
        # Pas de mTLS : pas de certfile/keyfile dans le helper.
        src = TLS_FILE.read_text(encoding="utf-8")
        assert "certfile" not in src
        assert "keyfile" not in src
