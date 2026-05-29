"""Tests de ``forge iot:doctor --mqtt`` — IOT-DOCTOR-MQTT-001.

Vérifie l'option ``--mqtt`` de la commande ``forge iot:doctor`` :

- sans ``--mqtt`` → le check broker reste en ``skip`` (comportement par
  défaut, aucun import ``paho`` déclenché) ;
- avec ``--mqtt`` → ``check_mqtt_broker()`` est appelé :
  - CONNACK reason code 0 → ``[OK] connexion réussie à host:port`` ;
  - authentification refusée → ``[FAIL] authentification refusée`` ;
  - connexion réseau impossible → ``[FAIL] connexion impossible`` + exit 1 ;
  - timeout (CONNACK jamais reçu) → ``[FAIL]`` + exit 1 ;
- aucun mot de passe MQTT n'apparaît dans la sortie ;
- pas de ``loop_forever``, pas de ``subscribe``, pas de ``publish`` ;
- ``--db`` et ``--mqtt`` peuvent coexister ;
- ``paho`` n'est pas importé tant que ``--mqtt`` est absent ;
- ``core/`` n'importe toujours pas ``forge_mvc_iot``.

Aucun broker requis : ``check_mqtt_broker`` accepte un ``client_factory``
injectable qui retourne un faux client pilotant les callbacks paho.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.cli import doctor as doctor_module
from forge_mvc_iot.cli.doctor import (
    CheckResult,
    check_mqtt_broker,
    has_failures,
    info_mqtt_not_tested,
    main,
    run_all,
)
from forge_mvc_iot.config import load_iot_config

PROJECT_ROOT = Path(__file__).parent.parent
DOCTOR_FILE = (
    PROJECT_ROOT / "packages" / "forge-mvc-iot" / "forge_mvc_iot"
    / "cli" / "doctor.py"
)
CORE_DIR = PROJECT_ROOT / "core"
HELP_DISPATCH_FILE = PROJECT_ROOT / "forge_cli" / "help_dispatch.py"


# ── Faux client MQTT (aucun broker, aucun paho) ─────────────────────────────


class _FakeReasonCode:
    """Reason code façon ``paho.mqtt.reasoncodes.ReasonCode``.

    ``__int__`` peut lever (cas v5 où seul le texte est exploitable),
    auquel cas la détection retombe sur l'analyse textuelle.
    """

    def __init__(self, value: int | None, text: str) -> None:
        self._value = value
        self._text = text

    def __int__(self) -> int:
        if self._value is None:
            raise TypeError("reason code non convertible en int")
        return self._value

    def __str__(self) -> str:
        return self._text


class _FakeMqttClient:
    """Faux client MQTT : enregistre les appels et pilote ``on_connect``.

    Paramètres de comportement :

    - ``connect_raises`` : exception levée par ``connect()`` (réseau KO) ;
    - ``reason_code``    : reason code fourni à ``on_connect`` lors de
      ``loop_start()`` ;
    - ``fire_connack``   : si ``False``, ``on_connect`` n'est jamais
      appelé (simule un timeout — le CONNACK n'arrive pas).
    """

    def __init__(
        self,
        *,
        reason_code=0,
        connect_raises: Exception | None = None,
        fire_connack: bool = True,
    ) -> None:
        self.on_connect = None
        self._reason_code = reason_code
        self._connect_raises = connect_raises
        self._fire_connack = fire_connack
        self.calls: list[str] = []
        self.credentials: tuple[str, str | None] | None = None

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
        if self._fire_connack and self.on_connect is not None:
            self.on_connect(self, None, None, self._reason_code)

    def loop_stop(self):
        self.calls.append("loop_stop")

    def disconnect(self):
        self.calls.append("disconnect")


def _config(**overrides):
    env = {
        "FORGE_IOT_MQTT_HOST": "localhost",
        "FORGE_IOT_MQTT_PORT": "1883",
    }
    env.update(overrides)
    return load_iot_config(env)


def _factory(client: _FakeMqttClient):
    def _make(_config):
        return client
    return _make


# ═══════════════════════════════════════════════════════════════════════════
# check_mqtt_broker — fonction unitaire
# ═══════════════════════════════════════════════════════════════════════════


class TestCheckMqttBrokerSuccess:
    def test_reason_code_zero_yields_ok(self):
        client = _FakeMqttClient(reason_code=0)
        result = check_mqtt_broker(_config(), client_factory=_factory(client))
        assert result.status == "ok"
        assert result.label == "broker MQTT"
        assert "connexion réussie" in result.detail
        assert "localhost:1883" in result.detail

    def test_connect_called_with_host_and_port(self):
        client = _FakeMqttClient(reason_code=0)
        check_mqtt_broker(_config(), client_factory=_factory(client))
        assert client.connect_target == ("localhost", 1883)

    def test_brief_connection_then_cleanup(self):
        # Connexion brève : connect → loop_start → loop_stop → disconnect.
        # Surtout : pas de subscribe, pas de publish, pas de loop_forever.
        client = _FakeMqttClient(reason_code=0)
        check_mqtt_broker(_config(), client_factory=_factory(client))
        assert "loop_stop" in client.calls
        assert "disconnect" in client.calls
        assert "subscribe" not in client.calls
        assert "publish" not in client.calls
        assert "loop_forever" not in client.calls


class TestCheckMqttBrokerAuthRefused:
    def test_reason_code_5_yields_auth_fail(self):
        client = _FakeMqttClient(reason_code=5)
        result = check_mqtt_broker(_config(), client_factory=_factory(client))
        assert result.status == "fail"
        assert result.detail == "authentification refusée"

    def test_reason_code_134_yields_auth_fail(self):
        # MQTT 5 : 0x86 = bad user name or password.
        client = _FakeMqttClient(reason_code=134)
        result = check_mqtt_broker(_config(), client_factory=_factory(client))
        assert result.status == "fail"
        assert result.detail == "authentification refusée"

    def test_text_only_reason_code_yields_auth_fail(self):
        # Reason code dont int() échoue : détection via le texte.
        rc = _FakeReasonCode(None, "Not authorized")
        client = _FakeMqttClient(reason_code=rc)
        result = check_mqtt_broker(_config(), client_factory=_factory(client))
        assert result.status == "fail"
        assert result.detail == "authentification refusée"


class TestCheckMqttBrokerConnectionError:
    def test_connect_refused_yields_fail(self):
        client = _FakeMqttClient(connect_raises=ConnectionRefusedError(111))
        result = check_mqtt_broker(_config(), client_factory=_factory(client))
        assert result.status == "fail"
        assert "connexion impossible" in result.detail
        assert "localhost:1883" in result.detail
        # On n'a pas tenté de boucler si la connexion TCP a échoué.
        assert "loop_start" not in client.calls

    def test_generic_network_exception_yields_fail(self):
        client = _FakeMqttClient(connect_raises=OSError("network unreachable"))
        result = check_mqtt_broker(_config(), client_factory=_factory(client))
        assert result.status == "fail"
        assert "connexion impossible" in result.detail

    def test_timeout_yields_fail(self):
        # CONNACK jamais reçu → wait expire (timeout court injecté).
        client = _FakeMqttClient(fire_connack=False)
        result = check_mqtt_broker(
            _config(), client_factory=_factory(client), connect_timeout=0.05,
        )
        assert result.status == "fail"
        assert "connexion impossible" in result.detail
        assert "timeout" in result.detail
        # Même en cas de timeout, on referme proprement.
        assert "loop_stop" in client.calls
        assert "disconnect" in client.calls

    def test_other_reason_code_yields_fail(self):
        # Reason code non nul et non lié à l'auth (ex. 3 = server
        # unavailable) → FAIL générique « refusée par le broker ».
        client = _FakeMqttClient(reason_code=3)
        result = check_mqtt_broker(_config(), client_factory=_factory(client))
        assert result.status == "fail"
        assert "broker" in result.detail.lower()
        assert result.detail != "authentification refusée"


class TestCheckMqttBrokerCredentials:
    def test_username_pw_set_called_when_username_present(self):
        client = _FakeMqttClient(reason_code=0)
        cfg = _config(
            FORGE_IOT_MQTT_USERNAME="forge",
            FORGE_IOT_MQTT_PASSWORD="s3cr3t",
        )
        check_mqtt_broker(cfg, client_factory=_factory(client))
        assert "username_pw_set" in client.calls
        assert client.credentials == ("forge", "s3cr3t")

    def test_username_pw_set_not_called_when_no_username(self):
        client = _FakeMqttClient(reason_code=0)
        check_mqtt_broker(_config(), client_factory=_factory(client))
        assert "username_pw_set" not in client.calls


class TestPasswordNeverLeaked:
    """Le mot de passe MQTT ne doit jamais apparaître dans la sortie."""

    def test_password_absent_from_ok_detail(self):
        client = _FakeMqttClient(reason_code=0)
        cfg = _config(
            FORGE_IOT_MQTT_USERNAME="forge",
            FORGE_IOT_MQTT_PASSWORD="supersecret-pwd-xyz123",
        )
        result = check_mqtt_broker(cfg, client_factory=_factory(client))
        assert "supersecret-pwd-xyz123" not in result.detail

    def test_password_absent_from_auth_fail_detail(self):
        client = _FakeMqttClient(reason_code=5)
        cfg = _config(
            FORGE_IOT_MQTT_USERNAME="forge",
            FORGE_IOT_MQTT_PASSWORD="supersecret-pwd-xyz123",
        )
        result = check_mqtt_broker(cfg, client_factory=_factory(client))
        assert "supersecret-pwd-xyz123" not in result.detail


# ═══════════════════════════════════════════════════════════════════════════
# run_all(test_mqtt=...)
# ═══════════════════════════════════════════════════════════════════════════


class TestRunAllToggle:
    def test_without_test_mqtt_uses_info_skip(self, monkeypatch):
        called: list[bool] = []
        monkeypatch.setattr(
            doctor_module, "check_mqtt_broker",
            lambda *a, **kw: called.append(True) or CheckResult(
                status="ok", label="never",
            ),
        )
        results = run_all()
        assert called == [], (
            "check_mqtt_broker ne doit PAS être appelé sans test_mqtt=True"
        )
        mqtt_result = next(r for r in results if r.label == "broker MQTT")
        assert mqtt_result.status == "skip"

    def test_with_test_mqtt_calls_check_mqtt_broker(self, monkeypatch):
        called: list[bool] = []

        def _fake_check(cfg, **kw):
            called.append(True)
            return CheckResult(
                status="ok", label="broker MQTT",
                detail="connexion réussie à localhost:1883",
            )

        monkeypatch.setattr(doctor_module, "check_mqtt_broker", _fake_check)
        results = run_all(test_mqtt=True, env={
            "FORGE_IOT_MQTT_HOST": "localhost",
        })
        assert called == [True]
        mqtt_result = next(r for r in results if r.label == "broker MQTT")
        assert mqtt_result.status == "ok"

    def test_invalid_config_does_not_mask_config_fail(self, monkeypatch):
        # Config invalide : le check configuration doit rester en fail,
        # le check MQTT se contente d'un skip sans planter.
        def _should_not_be_called(*a, **kw):
            raise AssertionError("check_mqtt_broker appelé sur config invalide")

        monkeypatch.setattr(
            doctor_module, "check_mqtt_broker", _should_not_be_called,
        )
        results = run_all(test_mqtt=True, env={"FORGE_IOT_MQTT_HOST": ""})
        config_result = next(r for r in results if r.label == "configuration IoT")
        mqtt_result = next(r for r in results if r.label == "broker MQTT")
        assert config_result.status == "fail"
        assert mqtt_result.status == "skip"
        assert "configuration" in mqtt_result.detail.lower()


# ═══════════════════════════════════════════════════════════════════════════
# main(--mqtt) et coexistence --db / --mqtt
# ═══════════════════════════════════════════════════════════════════════════


class TestMainWithMqttFlag:
    def test_main_mqtt_calls_check(self, monkeypatch, capsys):
        called: list[bool] = []

        def _fake_check(cfg, **kw):
            called.append(True)
            return CheckResult(
                status="ok", label="broker MQTT",
                detail="connexion réussie à localhost:1883",
            )

        monkeypatch.setattr(doctor_module, "check_mqtt_broker", _fake_check)
        rc = main(["--mqtt"])
        out = capsys.readouterr().out
        assert called == [True]
        assert rc == 0
        assert "[OK]" in out
        assert "connexion réussie" in out

    def test_main_mqtt_fail_exits_1(self, monkeypatch, capsys):
        monkeypatch.setattr(
            doctor_module, "check_mqtt_broker",
            lambda cfg, **kw: CheckResult(
                status="fail", label="broker MQTT",
                detail="connexion impossible à localhost:1883",
            ),
        )
        rc = main(["--mqtt"])
        capsys.readouterr()
        assert rc == 1

    def test_main_without_mqtt_keeps_skip(self, monkeypatch, capsys):
        def _should_not_be_called(*a, **kw):
            raise AssertionError("check_mqtt_broker appelé sans --mqtt")

        monkeypatch.setattr(
            doctor_module, "check_mqtt_broker", _should_not_be_called,
        )
        rc = main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[SKIP]" in out
        assert "--mqtt" in out

    def test_db_and_mqtt_coexist(self, monkeypatch, capsys):
        mqtt_called: list[bool] = []
        db_called: list[bool] = []

        def _fake_mqtt(cfg, **kw):
            mqtt_called.append(True)
            return CheckResult(
                status="ok", label="broker MQTT",
                detail="connexion réussie à localhost:1883",
            )

        def _fake_db():
            db_called.append(True)
            return CheckResult(
                status="ok", label="base iot_events",
                detail="table accessible (0 événement(s))",
            )

        monkeypatch.setattr(doctor_module, "check_mqtt_broker", _fake_mqtt)
        monkeypatch.setattr(doctor_module, "check_database_table", _fake_db)
        # Table ok → le contrôle de schéma est aussi déclenché (IOT-DOCTOR-
        # SCHEMA-001) : on le stubbe pour rester hors-ligne dans ce test.
        monkeypatch.setattr(
            doctor_module, "check_database_schema",
            lambda **kw: CheckResult(
                status="ok", label="schéma iot_events", detail="conforme",
            ),
        )
        rc = main(["--db", "--mqtt"])
        out = capsys.readouterr().out
        assert mqtt_called == [True]
        assert db_called == [True]
        assert rc == 0
        assert "broker MQTT" in out
        assert "base iot_events" in out


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous périmètre
# ═══════════════════════════════════════════════════════════════════════════


class TestPahoLazyImport:
    def test_paho_not_imported_at_module_level(self):
        # paho doit être importé dans le corps d'une fonction, jamais au
        # niveau module.
        src = DOCTOR_FILE.read_text(encoding="utf-8")
        head = src.split("\ndef ", 1)[0]
        head_imports = [
            line for line in head.splitlines()
            if line.lstrip().startswith(("import ", "from "))
        ]
        offenders = [line for line in head_imports if "paho" in line.lower()]
        assert not offenders, (
            f"paho doit être importé paresseusement, pas au niveau module : {offenders}"
        )

    def test_paho_absent_from_sys_modules_when_mqtt_flag_absent(self):
        # Dans un interpréteur frais, lancer le doctor sans --mqtt ne doit
        # jamais charger paho.
        code = (
            "import sys\n"
            "from forge_mvc_iot.cli import doctor\n"
            "doctor.run_all()\n"
            "print('paho' in sys.modules)\n"
        )
        out = subprocess.check_output(
            [sys.executable, "-c", code], stderr=subprocess.STDOUT,
        )
        assert out.strip().endswith(b"False"), (
            f"paho ne doit pas être importé sans --mqtt : {out!r}"
        )


class TestInfoMqttStillSkipsByDefault:
    def test_label_and_status(self):
        result = info_mqtt_not_tested()
        assert result.status == "skip"
        assert result.label == "broker MQTT"
        assert "--mqtt" in result.detail


class TestNoCoreImportsIot:
    def test_no_core_module_imports_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(PROJECT_ROOT))
        assert not offenders, offenders


# ═══════════════════════════════════════════════════════════════════════════
# Aide CLI
# ═══════════════════════════════════════════════════════════════════════════


class TestHelpDispatchMentionsMqtt:
    def test_help_text_mentions_mqtt(self):
        text = HELP_DISPATCH_FILE.read_text(encoding="utf-8")
        idx = text.find('"iot:doctor": """\\')
        assert idx >= 0, "Bloc HELP_TEXTS_RICH iot:doctor introuvable"
        block = text[idx:idx + 2500]
        assert "--mqtt" in block, (
            "L'aide riche iot:doctor doit mentionner --mqtt"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Intégration — has_failures cohérent
# ═══════════════════════════════════════════════════════════════════════════


class TestHasFailures:
    def test_mqtt_fail_counts_as_failure(self):
        results = [
            CheckResult(status="ok", label="a"),
            CheckResult(
                status="fail", label="broker MQTT",
                detail="connexion impossible à localhost:1883",
            ),
        ]
        assert has_failures(results) is True

    def test_mqtt_skip_does_not_count_as_failure(self):
        results = [
            CheckResult(status="ok", label="a"),
            CheckResult(status="skip", label="broker MQTT"),
        ]
        assert has_failures(results) is False
