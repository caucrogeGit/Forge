"""Tests des lectures du repository IoT — IOT-STORAGE-REPOSITORY-READ-001.

Couvre les trois méthodes de lecture ajoutées à ``IotEventRepository`` :

- ``list_recent(*, limit=100)`` ;
- ``find_by_device(site, device_id, *, limit=100)`` ;
- ``count_by_device(site, device_id)``.

Aucun MariaDB requis : tous les tests injectent un ``MagicMock`` comme
``db_adapter`` et vérifient les appels ``fetch_all``/``fetch_one`` plus
la transformation des lignes brutes en dicts consommables
(``metadata_json`` JSON ↔ ``metadata`` dict).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.storage.repository import (
    COUNT_IOT_EVENTS_BY_DEVICE_SQL,
    DEFAULT_LIMIT,
    MAX_LIMIT,
    IotEventRepository,
    select_iot_events_by_device_sql,
    select_iot_events_recent_sql,
)

def _limit_clause() -> str:
    """Borne attendue pour le backend actif (conftest : mariadb)."""
    from core.database.backend import get_backend

    return get_backend().dialect.limit_clause()


PROJECT_ROOT = Path(__file__).parent.parent
IOT_PKG_DIR = PROJECT_ROOT / "packages" / "forge-mvc-iot"
REPOSITORY_FILE = IOT_PKG_DIR / "forge_mvc_iot" / "storage" / "repository.py"


def _row(
    *,
    id: int = 1,
    site: str = "atelier",
    device_id: str = "esp32-001",
    kind: str = "temperature",
    value: float = 22.4,
    unit: str = "°C",
    timestamp: str = "2026-05-28T10:00:00Z",
    metadata_json: str | None = None,
    received_at: datetime | None = None,
) -> dict:
    return {
        "id": id,
        "site": site,
        "device_id": device_id,
        "kind": kind,
        "value": value,
        "unit": unit,
        "timestamp": timestamp,
        "metadata_json": metadata_json,
        "received_at": received_at or datetime(2026, 5, 28, 10, 0, 0, tzinfo=UTC),
    }


# ═══════════════════════════════════════════════════════════════════════════
# SQL exposés
# ═══════════════════════════════════════════════════════════════════════════


class TestReadSqlConstants:
    """Les requêtes SQL sont visibles et lisibles (charte v2 §5)."""

    def test_select_recent_targets_iot_events_with_order_and_limit(self):
        sql = select_iot_events_recent_sql()
        assert "FROM iot_events" in sql
        assert "ORDER BY received_at DESC" in sql
        assert sql.endswith(_limit_clause())
        # Toutes les colonnes lisibles (id + COLUMNS).
        for col in (
            "id", "site", "device_id", "kind", "value",
            "unit", "timestamp", "metadata_json", "received_at",
        ):
            assert col in sql

    def test_select_by_device_uses_where_site_and_device_id(self):
        sql = select_iot_events_by_device_sql()
        assert "FROM iot_events" in sql
        assert "WHERE site = ? AND device_id = ?" in sql
        assert "ORDER BY received_at DESC" in sql
        assert sql.endswith(_limit_clause())

    def test_count_by_device_returns_n(self):
        sql = COUNT_IOT_EVENTS_BY_DEVICE_SQL
        assert "COUNT(*)" in sql
        assert "AS n" in sql
        assert "FROM iot_events" in sql
        assert "WHERE site = ? AND device_id = ?" in sql

    def test_no_select_uses_named_placeholders(self):
        for sql in (
            select_iot_events_recent_sql(),
            select_iot_events_by_device_sql(),
            COUNT_IOT_EVENTS_BY_DEVICE_SQL,
        ):
            assert "%s" not in sql
            assert ":" not in sql.replace("AS ", "")


# ═══════════════════════════════════════════════════════════════════════════
# list_recent
# ═══════════════════════════════════════════════════════════════════════════


class TestListRecent:
    def test_calls_fetch_all_with_correct_sql_and_default_limit(self):
        adapter = MagicMock()
        adapter.fetch_all.return_value = []
        repo = IotEventRepository(db_adapter=adapter)
        repo.list_recent()
        adapter.fetch_all.assert_called_once_with(
            select_iot_events_recent_sql(), (DEFAULT_LIMIT,),
        )

    def test_custom_limit_is_forwarded(self):
        adapter = MagicMock()
        adapter.fetch_all.return_value = []
        repo = IotEventRepository(db_adapter=adapter)
        repo.list_recent(limit=7)
        adapter.fetch_all.assert_called_once_with(
            select_iot_events_recent_sql(), (7,),
        )

    def test_returns_list_of_dicts_with_metadata_parsed(self):
        adapter = MagicMock()
        adapter.fetch_all.return_value = [
            _row(metadata_json='{"room": "atelier", "sensor": "dht22"}'),
        ]
        repo = IotEventRepository(db_adapter=adapter)
        result = repo.list_recent()
        assert len(result) == 1
        ev = result[0]
        assert ev["site"] == "atelier"
        assert ev["device_id"] == "esp32-001"
        assert ev["metadata"] == {"room": "atelier", "sensor": "dht22"}
        # metadata_json (clé interne) ne doit pas fuiter au consommateur.
        assert "metadata_json" not in ev

    def test_metadata_null_in_row_becomes_python_none(self):
        adapter = MagicMock()
        adapter.fetch_all.return_value = [_row(metadata_json=None)]
        repo = IotEventRepository(db_adapter=adapter)
        result = repo.list_recent()
        assert result[0]["metadata"] is None

    def test_empty_result(self):
        adapter = MagicMock()
        adapter.fetch_all.return_value = []
        repo = IotEventRepository(db_adapter=adapter)
        assert repo.list_recent() == []

    def test_db_error_propagates(self):
        adapter = MagicMock()
        adapter.fetch_all.side_effect = RuntimeError("connection lost")
        repo = IotEventRepository(db_adapter=adapter)
        with pytest.raises(RuntimeError, match="connection lost"):
            repo.list_recent()


# ═══════════════════════════════════════════════════════════════════════════
# find_by_device
# ═══════════════════════════════════════════════════════════════════════════


class TestFindByDevice:
    def test_calls_fetch_all_with_site_device_and_default_limit(self):
        adapter = MagicMock()
        adapter.fetch_all.return_value = []
        repo = IotEventRepository(db_adapter=adapter)
        repo.find_by_device("atelier", "esp32-001")
        adapter.fetch_all.assert_called_once_with(
            select_iot_events_by_device_sql(),
            ("atelier", "esp32-001", DEFAULT_LIMIT),
        )

    def test_custom_limit_is_forwarded(self):
        adapter = MagicMock()
        adapter.fetch_all.return_value = []
        repo = IotEventRepository(db_adapter=adapter)
        repo.find_by_device("atelier", "esp32-001", limit=5)
        adapter.fetch_all.assert_called_once_with(
            select_iot_events_by_device_sql(),
            ("atelier", "esp32-001", 5),
        )

    def test_returns_processed_rows(self):
        adapter = MagicMock()
        adapter.fetch_all.return_value = [
            _row(id=10, metadata_json='{"sensor": "bme280"}'),
            _row(id=11, metadata_json=None),
        ]
        repo = IotEventRepository(db_adapter=adapter)
        rows = repo.find_by_device("atelier", "esp32-001")
        assert [r["id"] for r in rows] == [10, 11]
        assert rows[0]["metadata"] == {"sensor": "bme280"}
        assert rows[1]["metadata"] is None

    def test_empty_result(self):
        adapter = MagicMock()
        adapter.fetch_all.return_value = []
        repo = IotEventRepository(db_adapter=adapter)
        assert repo.find_by_device("atelier", "esp32-001") == []

    def test_db_error_propagates(self):
        adapter = MagicMock()
        adapter.fetch_all.side_effect = RuntimeError("db down")
        repo = IotEventRepository(db_adapter=adapter)
        with pytest.raises(RuntimeError, match="db down"):
            repo.find_by_device("atelier", "esp32-001")


# ═══════════════════════════════════════════════════════════════════════════
# count_by_device
# ═══════════════════════════════════════════════════════════════════════════


class TestCountByDevice:
    def test_calls_fetch_one_with_correct_sql_and_params(self):
        adapter = MagicMock()
        adapter.fetch_one.return_value = {"n": 42}
        repo = IotEventRepository(db_adapter=adapter)
        repo.count_by_device("atelier", "esp32-001")
        adapter.fetch_one.assert_called_once_with(
            COUNT_IOT_EVENTS_BY_DEVICE_SQL,
            ("atelier", "esp32-001"),
        )

    def test_returns_int(self):
        adapter = MagicMock()
        adapter.fetch_one.return_value = {"n": 42}
        repo = IotEventRepository(db_adapter=adapter)
        n = repo.count_by_device("atelier", "esp32-001")
        assert n == 42
        assert isinstance(n, int)

    def test_returns_zero_when_row_is_none(self):
        # COUNT(*) renvoie toujours une ligne en MariaDB, mais on
        # protège contre un adapter qui retournerait None.
        adapter = MagicMock()
        adapter.fetch_one.return_value = None
        repo = IotEventRepository(db_adapter=adapter)
        assert repo.count_by_device("atelier", "esp32-001") == 0

    def test_returns_zero_count_when_table_empty(self):
        adapter = MagicMock()
        adapter.fetch_one.return_value = {"n": 0}
        repo = IotEventRepository(db_adapter=adapter)
        assert repo.count_by_device("atelier", "esp32-001") == 0

    def test_db_error_propagates(self):
        adapter = MagicMock()
        adapter.fetch_one.side_effect = RuntimeError("timeout")
        repo = IotEventRepository(db_adapter=adapter)
        with pytest.raises(RuntimeError, match="timeout"):
            repo.count_by_device("atelier", "esp32-001")


# ═══════════════════════════════════════════════════════════════════════════
# Validation du limit
# ═══════════════════════════════════════════════════════════════════════════


class TestLimitValidation:
    @pytest.mark.parametrize("bad", [0, -1, -100])
    def test_limit_zero_or_negative_refused_list_recent(self, bad):
        repo = IotEventRepository(db_adapter=MagicMock())
        with pytest.raises(ValueError, match="limit"):
            repo.list_recent(limit=bad)

    @pytest.mark.parametrize("bad", [0, -1])
    def test_limit_zero_or_negative_refused_find_by_device(self, bad):
        repo = IotEventRepository(db_adapter=MagicMock())
        with pytest.raises(ValueError, match="limit"):
            repo.find_by_device("s", "d", limit=bad)

    def test_limit_above_max_refused(self):
        repo = IotEventRepository(db_adapter=MagicMock())
        with pytest.raises(ValueError, match="limit"):
            repo.list_recent(limit=MAX_LIMIT + 1)

    def test_limit_at_max_accepted(self):
        adapter = MagicMock()
        adapter.fetch_all.return_value = []
        repo = IotEventRepository(db_adapter=adapter)
        repo.list_recent(limit=MAX_LIMIT)  # ne doit pas lever
        adapter.fetch_all.assert_called_once_with(
            select_iot_events_recent_sql(), (MAX_LIMIT,),
        )

    @pytest.mark.parametrize("bad", ["10", 3.5, None, [10]])
    def test_non_int_limit_refused(self, bad):
        repo = IotEventRepository(db_adapter=MagicMock())
        with pytest.raises((TypeError, ValueError)):
            repo.list_recent(limit=bad)

    def test_bool_refused_even_though_subclass_of_int(self):
        # True et False sont des int en Python ; on les exclut
        # explicitement pour éviter les surprises.
        repo = IotEventRepository(db_adapter=MagicMock())
        with pytest.raises(TypeError):
            repo.list_recent(limit=True)


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous périmètre
# ═══════════════════════════════════════════════════════════════════════════


class TestRepositoryStaysFocused:
    """Pas d'import paho ni subscriber dans le repository."""

    def test_repository_does_not_import_paho_or_subscriber(self):
        text = REPOSITORY_FILE.read_text(encoding="utf-8")
        import_lines = [
            line for line in text.splitlines()
            if line.lstrip().startswith(("import ", "from "))
        ]
        for line in import_lines:
            assert "paho" not in line.lower(), (
                f"repository.py ne doit pas importer paho : {line!r}"
            )
            assert "subscriber" not in line.lower(), (
                f"repository.py ne doit pas importer le subscriber : {line!r}"
            )

    def test_repository_does_not_define_http_routes(self):
        text = REPOSITORY_FILE.read_text(encoding="utf-8")
        # Pas de décorateurs route, pas de référence à un router.
        for forbidden in ("@route", "Router(", "Response(", "@app.route"):
            assert forbidden not in text, (
                f"repository.py ne doit pas définir de route HTTP "
                f"(trouvé : {forbidden!r})"
            )


