"""Tests de robustesse de ``forge iot:listen`` — IOT-LISTEN-RESILIENCE-001.

Renforce la commande sans la transformer en service de production :

- arrêt propre sur ``Ctrl+C`` (``[INFO] Arrêt demandé.`` +
  ``[OK] Écoute MQTT arrêtée proprement.``) ;
- ``disconnect`` garanti dans un ``finally``, même en cas d'erreur ;
- compteurs de session (``ListenStats``) : reçues / stockées / erreurs de
  contrat / erreurs de stockage, restitués en fin de session ;
- erreurs de contrat MQTT visibles (``[WARN] Message MQTT ignoré — CODE``)
  et **non fatales** ;
- erreurs base distinguées : table absente (``forge iot:init`` +
  ``forge migration:apply``), connexion impossible (``forge iot:doctor
  --db``), générique (sobre, pas de stacktrace) ;
- la commande ne lance pas le simulateur, ne touche pas l'API HTTP, et
  ``core/`` n'importe toujours pas ``forge_mvc_iot``.

Aucun broker ni base réels : ``run_listener`` injecte ``config``,
``repository`` et ``subscriber_factory``.
"""

from __future__ import annotations

from pathlib import Path

from forge_mvc_iot.cli.listen import ListenStats, run_listener
from forge_mvc_iot.config import IotConfig
from forge_mvc_iot.mqtt.contract import ContractError
from forge_mvc_iot.mqtt.contract import Measurement

PROJECT_ROOT = Path(__file__).parent.parent
LISTEN_FILE = (
    PROJECT_ROOT / "packages" / "forge-mvc-iot" / "forge_mvc_iot"
    / "cli" / "listen.py"
)
CORE_DIR = PROJECT_ROOT / "core"


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
    """Sujet de test : délivre des mesures et/ou des erreurs de contrat.

    ``deliver`` est une liste d'éléments :
    - une ``Measurement`` → appelle ``on_measurement`` ;
    - un ``ContractError``  → appelle ``on_contract_error``.
    """

    def __init__(self, *, deliver=(), loop_raises: Exception | None = None) -> None:
        self.config = None
        self.on_measurement = None
        self.on_contract_error = None
        self.calls: list[str] = []
        self._deliver = list(deliver)
        self._loop_raises = loop_raises
        self._disconnected = False

    def connect(self):
        self.calls.append("connect")

    def loop_forever(self):
        self.calls.append("loop_forever")
        if self._loop_raises is not None:
            raise self._loop_raises
        for item in self._deliver:
            # Comme paho : un disconnect() dans un callback fait sortir la
            # boucle — on ne délivre plus les messages suivants.
            if self._disconnected:
                break
            if isinstance(item, ContractError):
                self.on_contract_error(item, "forge/bad/topic", b"{}")
            else:
                self.on_measurement(item)

    def disconnect(self):
        self.calls.append("disconnect")
        self._disconnected = True


def _factory(sub: _FakeSubscriber):
    def _make(*, config, on_measurement, on_contract_error=None):
        sub.config = config
        sub.on_measurement = on_measurement
        sub.on_contract_error = on_contract_error
        return sub
    return _make


