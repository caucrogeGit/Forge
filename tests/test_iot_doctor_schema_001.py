"""Tests de ``forge iot:doctor --db`` — contrôle du schéma — IOT-DOCTOR-SCHEMA-001.

Vérifie ``check_database_schema()`` et son orchestration :

- schéma conforme → ``ok`` ;
- colonne manquante → ``warn`` clair + conseil ;
- colonne supplémentaire → ``ok`` (tolérée, migration future) ;
- type SQL inattendu → ``warn`` ;
- nullable inattendu → ``warn`` ;
- ``id`` sans AUTO_INCREMENT → ``warn`` ;
- ``metadata_json`` nullable accepté ;
- ``received_at`` DATETIME(6) attendu ;
- échec de lecture système (exception) → ``fail`` ;
- ``--db`` déclenche aussi le contrôle de schéma quand la table est ok ;
- sans ``--db``, aucun import DB et aucun check schéma ;
- sortie sans fuite de SQL brut excessive.

Aucun MariaDB requis : ``check_database_schema`` accepte un
``fetch_all_func`` injectable, et ``main`` est testé via
``monkeypatch.setattr`` sur le module ``doctor``.
"""

from __future__ import annotations

from pathlib import Path

from forge_mvc_iot.cli import doctor as doctor_module
from forge_mvc_iot.cli.doctor import (
    CheckResult,
    check_database_schema,
    has_failures,
    main,
    run_all,
)

PROJECT_ROOT = Path(__file__).parent.parent
DOCTOR_FILE = (
    PROJECT_ROOT / "packages" / "forge-mvc-iot" / "forge_mvc_iot"
    / "cli" / "doctor.py"
)


# ── Helpers de fixture ─────────────────────────────────────────────────────


def _conforming_rows() -> list[dict[str, str]]:
    """Schéma exact attendu, tel que renvoyé par INFORMATION_SCHEMA.COLUMNS."""
    return [
        {"COLUMN_NAME": "id", "DATA_TYPE": "bigint",
         "COLUMN_TYPE": "bigint(20) unsigned", "IS_NULLABLE": "NO",
         "EXTRA": "auto_increment"},
        {"COLUMN_NAME": "site", "DATA_TYPE": "varchar",
         "COLUMN_TYPE": "varchar(64)", "IS_NULLABLE": "NO", "EXTRA": ""},
        {"COLUMN_NAME": "device_id", "DATA_TYPE": "varchar",
         "COLUMN_TYPE": "varchar(64)", "IS_NULLABLE": "NO", "EXTRA": ""},
        {"COLUMN_NAME": "kind", "DATA_TYPE": "varchar",
         "COLUMN_TYPE": "varchar(64)", "IS_NULLABLE": "NO", "EXTRA": ""},
        {"COLUMN_NAME": "value", "DATA_TYPE": "double",
         "COLUMN_TYPE": "double", "IS_NULLABLE": "NO", "EXTRA": ""},
        {"COLUMN_NAME": "unit", "DATA_TYPE": "varchar",
         "COLUMN_TYPE": "varchar(32)", "IS_NULLABLE": "NO", "EXTRA": ""},
        {"COLUMN_NAME": "timestamp", "DATA_TYPE": "varchar",
         "COLUMN_TYPE": "varchar(40)", "IS_NULLABLE": "NO", "EXTRA": ""},
        {"COLUMN_NAME": "metadata_json", "DATA_TYPE": "text",
         "COLUMN_TYPE": "text", "IS_NULLABLE": "YES", "EXTRA": ""},
        {"COLUMN_NAME": "received_at", "DATA_TYPE": "datetime",
         "COLUMN_TYPE": "datetime(6)", "IS_NULLABLE": "NO", "EXTRA": ""},
    ]


def _fetch_all_returning(rows):
    def _stub(sql, params=()):
        return rows
    return _stub


