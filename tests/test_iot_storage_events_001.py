"""Tests du contrat SQL des événements IoT — IOT-STORAGE-EVENTS-001.

Couvre :

- ``serialize_measurement_for_storage`` (avec/sans metadata, avec/sans
  ``received_at``, sérialisation JSON déterministe, types préservés) ;
- ``build_insert_iot_event_sql`` (forme du SQL, placeholders ``?``,
  ordre des paramètres aligné sur ``COLUMNS``, table cible
  ``iot_events``) ;
- garde-fous périmètre : aucun import de ``core.database`` dans le
  module storage, aucun import IoT dans ``core/``.

Aucun broker, aucune base de données. Tests purs et reproductibles.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from forge_mvc_iot.mqtt.contract import Measurement
from forge_mvc_iot.storage import events as storage_events
from forge_mvc_iot.storage.events import (
    COLUMNS,
    INSERT_IOT_EVENT_SQL,
    TABLE_NAME,
    build_insert_iot_event_sql,
    serialize_measurement_for_storage,
)

PROJECT_ROOT = Path(__file__).parent.parent
STORAGE_MODULE_FILE = Path(storage_events.__file__)
CORE_DIR = PROJECT_ROOT / "core"


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


FIXED_RECEIVED_AT = datetime(2026, 5, 28, 10, 0, 5, tzinfo=UTC)


# ═══════════════════════════════════════════════════════════════════════════
# Constantes
# ═══════════════════════════════════════════════════════════════════════════


class TestConstants:
    def test_table_name(self):
        assert TABLE_NAME == "iot_events"

    def test_columns_order(self):
        assert COLUMNS == (
            "site",
            "device_id",
            "kind",
            "value",
            "unit",
            "timestamp",
            "metadata_json",
            "received_at",
        )

    def test_id_excluded_from_columns(self):
        # id est généré par la base ; il ne doit jamais figurer dans
        # les colonnes insérées explicitement.
        assert "id" not in COLUMNS


# ═══════════════════════════════════════════════════════════════════════════
# serialize_measurement_for_storage
# ═══════════════════════════════════════════════════════════════════════════


class TestSerializeBasics:
    def test_returns_dict_with_all_columns_as_keys(self):
        m = _make_measurement()
        row = serialize_measurement_for_storage(m, received_at=FIXED_RECEIVED_AT)
        assert set(row.keys()) == set(COLUMNS)

    def test_preserves_string_fields(self):
        m = _make_measurement()
        row = serialize_measurement_for_storage(m, received_at=FIXED_RECEIVED_AT)
        assert row["site"] == "atelier"
        assert row["device_id"] == "esp32-001"
        assert row["kind"] == "temperature"
        assert row["unit"] == "°C"
        assert row["timestamp"] == "2026-05-28T10:00:00Z"

    def test_preserves_float_value(self):
        m = _make_measurement(value=22.4)
        row = serialize_measurement_for_storage(m, received_at=FIXED_RECEIVED_AT)
        assert row["value"] == 22.4
        assert isinstance(row["value"], float)

    def test_preserves_int_value(self):
        m = _make_measurement(value=47, kind="humidity", unit="%")
        row = serialize_measurement_for_storage(m, received_at=FIXED_RECEIVED_AT)
        assert row["value"] == 47
        assert isinstance(row["value"], int)

    def test_received_at_is_returned_as_datetime(self):
        m = _make_measurement()
        row = serialize_measurement_for_storage(m, received_at=FIXED_RECEIVED_AT)
        assert isinstance(row["received_at"], datetime)
        assert row["received_at"] == FIXED_RECEIVED_AT


class TestReceivedAtDefault:
    def test_received_at_defaults_to_now_utc(self):
        m = _make_measurement()
        before = datetime.now(UTC)
        row = serialize_measurement_for_storage(m)
        after = datetime.now(UTC)

        received = row["received_at"]
        assert isinstance(received, datetime)
        # Doit être dans la fenêtre [before, after].
        assert before <= received <= after

    def test_received_at_default_is_timezone_aware_utc(self):
        m = _make_measurement()
        row = serialize_measurement_for_storage(m)
        received = row["received_at"]
        assert received.tzinfo is not None
        assert received.utcoffset() == timedelta(0)


class TestMetadataSerialization:
    def test_no_metadata_yields_none(self):
        m = _make_measurement(metadata=None)
        row = serialize_measurement_for_storage(m, received_at=FIXED_RECEIVED_AT)
        assert row["metadata_json"] is None

    def test_metadata_serialized_as_json_string(self):
        m = _make_measurement(metadata={"room": "atelier", "sensor": "dht22"})
        row = serialize_measurement_for_storage(m, received_at=FIXED_RECEIVED_AT)
        assert isinstance(row["metadata_json"], str)
        # Parsable et fidèle.
        assert json.loads(row["metadata_json"]) == {
            "room": "atelier", "sensor": "dht22",
        }

    def test_metadata_json_is_deterministic_sorted_keys(self):
        # On insère les clés volontairement dans l'ordre inverse pour
        # vérifier que sort_keys=True produit toujours la même sortie.
        m1 = _make_measurement(metadata={"sensor": "dht22", "room": "atelier"})
        m2 = _make_measurement(metadata={"room": "atelier", "sensor": "dht22"})
        row1 = serialize_measurement_for_storage(m1, received_at=FIXED_RECEIVED_AT)
        row2 = serialize_measurement_for_storage(m2, received_at=FIXED_RECEIVED_AT)
        assert row1["metadata_json"] == row2["metadata_json"]

    def test_metadata_json_keeps_utf8(self):
        m = _make_measurement(metadata={"piece": "Atelier — étage 2"})
        row = serialize_measurement_for_storage(m, received_at=FIXED_RECEIVED_AT)
        # ensure_ascii=False : pas de "é".
        assert "étage" in row["metadata_json"]
        assert "\\u" not in row["metadata_json"]

    def test_empty_metadata_dict_yields_empty_json_object(self):
        m = _make_measurement(metadata={})
        row = serialize_measurement_for_storage(m, received_at=FIXED_RECEIVED_AT)
        assert row["metadata_json"] == "{}"


# ═══════════════════════════════════════════════════════════════════════════
# build_insert_iot_event_sql
# ═══════════════════════════════════════════════════════════════════════════


class TestBuildInsertSql:
    def test_returns_tuple_str_tuple(self):
        sql, params = build_insert_iot_event_sql(
            _make_measurement(), received_at=FIXED_RECEIVED_AT,
        )
        assert isinstance(sql, str)
        assert isinstance(params, tuple)

    def test_sql_targets_iot_events_table(self):
        sql, _ = build_insert_iot_event_sql(_make_measurement())
        assert f"INSERT INTO {TABLE_NAME}" in sql
        assert "iot_events" in sql

    def test_sql_uses_qmark_placeholders(self):
        sql, _ = build_insert_iot_event_sql(_make_measurement())
        # Un placeholder par colonne.
        assert sql.count("?") == len(COLUMNS)

    def test_sql_does_not_use_named_placeholders(self):
        sql, _ = build_insert_iot_event_sql(_make_measurement())
        # Aucun %s ou :name à ce stade.
        assert "%s" not in sql
        assert not re.search(r":\w+", sql)

    def test_sql_lists_columns_in_canonical_order(self):
        sql, _ = build_insert_iot_event_sql(_make_measurement())
        column_match = re.search(r"\(([^)]+)\)\s*VALUES", sql)
        assert column_match is not None, "Liste de colonnes introuvable"
        cols = [c.strip() for c in column_match.group(1).split(",")]
        assert tuple(cols) == COLUMNS

    def test_sql_is_a_single_statement(self):
        sql, _ = build_insert_iot_event_sql(_make_measurement())
        # Pas d'instruction supplémentaire derrière le INSERT.
        # On tolère un éventuel point-virgule final mais pas plus.
        body = sql.rstrip(";").strip()
        assert ";" not in body, "Le SQL doit être une seule instruction"

    def test_exposes_static_insert_sql_constant(self):
        sql, _ = build_insert_iot_event_sql(_make_measurement())
        assert sql == INSERT_IOT_EVENT_SQL


class TestBuildInsertParams:
    def test_params_count_matches_columns(self):
        _, params = build_insert_iot_event_sql(
            _make_measurement(), received_at=FIXED_RECEIVED_AT,
        )
        assert len(params) == len(COLUMNS)

    def test_params_order_matches_columns(self):
        m = _make_measurement(
            site="salle-tp",
            device_id="raspi-04",
            kind="humidity",
            value=47,
            unit="%",
            timestamp="2026-05-28T10:00:05Z",
            metadata={"room": "atelier"},
        )
        _, params = build_insert_iot_event_sql(m, received_at=FIXED_RECEIVED_AT)
        # site, device_id, kind, value, unit, timestamp, metadata_json, received_at
        assert params[0] == "salle-tp"
        assert params[1] == "raspi-04"
        assert params[2] == "humidity"
        assert params[3] == 47
        assert params[4] == "%"
        assert params[5] == "2026-05-28T10:00:05Z"
        assert params[6] == '{"room": "atelier"}'
        assert params[7] == FIXED_RECEIVED_AT

    def test_metadata_none_passed_as_python_none(self):
        _, params = build_insert_iot_event_sql(
            _make_measurement(metadata=None),
            received_at=FIXED_RECEIVED_AT,
        )
        # Position 6 = metadata_json. Doit être None (pour donner NULL
        # côté SQL), pas la chaîne 'null'.
        assert params[6] is None

    def test_metadata_present_passed_as_json_string(self):
        _, params = build_insert_iot_event_sql(
            _make_measurement(metadata={"k": "v"}),
            received_at=FIXED_RECEIVED_AT,
        )
        assert params[6] == '{"k": "v"}'


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous périmètre
# ═══════════════════════════════════════════════════════════════════════════


class TestModuleStaysPure:
    """Le module de stockage ne se branche pas encore à la base."""

    def test_module_does_not_import_core_database(self):
        # On vérifie les *imports* (lignes commençant par 'import' /
        # 'from'), pas les mentions dans docstring qui peuvent
        # légitimement référencer le module futur.
        text = STORAGE_MODULE_FILE.read_text(encoding="utf-8")
        import_lines = [
            line for line in text.splitlines()
            if line.lstrip().startswith(("import ", "from "))
        ]
        offenders = [line for line in import_lines if "core.database" in line]
        assert not offenders, (
            "events.py ne doit pas importer core.database à ce ticket "
            f"(branchement prévu dans IOT-STORAGE-REPOSITORY-001) : {offenders}"
        )

    def test_module_does_not_import_mariadb_connector(self):
        text = STORAGE_MODULE_FILE.read_text(encoding="utf-8")
        import_lines = [
            line for line in text.splitlines()
            if line.lstrip().startswith(("import ", "from "))
        ]
        offenders = [line for line in import_lines if "mariadb" in line]
        assert not offenders, (
            "events.py ne doit pas importer le connecteur MariaDB : "
            f"{offenders}"
        )


class TestNoCoreImportsIot:
    """Garde-fou récurrent : core/ reste indépendant du module IoT."""

    def test_no_core_module_imports_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(PROJECT_ROOT))
        assert not offenders, offenders


# ═══════════════════════════════════════════════════════════════════════════
# Intégration de bout en bout — Measurement → SQL prêt à l'envoi
# ═══════════════════════════════════════════════════════════════════════════


class TestEndToEnd:
    """Une Measurement issue du subscriber produit un SQL+params valide."""

    def test_minimal_measurement_yields_complete_row(self):
        m = _make_measurement()
        sql, params = build_insert_iot_event_sql(m, received_at=FIXED_RECEIVED_AT)
        # Sanity : toutes les positions sont remplies (None autorisé
        # uniquement pour metadata_json).
        assert all(
            (p is not None) or i == COLUMNS.index("metadata_json")
            for i, p in enumerate(params)
        )
        # Le SQL est non vide et bien formé.
        assert sql.startswith("INSERT INTO iot_events")

    def test_two_measurements_yield_same_sql_different_params(self):
        m1 = _make_measurement(value=22.4)
        m2 = _make_measurement(value=23.1)
        sql1, params1 = build_insert_iot_event_sql(
            m1, received_at=FIXED_RECEIVED_AT,
        )
        sql2, params2 = build_insert_iot_event_sql(
            m2, received_at=FIXED_RECEIVED_AT,
        )
        assert sql1 == sql2
        assert params1 != params2
        # Seul le champ value diffère.
        idx_value = COLUMNS.index("value")
        for i, (p1, p2) in enumerate(zip(params1, params2)):
            if i == idx_value:
                assert p1 != p2
            else:
                assert p1 == p2
