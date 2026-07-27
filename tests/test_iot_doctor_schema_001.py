"""Tests de ``forge iot:doctor --db`` — contrôle du schéma — IOT-DOCTOR-SCHEMA-001.

Vérifie ``check_database_schema()`` et son orchestration :

- schéma conforme → ``ok`` ;
- colonne manquante → ``warn`` clair + conseil ;
- colonne supplémentaire → ``ok`` (tolérée, migration future) ;
- type SQL inattendu → ``warn`` ;
- nullable inattendu → ``warn`` ;
- ``id`` sans AUTO_INCREMENT → ``warn`` ;
- ``metadata_json`` nullable accepté ;
- ``received_at`` du bon type attendu ;
- échec de lecture système (exception) → ``fail`` ;
- ``--db`` déclenche aussi le contrôle de schéma quand la table est ok ;
- sans ``--db``, aucun import DB et aucun check schéma ;
- sortie sans fuite de SQL brut excessive.

Aucun serveur requis : ``check_database_schema`` accepte un
``introspect_func`` injectable, et ``main`` est testé via
``monkeypatch.setattr`` sur le module ``doctor``.

Depuis ``OPTIN-DDL-IOT-DOCTOR-001``, le contrôle passe par
``Dialect.introspect_columns`` au lieu d'une requête ``INFORMATION_SCHEMA``
écrite en dur, qui ne valait que pour MariaDB et n'existe pas sur SQLite.
Les lignes injectées suivent donc le contrat d'introspection :
``(nom, type_sql, nullable, auto_increment)``.

Ce que le contrôle ne détecte plus, et c'est assumé : l'attribut ``UNSIGNED``,
propre à MariaDB et absent des trois autres backends. La longueur reste
vérifiée quand le moteur la fournit à l'introspection (MariaDB), et ignorée
quand il ne la donne pas (PostgreSQL, SQL Server).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_iot")

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


def _conforming_rows() -> list[tuple[str, str, bool, bool]]:
    """Schéma attendu, au format de ``Dialect.introspect_columns``.

    Valeurs telles que MariaDB les renvoie réellement (mesuré) :
    ``bigint(20) unsigned``, ``varchar(64)``, ``datetime``.
    """
    return [
        ("id", "bigint(20) unsigned", False, True),
        ("site", "varchar(64)", False, False),
        ("device_id", "varchar(64)", False, False),
        ("kind", "varchar(64)", False, False),
        ("value", "double", False, False),
        ("unit", "varchar(32)", False, False),
        ("timestamp", "varchar(40)", False, False),
        ("metadata_json", "text", True, False),
        ("received_at", "datetime", False, False),
    ]


def _fetch_all_returning(rows):
    def _stub():
        return rows
    return _stub


def _fetch_all_raises(exc: Exception):
    def _stub():
        raise exc
    return _stub


def _without(rows, name):
    return [r for r in rows if r[0] != name]


def _patch(rows, name, *, sql_type=None, nullable=None, auto=None):
    out = []
    for row in rows:
        if row[0] == name:
            row = (
                row[0],
                sql_type if sql_type is not None else row[1],
                nullable if nullable is not None else row[2],
                auto if auto is not None else row[3],
            )
        out.append(row)
    return out


# ═══════════════════════════════════════════════════════════════════════════
# Schéma conforme
# ═══════════════════════════════════════════════════════════════════════════


class TestSchemaConforming:
    def test_conforming_schema_is_ok(self):
        result = check_database_schema(
            introspect_func=_fetch_all_returning(_conforming_rows()),
        )
        assert result.status == "ok"
        assert result.label == "schéma iot_events"
        assert "conforme" in result.detail

    def test_metadata_json_nullable_accepted(self):
        # metadata_json doit être TEXT NULL — déjà le cas dans le schéma
        # conforme, donc aucun warn lié à cette colonne.
        result = check_database_schema(
            introspect_func=_fetch_all_returning(_conforming_rows()),
        )
        assert result.status == "ok"

    def test_received_at_datetime6_accepted(self):
        result = check_database_schema(
            introspect_func=_fetch_all_returning(_conforming_rows()),
        )
        assert result.status == "ok"

    def test_types_majuscules_supportes(self):
        """SQL Server renvoie ses types en majuscules : la comparaison est
        insensible a la casse (mesure : BIGINT, NVARCHAR)."""
        rows = [(n, t.upper(), null, auto) for n, t, null, auto in _conforming_rows()]
        result = check_database_schema(introspect_func=_fetch_all_returning(rows))
        assert result.status == "ok", result.detail


    def test_bigint_sans_largeur_toujours_ok(self):
        """PostgreSQL et SQL Server renvoient `bigint` sans largeur."""
        rows = _patch(_conforming_rows(), "id", sql_type="bigint")
        result = check_database_schema(introspect_func=_fetch_all_returning(rows))
        assert result.status == "ok", result.detail



class TestMissingColumn:
    def test_missing_column_is_warn(self):
        rows = _without(_conforming_rows(), "metadata_json")
        result = check_database_schema(
            introspect_func=_fetch_all_returning(rows),
        )
        assert result.status == "warn"
        all_text = result.detail + " " + " ".join(result.lines)
        assert "colonne manquante" in all_text
        assert "metadata_json" in all_text

    def test_missing_column_includes_hint(self):
        rows = _without(_conforming_rows(), "value")
        result = check_database_schema(
            introspect_func=_fetch_all_returning(rows),
        )
        all_text = result.detail + " " + " ".join(result.lines)
        assert "migration" in all_text.lower()

    def test_empty_table_is_warn_not_crash(self):
        # Aucune ligne : table absente → warn sobre, pas de crash.
        result = check_database_schema(
            introspect_func=_fetch_all_returning([]),
        )
        assert result.status == "warn"


# ═══════════════════════════════════════════════════════════════════════════
# Colonne supplémentaire → tolérée (OK)
# ═══════════════════════════════════════════════════════════════════════════


class TestExtraColumn:
    def test_extra_column_is_ok(self):
        rows = _conforming_rows() + [("colonne_future", "varchar(10)", True, False)]
        result = check_database_schema(introspect_func=_fetch_all_returning(rows))
        assert result.status == "ok", result.detail



class TestUnexpectedType:
    def test_wrong_type_is_warn(self):
        """Une famille differente est detectee : texte la ou un nombre est attendu."""
        rows = _patch(_conforming_rows(), "value", sql_type="varchar(20)")
        result = check_database_schema(introspect_func=_fetch_all_returning(rows))
        assert result.status == "warn"
        assert "value" in result.detail


    def test_wrong_varchar_length_is_warn(self):
        """La longueur reste verifiee quand le moteur la fournit (MariaDB)."""
        rows = _patch(_conforming_rows(), "site", sql_type="varchar(255)")
        result = check_database_schema(introspect_func=_fetch_all_returning(rows))
        assert result.status == "warn"
        assert "site" in result.detail

    def test_longueur_absente_ne_declenche_rien(self):
        """PostgreSQL renvoie `character varying` sans longueur : pas de faux positif."""
        rows = _patch(_conforming_rows(), "site", sql_type="character varying")
        result = check_database_schema(introspect_func=_fetch_all_returning(rows))
        assert result.status == "ok", result.detail


    def test_datetime_dun_autre_backend_est_accepte(self):
        """PostgreSQL renvoie `timestamp without time zone`, SQL Server
        `DATETIME2` : meme famille, aucun ecart signale."""
        for observed in ("timestamp without time zone", "DATETIME2"):
            rows = _patch(_conforming_rows(), "received_at", sql_type=observed)
            result = check_database_schema(introspect_func=_fetch_all_returning(rows))
            assert result.status == "ok", f"{observed} : {result.detail}"


    def test_unsigned_nest_plus_verifie(self):
        """Perte assumee : UNSIGNED est propre a MariaDB, absent des trois
        autres backends. Le controle porte sur la famille, pas sur cet
        attribut (OPTIN-DDL-IOT-DOCTOR-001)."""
        rows = _patch(_conforming_rows(), "id", sql_type="bigint(20)")
        result = check_database_schema(introspect_func=_fetch_all_returning(rows))
        assert result.status == "ok", result.detail



class TestUnexpectedNullable:
    def test_not_null_expected_but_nullable_is_warn(self):
        rows = _patch(_conforming_rows(), "site", nullable=True)
        result = check_database_schema(introspect_func=_fetch_all_returning(rows))
        assert result.status == "warn"
        assert "site" in result.detail


    def test_nullable_expected_but_not_null_is_warn(self):
        rows = _patch(_conforming_rows(), "metadata_json", nullable=False)
        result = check_database_schema(introspect_func=_fetch_all_returning(rows))
        assert result.status == "warn"
        assert "metadata_json" in result.detail



class TestAutoIncrement:
    def test_id_without_auto_increment_is_warn(self):
        rows = _patch(_conforming_rows(), "id", auto=False)
        result = check_database_schema(introspect_func=_fetch_all_returning(rows))
        assert result.status == "warn"
        assert "id" in result.detail



class TestSystemReadFailure:
    def test_fetch_all_exception_is_fail(self):
        result = check_database_schema(
            introspect_func=_fetch_all_raises(RuntimeError("boom")),
        )
        assert result.status == "fail"
        assert result.label == "schéma iot_events"

    def test_fail_message_is_sober(self):
        result = check_database_schema(
            introspect_func=_fetch_all_raises(RuntimeError("boom")),
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