def _fetch_all_raises(exc: Exception):
    def _stub(sql, params=()):
        raise exc
    return _stub


def _without(rows, name):
    return [r for r in rows if r["COLUMN_NAME"] != name]


def _patch(rows, name, **changes):
    out = []
    for r in rows:
        if r["COLUMN_NAME"] == name:
            r = {**r, **changes}
        out.append(r)
    return out


# ═══════════════════════════════════════════════════════════════════════════
# Schéma conforme
# ═══════════════════════════════════════════════════════════════════════════


class TestSchemaConforming:
    def test_conforming_schema_is_ok(self):
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(_conforming_rows()),
        )
        assert result.status == "ok"
        assert result.label == "schéma iot_events"
        assert "conforme" in result.detail

    def test_metadata_json_nullable_accepted(self):
        # metadata_json doit être TEXT NULL — déjà le cas dans le schéma
        # conforme, donc aucun warn lié à cette colonne.
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(_conforming_rows()),
        )
        assert result.status == "ok"

    def test_received_at_datetime6_accepted(self):
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(_conforming_rows()),
        )
        assert result.status == "ok"

    def test_lowercase_keys_supported(self):
        # Certains connecteurs renvoient les clés en minuscules.
        rows = [
            {k.lower(): v for k, v in row.items()}
            for row in _conforming_rows()
        ]
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(rows),
        )
        assert result.status == "ok"

    def test_bigint_without_display_width_still_ok(self):
        # MySQL 8 / MariaDB récent peuvent omettre la largeur d'affichage.
        rows = _patch(
            _conforming_rows(), "id", COLUMN_TYPE="bigint unsigned",
        )
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(rows),
        )
        assert result.status == "ok"


# ═══════════════════════════════════════════════════════════════════════════
# Colonne manquante
# ═══════════════════════════════════════════════════════════════════════════


class TestMissingColumn:
    def test_missing_column_is_warn(self):
        rows = _without(_conforming_rows(), "metadata_json")
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(rows),
        )
        assert result.status == "warn"
        all_text = result.detail + " " + " ".join(result.lines)
        assert "colonne manquante" in all_text
        assert "metadata_json" in all_text

    def test_missing_column_includes_hint(self):
        rows = _without(_conforming_rows(), "value")
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(rows),
        )
        all_text = result.detail + " " + " ".join(result.lines)
        assert "migration" in all_text.lower()

    def test_empty_table_is_warn_not_crash(self):
        # Aucune ligne : table absente → warn sobre, pas de crash.
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning([]),
        )
        assert result.status == "warn"


# ═══════════════════════════════════════════════════════════════════════════
# Colonne supplémentaire → tolérée (OK)
# ═══════════════════════════════════════════════════════════════════════════


class TestExtraColumn:
    def test_extra_column_is_ok(self):
        rows = _conforming_rows()
        rows.append({
            "COLUMN_NAME": "future_field", "DATA_TYPE": "varchar",
            "COLUMN_TYPE": "varchar(10)", "IS_NULLABLE": "YES", "EXTRA": "",
        })
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(rows),
        )
        assert result.status == "ok"


# ═══════════════════════════════════════════════════════════════════════════
# Type SQL inattendu
# ═══════════════════════════════════════════════════════════════════════════


class TestUnexpectedType:
    def test_wrong_type_is_warn(self):
        rows = _patch(
            _conforming_rows(), "value",
            DATA_TYPE="varchar", COLUMN_TYPE="varchar(255)",
        )
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(rows),
        )
        assert result.status == "warn"
        all_text = result.detail + " " + " ".join(result.lines)
        assert "type inattendu" in all_text
        assert "value" in all_text
        assert "DOUBLE" in all_text
        assert "VARCHAR(255)" in all_text

    def test_wrong_varchar_length_is_warn(self):
        rows = _patch(
            _conforming_rows(), "site",
            COLUMN_TYPE="varchar(32)",
        )
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(rows),
        )
        assert result.status == "warn"
        assert "site" in (result.detail + " ".join(result.lines))

    def test_wrong_datetime_precision_is_warn(self):
        rows = _patch(
            _conforming_rows(), "received_at",
            COLUMN_TYPE="datetime",
        )
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(rows),
        )
        assert result.status == "warn"

    def test_unsigned_mismatch_is_warn(self):
        # id signé (sans unsigned) → type inattendu.
        rows = _patch(
            _conforming_rows(), "id",
            COLUMN_TYPE="bigint(20)",
        )
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(rows),
        )
        assert result.status == "warn"


