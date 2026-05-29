"""Tests de la commande ``forge iot:listen`` — IOT-SUBSCRIBER-CLI-001.

`forge iot:listen` écoute le broker MQTT configuré et insère les mesures
reçues dans `iot_events`. Les tests vérifient le flux **sans broker ni
base réels** grâce aux injections de `run_listener`
(`config`, `repository`, `subscriber_factory`) :

- la config est chargée et le repository créé (via `main`) ;
- le subscriber est créé avec un `on_measurement` branché ;
- une mesure reçue appelle `repository.insert` et produit un `[OK]` ;
- config invalide → exit 1 ;
- erreur DB table absente → message pédagogique (`forge iot:init` +
  `forge migration:apply`) ;
- `KeyboardInterrupt` géré proprement ;
- pas de simulateur lancé, pas de route HTTP, `paho` non importé tant
  que la commande n'est pas lancée, aucun import IoT dans `core/`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from forge_mvc_iot.cli import listen as listen_module
from forge_mvc_iot.cli.listen import main, run_listener
from forge_mvc_iot.config import IotConfig
from forge_mvc_iot.mqtt.contract import Measurement

PROJECT_ROOT = Path(__file__).parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"
LISTEN_FILE = (
    PROJECT_ROOT / "packages" / "forge-mvc-iot" / "forge_mvc_iot"
    / "cli" / "listen.py"
)
CORE_DIR = PROJECT_ROOT / "core"
HELP_FILE = PROJECT_ROOT / "forge_cli" / "help.py"


# ── Helpers / fakes ──────────────────────────────────────────────────────────


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


def _measurement(kind="temperature", value=22.4, unit="°C") -> Measurement:
    return Measurement(
        site="atelier", device_id="esp32-001",
        kind=kind, value=value, unit=unit,
        timestamp="2026-05-29T10:00:00Z", metadata=None,
    )


class _FakeMariadbError(Exception):
    def __init__(self, errno: int, message: str) -> None:
        super().__init__(message)
        self.errno = errno


class _FakeRepo:
    def __init__(self, *, insert_raises: Exception | None = None) -> None:
        self.inserted: list[Measurement] = []
        self._insert_raises = insert_raises

    def insert(self, measurement, *, received_at=None):
        if self._insert_raises is not None:
            raise self._insert_raises
        self.inserted.append(measurement)
        return 1


class _FakeSubscriber:
    def __init__(
        self,
        *,
        deliver=(),
        connect_raises: Exception | None = None,
        loop_raises: Exception | None = None,
    ) -> None:
        self.config = None
        self.on_measurement = None
        self.calls: list[str] = []
        self._deliver = list(deliver)
        self._connect_raises = connect_raises
        self._loop_raises = loop_raises

    def connect(self):
        self.calls.append("connect")
        if self._connect_raises is not None:
            raise self._connect_raises

    def loop_forever(self):
        self.calls.append("loop_forever")
        if self._loop_raises is not None:
            raise self._loop_raises
        for measurement in self._deliver:
            self.on_measurement(measurement)

    def disconnect(self):
        self.calls.append("disconnect")


def _factory(sub: _FakeSubscriber):
    def _make(*, config, on_measurement):
        sub.config = config
        sub.on_measurement = on_measurement
        return sub
    return _make


# ═══════════════════════════════════════════════════════════════════════════
# run_listener
# ═══════════════════════════════════════════════════════════════════════════


class TestRunListenerHappyPath:
    def test_inserts_and_logs_ok(self, capsys):
        repo = _FakeRepo()
        sub = _FakeSubscriber(deliver=[_measurement()])
        rc = run_listener(
            config=_config(), repository=repo, subscriber_factory=_factory(sub),
        )
        out = capsys.readouterr().out
        assert rc == 0
        assert repo.inserted == [_measurement()]
        assert "[OK] atelier/esp32-001 temperature=22.4 °C" in out
        assert "connect" in sub.calls
        assert "disconnect" in sub.calls

    def test_subscriber_built_with_callable_on_measurement(self, capsys):
        repo = _FakeRepo()
        sub = _FakeSubscriber()
        run_listener(
            config=_config(), repository=repo, subscriber_factory=_factory(sub),
        )
        capsys.readouterr()
        assert callable(sub.on_measurement)

    def test_banner_shows_broker_and_topic(self, capsys):
        repo = _FakeRepo()
        sub = _FakeSubscriber()
        run_listener(
            config=_config(), repository=repo, subscriber_factory=_factory(sub),
        )
        out = capsys.readouterr().out
        assert "Forge IoT listen" in out
        assert "localhost:1883" in out
        assert "forge/+/+/telemetry" in out

    def test_two_measurements_two_inserts(self, capsys):
        repo = _FakeRepo()
        sub = _FakeSubscriber(deliver=[
            _measurement(kind="temperature", value=22.4, unit="°C"),
            _measurement(kind="humidity", value=55, unit="%"),
        ])
        run_listener(
            config=_config(), repository=repo, subscriber_factory=_factory(sub),
        )
        out = capsys.readouterr().out
        assert len(repo.inserted) == 2
        assert "humidity=55 %" in out


class TestRunListenerKeyboardInterrupt:
    def test_clean_stop(self, capsys):
        repo = _FakeRepo()
        sub = _FakeSubscriber(loop_raises=KeyboardInterrupt())
        rc = run_listener(
            config=_config(), repository=repo, subscriber_factory=_factory(sub),
        )
        out = capsys.readouterr().out
        assert rc == 0
        assert "Arrêt" in out
        assert "disconnect" in sub.calls


class TestRunListenerConnectionError:
    def test_connection_refused_exit_1(self, capsys):
        repo = _FakeRepo()
        sub = _FakeSubscriber(connect_raises=ConnectionRefusedError(111))
        rc = run_listener(
            config=_config(), repository=repo, subscriber_factory=_factory(sub),
        )
        err = capsys.readouterr().err
        assert rc == 1
        assert "Connexion MQTT impossible" in err
        # On n'entre pas dans la boucle si la connexion échoue.
        assert "loop_forever" not in sub.calls


class TestRunListenerStorageErrors:
    def test_table_missing_is_pedagogical(self, capsys):
        repo = _FakeRepo(insert_raises=_FakeMariadbError(
            1146, "Table 'mydb.iot_events' doesn't exist",
        ))
        sub = _FakeSubscriber(deliver=[_measurement()])
        rc = run_listener(
            config=_config(), repository=repo, subscriber_factory=_factory(sub),
        )
        err = capsys.readouterr().err
        assert rc == 1
        assert "Stockage IoT indisponible" in err
        assert "forge iot:init" in err
        assert "forge migration:apply" in err
        # L'arrêt a bien été demandé au subscriber.
        assert "disconnect" in sub.calls

    def test_text_fallback_table_missing(self, capsys):
        repo = _FakeRepo(insert_raises=RuntimeError(
            "wrapper: Table doesn't exist",
        ))
        sub = _FakeSubscriber(deliver=[_measurement()])
        rc = run_listener(
            config=_config(), repository=repo, subscriber_factory=_factory(sub),
        )
        err = capsys.readouterr().err
        assert rc == 1
        assert "forge iot:init" in err

    def test_generic_db_error_is_sober(self, capsys):
        repo = _FakeRepo(insert_raises=RuntimeError("boom"))
        sub = _FakeSubscriber(deliver=[_measurement()])
        rc = run_listener(
            config=_config(), repository=repo, subscriber_factory=_factory(sub),
        )
        err = capsys.readouterr().err
        assert rc == 1
        assert "Insertion en base impossible" in err
        assert "Traceback" not in err


# ═══════════════════════════════════════════════════════════════════════════
# main
# ═══════════════════════════════════════════════════════════════════════════


class TestMain:
    def test_config_loaded_and_repository_created_on_success(
        self, monkeypatch, capsys,
    ):
        repo = _FakeRepo()
        sub = _FakeSubscriber(deliver=[_measurement()])
        created: list[bool] = []

        def _fake_repo_ctor():
            created.append(True)
            return repo

        monkeypatch.setattr(
            "forge_mvc_iot.config.load_iot_config", lambda env=None: _config(),
        )
        monkeypatch.setattr(
            "forge_mvc_iot.storage.IotEventRepository", _fake_repo_ctor,
        )
        monkeypatch.setattr(
            listen_module, "_default_subscriber_factory", _factory(sub),
        )
        rc = main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert created == [True]
        assert repo.inserted == [_measurement()]
        assert "[OK]" in out

    def test_config_invalid_exit_1(self, monkeypatch, capsys):
        def _raise(env=None):
            raise ValueError("FORGE_IOT_MQTT_HOST ne peut pas être vide")

        monkeypatch.setattr("forge_mvc_iot.config.load_iot_config", _raise)
        rc = main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "Configuration IoT invalide" in err


# ═══════════════════════════════════════════════════════════════════════════
# Aide CLI
# ═══════════════════════════════════════════════════════════════════════════


class TestCliHelp:
    def test_listen_help_renders(self):
        result = subprocess.run(
            [sys.executable, str(FORGE_PY), "iot:listen", "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "iot:listen" in result.stdout

    def test_forge_help_lists_listen(self):
        result = subprocess.run(
            [sys.executable, str(FORGE_PY), "help"],
            capture_output=True, text=True, timeout=30,
        )
        assert "iot:listen" in result.stdout

    def test_help_py_lists_listen(self):
        assert "iot:listen" in HELP_FILE.read_text(encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous périmètre
# ═══════════════════════════════════════════════════════════════════════════


class TestScopeGuards:
    def test_no_paho_or_subscriber_import_at_module_level(self):
        src = LISTEN_FILE.read_text(encoding="utf-8")
        head = src.split("\ndef ", 1)[0]
        head_imports = [
            line for line in head.splitlines()
            if line.lstrip().startswith(("import ", "from "))
        ]
        offenders = [
            line for line in head_imports
            if "paho" in line.lower() or "mqtt.subscriber" in line
        ]
        assert not offenders, offenders

    def test_importing_module_does_not_import_paho(self):
        code = (
            "import sys\n"
            "import forge_mvc_iot.cli.listen  # noqa\n"
            "print('paho' in sys.modules)\n"
        )
        out = subprocess.check_output(
            [sys.executable, "-c", code], stderr=subprocess.STDOUT,
        )
        assert out.strip().endswith(b"False"), out

    def test_does_not_launch_simulator(self):
        src = LISTEN_FILE.read_text(encoding="utf-8")
        assert "cli.simulate" not in src
        assert "publish_measurements" not in src

    def test_does_not_touch_http_api(self):
        src = LISTEN_FILE.read_text(encoding="utf-8")
        assert "register_iot_routes" not in src
        assert "forge_mvc_iot.http" not in src

    def test_no_core_module_imports_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(PROJECT_ROOT))
        assert not offenders, offenders
