"""Tests du repository d'insertion IoT — IOT-STORAGE-REPOSITORY-001.

Vérifie que ``IotEventRepository`` :

- délègue à un adapter injectable exposant ``execute(sql, params)`` ;
- produit le SQL via ``build_insert_iot_event_sql`` (cohérence avec
  ``IOT-STORAGE-EVENTS-001``) ;
- respecte l'ordre des paramètres aligné sur ``COLUMNS`` ;
- propage ``received_at``, gère ``metadata=None`` et
  ``metadata=dict`` ;
- propage telles quelles les erreurs SQL (pas de catch silencieux) ;
- utilise ``core.database.db`` par défaut quand aucun adapter n'est
  fourni — vérifié sans toucher MariaDB.

Garde-fous périmètre :

- le repository n'importe pas ``paho.mqtt`` ;
- le subscriber n'importe pas le repository ;
- ``core/`` n'importe toujours pas ``forge_mvc_iot``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.mqtt.contract import Measurement
from forge_mvc_iot.storage.events import (
    COLUMNS,
    INSERT_IOT_EVENT_SQL,
)
from forge_mvc_iot.storage.repository import (
    DbAdapter,
    IotEventRepository,
    _default_db_adapter,
)

PROJECT_ROOT = Path(__file__).parent.parent
IOT_PKG_DIR = PROJECT_ROOT / "packages" / "forge-mvc-iot"
REPOSITORY_FILE = IOT_PKG_DIR / "forge_mvc_iot" / "storage" / "repository.py"
SUBSCRIBER_FILE = IOT_PKG_DIR / "forge_mvc_iot" / "mqtt" / "subscriber.py"
CORE_DIR = PROJECT_ROOT / "core"

FIXED_RECEIVED_AT = datetime(2026, 5, 28, 10, 0, 5, tzinfo=UTC)


def _make_measurement(**overrides) -> Measurement:
    base = dict(
        site="atelier",
        device_id="esp32-001",
        kind="temperature",
        value=22.4,
        unit="°C",
        timestamp="2026-05-28T10:00:00Z",
        metadata=None,
    )
    base.update(overrides)
    return Measurement(**base)


# ═══════════════════════════════════════════════════════════════════════════
# Construction
# ═══════════════════════════════════════════════════════════════════════════


class TestConstruction:
    def test_accepts_injected_adapter(self):
        adapter = MagicMock()
        repo = IotEventRepository(db_adapter=adapter)
        assert repo._db is adapter

    def test_default_adapter_is_core_database_db(self):
        # Construction sans adapter : on doit utiliser core.database.db.
        # Aucune connexion réseau n'est ouverte (lazy pool documenté
        # dans core/database/connection.py).
        from core.database import db as forge_db

        repo = IotEventRepository()
        assert repo._db is forge_db, (
            "Par défaut, le repository doit utiliser core.database.db"
        )

    def test_default_adapter_resolved_via_helper(self):
        # Le helper est exporté pour testabilité — on vérifie qu'il
        # retourne le même module que celui choisi par défaut.
        from core.database import db as forge_db
        assert _default_db_adapter() is forge_db


class TestProtocolShape:
    def test_db_adapter_protocol_exposes_execute(self):
        # Le Protocol définit bien execute(sql, params).
        assert hasattr(DbAdapter, "execute")


# ═══════════════════════════════════════════════════════════════════════════
# insert() — délégation et paramètres
# ═══════════════════════════════════════════════════════════════════════════


class TestInsertDelegation:
    def test_calls_adapter_execute_once(self):
        adapter = MagicMock()
        repo = IotEventRepository(db_adapter=adapter)
        repo.insert(_make_measurement(), received_at=FIXED_RECEIVED_AT)
        adapter.execute.assert_called_once()

    def test_sql_passed_is_insert_iot_event_sql(self):
        adapter = MagicMock()
        repo = IotEventRepository(db_adapter=adapter)
        repo.insert(_make_measurement(), received_at=FIXED_RECEIVED_AT)
        sql_arg = adapter.execute.call_args.args[0]
        assert sql_arg == INSERT_IOT_EVENT_SQL

    def test_returns_adapter_result(self):
        adapter = MagicMock()
        adapter.execute.return_value = 42
        repo = IotEventRepository(db_adapter=adapter)
        result = repo.insert(_make_measurement(), received_at=FIXED_RECEIVED_AT)
        assert result == 42


class TestInsertParameters:
    def _capture_params(self, repo: IotEventRepository) -> tuple:
        adapter = repo._db
        return adapter.execute.call_args.args[1]

    def test_params_count_matches_columns(self):
        adapter = MagicMock()
        repo = IotEventRepository(db_adapter=adapter)
        repo.insert(_make_measurement(), received_at=FIXED_RECEIVED_AT)
        params = adapter.execute.call_args.args[1]
        assert len(params) == len(COLUMNS)

    def test_params_order_matches_columns(self):
        adapter = MagicMock()
        m = _make_measurement(
            site="salle-tp",
            device_id="raspi-04",
            kind="humidity",
            value=47,
            unit="%",
            timestamp="2026-05-28T10:00:05Z",
            metadata={"room": "atelier"},
        )
        repo = IotEventRepository(db_adapter=adapter)
        repo.insert(m, received_at=FIXED_RECEIVED_AT)
        params = adapter.execute.call_args.args[1]
        # Position 0..7 selon COLUMNS.
        assert params[COLUMNS.index("site")] == "salle-tp"
        assert params[COLUMNS.index("device_id")] == "raspi-04"
        assert params[COLUMNS.index("kind")] == "humidity"
        assert params[COLUMNS.index("value")] == 47
        assert params[COLUMNS.index("unit")] == "%"
        assert params[COLUMNS.index("timestamp")] == "2026-05-28T10:00:05Z"
        assert params[COLUMNS.index("metadata_json")] == '{"room": "atelier"}'
        assert params[COLUMNS.index("received_at")] == FIXED_RECEIVED_AT

    def test_received_at_is_forwarded(self):
        adapter = MagicMock()
        repo = IotEventRepository(db_adapter=adapter)
        custom = datetime(2030, 1, 1, 0, 0, 0, tzinfo=UTC)
        repo.insert(_make_measurement(), received_at=custom)
        params = adapter.execute.call_args.args[1]
        assert params[COLUMNS.index("received_at")] == custom

    def test_received_at_default_is_naive_utc(self):
        """L'horodatage est un UTC **naïf**, comme toutes les colonnes de Forge.

        Ce test exigeait l'inverse, `tzinfo is not None`, et épinglait ainsi le
        défaut : la forme consciente était convertie par le pilote PostgreSQL
        vers l'heure locale du serveur, soit 7200 s d'écart mesurés
        (`OPTIN-AWARE-TIMESTAMP-001`).
        """
        adapter = MagicMock()
        repo = IotEventRepository(db_adapter=adapter)
        before = datetime.now(UTC).replace(tzinfo=None)
        repo.insert(_make_measurement())
        after = datetime.now(UTC).replace(tzinfo=None)
        params = adapter.execute.call_args.args[1]
        received = params[COLUMNS.index("received_at")]
        assert before <= received <= after
        assert received.tzinfo is None

    def test_metadata_none_stays_none(self):
        adapter = MagicMock()
        repo = IotEventRepository(db_adapter=adapter)
        repo.insert(_make_measurement(metadata=None), received_at=FIXED_RECEIVED_AT)
        params = adapter.execute.call_args.args[1]
        # Doit être Python None pour produire NULL côté SQL.
        assert params[COLUMNS.index("metadata_json")] is None

    def test_metadata_dict_becomes_deterministic_json(self):
        adapter = MagicMock()
        repo = IotEventRepository(db_adapter=adapter)
        # Clés volontairement inversées pour vérifier le tri.
        repo.insert(
            _make_measurement(metadata={"sensor": "dht22", "room": "atelier"}),
            received_at=FIXED_RECEIVED_AT,
        )
        params = adapter.execute.call_args.args[1]
        # sort_keys=True : 'room' avant 'sensor'.
        assert params[COLUMNS.index("metadata_json")] == (
            '{"room": "atelier", "sensor": "dht22"}'
        )


# ═══════════════════════════════════════════════════════════════════════════
# Erreurs : pas de catch silencieux
# ═══════════════════════════════════════════════════════════════════════════


class TestErrorPropagation:
    def test_db_error_propagates(self):
        adapter = MagicMock()
        adapter.execute.side_effect = RuntimeError("boom")
        repo = IotEventRepository(db_adapter=adapter)
        with pytest.raises(RuntimeError, match="boom"):
            repo.insert(_make_measurement(), received_at=FIXED_RECEIVED_AT)

    def test_specific_db_error_propagates(self):
        # Simulation d'une erreur typique « duplicate key » que le
        # repository ne doit surtout pas avaler.
        adapter = MagicMock()

        class DuplicateKeyError(Exception):
            pass

        adapter.execute.side_effect = DuplicateKeyError("Duplicate entry")
        repo = IotEventRepository(db_adapter=adapter)
        with pytest.raises(DuplicateKeyError):
            repo.insert(_make_measurement(), received_at=FIXED_RECEIVED_AT)


class TestNoManualCommitRollback:
    """Le repository ne doit ni committer ni rollbacker manuellement —
    c'est l'adapter (par défaut core.database.db.execute) qui s'en
    charge."""

    def test_does_not_call_commit_on_adapter(self):
        adapter = MagicMock()
        repo = IotEventRepository(db_adapter=adapter)
        repo.insert(_make_measurement(), received_at=FIXED_RECEIVED_AT)
        # adapter.commit/rollback ne sont jamais appelés explicitement.
        assert not adapter.commit.called
        assert not adapter.rollback.called


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous périmètre
# ═══════════════════════════════════════════════════════════════════════════


class TestRepositoryStaysFocused:
    """Pas de transport MQTT, pas de paho dans le repository."""

    def test_repository_does_not_import_paho(self):
        text = REPOSITORY_FILE.read_text(encoding="utf-8")
        import_lines = [
            line for line in text.splitlines()
            if line.lstrip().startswith(("import ", "from "))
        ]
        offenders = [line for line in import_lines if "paho" in line.lower()]
        assert not offenders, (
            f"repository.py ne doit pas importer paho-mqtt : {offenders}"
        )


class TestSubscriberStaysDecoupled:
    """Le subscriber ne doit pas être automatiquement branché au
    repository à ce ticket."""

    def test_subscriber_does_not_import_repository(self):
        text = SUBSCRIBER_FILE.read_text(encoding="utf-8")
        import_lines = [
            line for line in text.splitlines()
            if line.lstrip().startswith(("import ", "from "))
        ]
        offenders = [
            line for line in import_lines
            if "storage.repository" in line or "IotEventRepository" in line
        ]
        assert not offenders, (
            f"subscriber.py ne doit pas importer le repository à ce "
            f"ticket — le branchement reste documentaire : {offenders}"
        )


class TestNoCoreImportsIot:
    """core/ continue à ne pas dépendre du module IoT."""

    def test_no_core_module_imports_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(PROJECT_ROOT))
        assert not offenders, offenders


# ═══════════════════════════════════════════════════════════════════════════
# API publique du sous-package storage
# ═══════════════════════════════════════════════════════════════════════════


class TestStoragePublicApi:
    """Le sous-package storage expose proprement le repository."""

    def test_repository_importable_from_storage(self):
        from forge_mvc_iot.storage import IotEventRepository as Cls
        assert Cls is IotEventRepository

    def test_storage_all_lists_repository(self):
        import forge_mvc_iot.storage as storage_pkg
        assert "IotEventRepository" in storage_pkg.__all__
        assert "DbAdapter" in storage_pkg.__all__