def _run(sub: _FakeSubscriber, repo: _FakeRepo):
    return run_listener(
        config=_config(), repository=repo, subscriber_factory=_factory(sub),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Arrêt propre
# ═══════════════════════════════════════════════════════════════════════════


class TestCleanStop:
    def test_ctrl_c_prints_clean_stop(self, capsys):
        sub = _FakeSubscriber(loop_raises=KeyboardInterrupt())
        rc = _run(sub, _FakeRepo())
        out = capsys.readouterr().out
        assert rc == 0
        assert "[INFO] Arrêt demandé." in out
        assert "[OK] Écoute MQTT arrêtée proprement." in out

    def test_disconnect_called_in_finally_on_ctrl_c(self, capsys):
        sub = _FakeSubscriber(loop_raises=KeyboardInterrupt())
        _run(sub, _FakeRepo())
        capsys.readouterr()
        assert "disconnect" in sub.calls

    def test_disconnect_called_even_on_unexpected_loop_error(self, capsys):
        # Une exception inattendue dans la boucle ne doit pas empêcher le
        # disconnect (garanti par le finally). L'exception se propage ensuite.
        sub = _FakeSubscriber(loop_raises=RuntimeError("loop blew up"))
        try:
            _run(sub, _FakeRepo())
        except RuntimeError:
            pass
        capsys.readouterr()
        assert "disconnect" in sub.calls


# ═══════════════════════════════════════════════════════════════════════════
# Compteurs de session
# ═══════════════════════════════════════════════════════════════════════════


class TestSessionStats:
    def test_valid_measurement_increments_received_and_stored(self, capsys):
        repo = _FakeRepo()
        sub = _FakeSubscriber(deliver=[_measurement(), _measurement()])
        rc = _run(sub, repo)
        out = capsys.readouterr().out
        assert rc == 0
        assert "mesures reçues       : 2" in out
        assert "mesures stockées     : 2" in out
        assert "erreurs de contrat   : 0" in out
        assert "erreurs de stockage  : 0" in out

    def test_summary_always_printed(self, capsys):
        sub = _FakeSubscriber(deliver=[])
        _run(sub, _FakeRepo())
        out = capsys.readouterr().out
        assert "Résumé :" in out

    def test_stats_dataclass_defaults(self):
        stats = ListenStats()
        assert (stats.received, stats.stored) == (0, 0)
        assert (stats.contract_errors, stats.storage_errors) == (0, 0)


# ═══════════════════════════════════════════════════════════════════════════
# Erreurs de contrat MQTT — visibles, non fatales
# ═══════════════════════════════════════════════════════════════════════════


class TestContractErrors:
    def test_contract_error_is_warned_and_counted(self, capsys):
        repo = _FakeRepo()
        sub = _FakeSubscriber(deliver=[
            ContractError("PAYLOAD_FIELD_MISSING", "champ value manquant"),
        ])
        rc = _run(sub, repo)
        out, err = capsys.readouterr()
        assert rc == 0  # une erreur de contrat n'est pas fatale
        assert "[WARN] Message MQTT ignoré — PAYLOAD_FIELD_MISSING" in err
        assert "erreurs de contrat   : 1" in out

    def test_contract_error_does_not_stop_listening(self, capsys):
        repo = _FakeRepo()
        sub = _FakeSubscriber(deliver=[
            ContractError("TOPIC_PATTERN", "topic invalide"),
            _measurement(),
        ])
        rc = _run(sub, repo)
        out = capsys.readouterr().out
        assert rc == 0
        assert repo.inserted == [_measurement()]
        assert "mesures stockées     : 1" in out
        assert "erreurs de contrat   : 1" in out

    def test_contract_error_payload_not_leaked(self, capsys):
        repo = _FakeRepo()
        sub = _FakeSubscriber(deliver=[
            ContractError("PAYLOAD_PARSE", "JSON invalide"),
        ])
        _run(sub, repo)
        err = capsys.readouterr().err
        # On n'affiche que le code, pas le détail ni le payload brut.
        assert "JSON invalide" not in err


# ═══════════════════════════════════════════════════════════════════════════
# Erreurs base — distinguées et pédagogiques
# ═══════════════════════════════════════════════════════════════════════════


class TestStorageErrors:
    def test_table_missing_advises_init_and_apply(self, capsys):
        repo = _FakeRepo(insert_raises=_FakeMariadbError(
            1146, "Table 'mydb.iot_events' doesn't exist",
        ))
        sub = _FakeSubscriber(deliver=[_measurement()])
        rc = _run(sub, repo)
        out, err = capsys.readouterr()
        assert rc == 1
        assert "Table iot_events absente" in err
        assert "forge iot:init" in err
        assert "forge migration:apply" in err
        assert "disconnect" in sub.calls
        assert "erreurs de stockage  : 1" in out

    def test_connection_error_advises_doctor_db(self, capsys):
        repo = _FakeRepo(insert_raises=_FakeMariadbError(
            2003, "Can't connect to MySQL server on 'localhost' (111)",
        ))
        sub = _FakeSubscriber(deliver=[_measurement()])
        rc = _run(sub, repo)
        err = capsys.readouterr().err
        assert rc == 1
        assert "Connexion base impossible" in err
        assert "forge iot:doctor --db" in err
        # On ne confond pas avec le cas « table absente ».
        assert "forge migration:apply" not in err

    def test_access_denied_is_connection_error(self, capsys):
        repo = _FakeRepo(insert_raises=_FakeMariadbError(
            1045, "Access denied for user 'forge'@'localhost' (using password: YES)",
        ))
        sub = _FakeSubscriber(deliver=[_measurement()])
        rc = _run(sub, repo)
        err = capsys.readouterr().err
        assert rc == 1
        assert "Connexion base impossible" in err

    def test_connection_error_text_fallback(self, capsys):
        # Pas d'errno : on se rabat sur le message.
        repo = _FakeRepo(insert_raises=RuntimeError(
            "wrapper: Can't connect to MySQL server",
        ))
        sub = _FakeSubscriber(deliver=[_measurement()])
        rc = _run(sub, repo)
        err = capsys.readouterr().err
        assert rc == 1
        assert "Connexion base impossible" in err

    def test_generic_db_error_is_sober(self, capsys):
        repo = _FakeRepo(insert_raises=RuntimeError("boom"))
        sub = _FakeSubscriber(deliver=[_measurement()])
        rc = _run(sub, repo)
        err = capsys.readouterr().err
        assert rc == 1
        assert "Stockage IoT impossible" in err
        assert "Traceback" not in err
        assert "boom" not in err  # pas de fuite du détail technique

    def test_storage_error_stops_after_first(self, capsys):
        # On s'arrête au premier échec base : la 2e mesure n'est pas tentée.
        repo = _FakeRepo(insert_raises=RuntimeError("boom"))
        sub = _FakeSubscriber(deliver=[_measurement(), _measurement()])
        _run(sub, repo)
        out = capsys.readouterr().out
        # disconnect demandé dès la 1re erreur ; received compte la 1re mesure.
        assert "mesures reçues       : 1" in out
        assert "mesures stockées     : 0" in out


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous périmètre — pas de logique production lourde
# ═══════════════════════════════════════════════════════════════════════════


class TestScopeGuards:
    def test_does_not_launch_simulator(self):
        src = LISTEN_FILE.read_text(encoding="utf-8")
        assert "cli.simulate" not in src
        assert "publish_measurements" not in src

    def test_does_not_touch_http_api(self):
        src = LISTEN_FILE.read_text(encoding="utf-8")
        assert "register_iot_routes" not in src
        assert "forge_mvc_iot.http" not in src

    def test_no_systemd_service_machinery(self):
        # Reste une commande dev/pédagogie : pas de service systemd.
        src = LISTEN_FILE.read_text(encoding="utf-8").lower()
        assert "systemd" not in src

    def test_no_core_module_imports_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(PROJECT_ROOT))
        assert not offenders, offenders