# ═══════════════════════════════════════════════════════════════════════════
# Nullable inattendu
# ═══════════════════════════════════════════════════════════════════════════


class TestUnexpectedNullable:
    def test_not_null_expected_but_nullable_is_warn(self):
        rows = _patch(
            _conforming_rows(), "site", IS_NULLABLE="YES",
        )
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(rows),
        )
        assert result.status == "warn"
        all_text = result.detail + " " + " ".join(result.lines)
        assert "nullable" in all_text.lower()
        assert "site" in all_text

    def test_nullable_expected_but_not_null_is_warn(self):
        # metadata_json doit accepter NULL ; NOT NULL est une divergence.
        rows = _patch(
            _conforming_rows(), "metadata_json", IS_NULLABLE="NO",
        )
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(rows),
        )
        assert result.status == "warn"
        assert "metadata_json" in (result.detail + " ".join(result.lines))


# ═══════════════════════════════════════════════════════════════════════════
# id sans AUTO_INCREMENT
# ═══════════════════════════════════════════════════════════════════════════


class TestAutoIncrement:
    def test_id_without_auto_increment_is_warn(self):
        rows = _patch(_conforming_rows(), "id", EXTRA="")
        result = check_database_schema(
            fetch_all_func=_fetch_all_returning(rows),
        )
        assert result.status == "warn"
        all_text = result.detail + " " + " ".join(result.lines)
        assert "AUTO_INCREMENT" in all_text
        assert "id" in all_text


# ═══════════════════════════════════════════════════════════════════════════
# Échec de lecture système → FAIL
# ═══════════════════════════════════════════════════════════════════════════


class TestSystemReadFailure:
    def test_fetch_all_exception_is_fail(self):
        result = check_database_schema(
            fetch_all_func=_fetch_all_raises(RuntimeError("boom")),
        )
        assert result.status == "fail"
        assert result.label == "schéma iot_events"

    def test_fail_message_is_sober(self):
        result = check_database_schema(
            fetch_all_func=_fetch_all_raises(RuntimeError("boom")),
        )
        assert "Traceback" not in result.detail
        # Pas de fuite de SQL brut dans la sortie utilisateur.
        assert "INFORMATION_SCHEMA" not in result.detail
        assert "SELECT" not in result.detail


# ═══════════════════════════════════════════════════════════════════════════
# Orchestration : --db déclenche le contrôle de schéma
# ═══════════════════════════════════════════════════════════════════════════