# ═══════════════════════════════════════════════════════════════════════════
# API publique du sous-package storage
# ═══════════════════════════════════════════════════════════════════════════


class TestStoragePublicApi:
    def test_read_sql_exported(self):
        from forge_mvc_iot import storage as storage_pkg
        for name in (
            "select_iot_events_recent_sql",
            "select_iot_events_by_device_sql",
            "COUNT_IOT_EVENTS_BY_DEVICE_SQL",
            "DEFAULT_LIMIT",
            "MAX_LIMIT",
        ):
            assert name in storage_pkg.__all__
            assert hasattr(storage_pkg, name)

    def test_read_methods_exposed_on_repository(self):
        repo = IotEventRepository(db_adapter=MagicMock())
        for method in ("list_recent", "find_by_device", "count_by_device"):
            assert callable(getattr(repo, method)), (
                f"IotEventRepository.{method} doit être appelable"
            )


# ═══════════════════════════════════════════════════════════════════════════
# Sanity — insert intact
# ═══════════════════════════════════════════════════════════════════════════


class TestInsertStillWorks:
    """Sanity : l'ajout des méthodes de lecture ne casse pas insert."""

    def test_insert_still_delegates_to_execute(self):
        from forge_mvc_iot.mqtt.contract import Measurement

        adapter = MagicMock()
        repo = IotEventRepository(db_adapter=adapter)
        m = Measurement(
            site="atelier", device_id="esp32-001",
            kind="temperature", value=22.4, unit="°C",
            timestamp="2026-05-28T10:00:00Z", metadata=None,
        )
        repo.insert(m)
        adapter.execute.assert_called_once()
        adapter.fetch_all.assert_not_called()
        adapter.fetch_one.assert_not_called()