class TestRunAllSchemaToggle:
    def test_schema_checked_when_table_ok(self, monkeypatch):
        monkeypatch.setattr(
            doctor_module, "check_database_table",
            lambda **kw: CheckResult(
                status="ok", label="base iot_events",
                detail="table accessible (3 événement(s))",
            ),
        )
        called: list[bool] = []
        monkeypatch.setattr(
            doctor_module, "check_database_schema",
            lambda **kw: called.append(True) or CheckResult(
                status="ok", label="schéma iot_events", detail="conforme",
            ),
        )
        results = run_all(test_db=True)
        assert called == [True]
        schema = next(
            (r for r in results if r.label == "schéma iot_events"), None,
        )
        assert schema is not None
        assert schema.status == "ok"

    def test_schema_skipped_when_table_warn(self, monkeypatch):
        # Table absente (warn) → on ne ré-émet pas un check schéma.
        monkeypatch.setattr(
            doctor_module, "check_database_table",
            lambda **kw: CheckResult(
                status="warn", label="base iot_events",
                detail="table absente ou migration non appliquée",
            ),
        )
        def _should_not_run(**kw):
            raise AssertionError("schéma vérifié alors que la table est absente")
        monkeypatch.setattr(
            doctor_module, "check_database_schema", _should_not_run,
        )
        results = run_all(test_db=True)
        labels = [r.label for r in results]
        assert "schéma iot_events" not in labels

    def test_schema_skipped_when_table_fail(self, monkeypatch):
        monkeypatch.setattr(
            doctor_module, "check_database_table",
            lambda **kw: CheckResult(
                status="fail", label="base iot_events",
                detail="connexion MariaDB impossible — …",
            ),
        )
        def _should_not_run(**kw):
            raise AssertionError("schéma vérifié alors que la connexion échoue")
        monkeypatch.setattr(
            doctor_module, "check_database_schema", _should_not_run,
        )
        results = run_all(test_db=True)
        assert "schéma iot_events" not in [r.label for r in results]
        # Le fail de la table reste un fail global.
        assert has_failures(results) is True

    def test_no_schema_check_without_db_flag(self, monkeypatch):
        def _should_not_run(**kw):
            raise AssertionError("check_database_schema appelé sans --db")
        monkeypatch.setattr(
            doctor_module, "check_database_schema", _should_not_run,
        )
        results = run_all()
        assert "schéma iot_events" not in [r.label for r in results]


# ═══════════════════════════════════════════════════════════════════════════
# Orchestration : main(--db)
# ═══════════════════════════════════════════════════════════════════════════


class TestMainSchema:
    def test_main_db_prints_schema_ok(self, monkeypatch, capsys):
        monkeypatch.setattr(
            doctor_module, "check_database_table",
            lambda **kw: CheckResult(
                status="ok", label="base iot_events",
                detail="table accessible (0 événement(s))",
            ),
        )
        monkeypatch.setattr(
            doctor_module, "check_database_schema",
            lambda **kw: CheckResult(
                status="ok", label="schéma iot_events", detail="conforme",
            ),
        )
        rc = main(["--db"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "schéma iot_events" in out
        assert "conforme" in out

    def test_main_db_schema_warn_does_not_exit_1(self, monkeypatch, capsys):
        monkeypatch.setattr(
            doctor_module, "check_database_table",
            lambda **kw: CheckResult(
                status="ok", label="base iot_events",
                detail="table accessible (1 événement(s))",
            ),
        )
        monkeypatch.setattr(
            doctor_module, "check_database_schema",
            lambda **kw: CheckResult(
                status="warn", label="schéma iot_events",
                detail="colonne manquante : metadata_json",
                lines=("Conseil : vérifie la migration Forge IoT.",),
            ),
        )
        rc = main(["--db"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[WARN]" in out
        assert "metadata_json" in out


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous périmètre
# ═══════════════════════════════════════════════════════════════════════════


class TestLazyDbImport:
    def test_db_imported_lazily_in_schema_check(self):
        src = DOCTOR_FILE.read_text(encoding="utf-8")
        head, *_ = src.split("def check_database_schema")
        assert "from core.database import fetch_all" not in head
        assert "from core.database.db import fetch_all" not in head


class TestNoSchemaCorrection:
    """Le ticket diagnostique, il ne répare pas : aucun ALTER / migration."""

    def test_no_alter_or_migration_in_schema_check(self):
        src = DOCTOR_FILE.read_text(encoding="utf-8")
        idx = src.find("def check_database_schema")
        end = src.find("def _default_mqtt_client_factory")
        block = src[idx:end].upper()
        assert "ALTER TABLE" not in block
        assert "DROP COLUMN" not in block
        assert "DROP TABLE" not in block
