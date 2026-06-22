"""Tests du diagnostic ``forge iot:doctor`` — IOT-DOCTOR-001.

Diagnostic **statique** : aucun broker MQTT, aucune base de données.
Les tests vérifient chaque check unitairement, l'orchestration
(``run_all``, ``has_failures``, ``print_report``, ``main``), le
masquage du mot de passe et le branchement de la commande dans le
dispatcher Forge (``forge.py``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.cli.doctor import (
    CheckResult,
    check_config_loadable,
    check_http_api_registrable,
    check_migration_present,
    check_package_importable,
    has_failures,
    info_db_not_tested,
    info_mqtt_not_tested,
    main,
    print_report,
    run_all,
)

PROJECT_ROOT = Path(__file__).parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"
HELP_FILE = PROJECT_ROOT / "cli" / "help.py"
HELP_DISPATCH_FILE = PROJECT_ROOT / "cli" / "help_dispatch.py"


# ═══════════════════════════════════════════════════════════════════════════
# Checks unitaires
# ═══════════════════════════════════════════════════════════════════════════


class TestPackageCheck:
    def test_returns_ok_with_version(self):
        result = check_package_importable()
        assert result.status == "ok"
        assert "forge-mvc-iot" in result.label
        assert "version" in result.detail


class TestConfigCheck:
    def test_default_config_ok(self):
        result = check_config_loadable({})
        assert result.status == "ok"
        assert result.label == "configuration IoT"
        assert "chargée" in result.detail

    def test_default_config_lines_include_host_port_topic(self):
        result = check_config_loadable({})
        text = "\n".join(result.lines)
        assert "mqtt_host       : localhost" in text
        assert "mqtt_port       : 1883" in text
        assert "mqtt_topic      : forge/+/+/telemetry" in text
        assert "mqtt_client_id  : forge-iot" in text
        assert "mqtt_username   : (none)" in text
        assert "mqtt_password   : (none)" in text

    def test_password_masked_in_lines(self):
        result = check_config_loadable({
            "FORGE_IOT_MQTT_USERNAME": "forge",
            "FORGE_IOT_MQTT_PASSWORD": "s3cr3t",
        })
        text = "\n".join(result.lines)
        assert "s3cr3t" not in text, (
            "Le mot de passe ne doit jamais apparaître en clair dans "
            "le rapport du doctor"
        )
        assert "mqtt_password   : ***" in text
        # Le username peut figurer en clair, c'est volontaire.
        assert "mqtt_username   : forge" in text

    def test_invalid_config_returns_fail(self):
        # FORGE_IOT_MQTT_HOST vide est refusé par load_iot_config.
        result = check_config_loadable({"FORGE_IOT_MQTT_HOST": ""})
        assert result.status == "fail"
        assert "FORGE_IOT_MQTT_HOST" in result.detail


class TestMigrationCheck:
    def test_migration_present(self):
        result = check_migration_present()
        # En install éditable (cas du dépôt monorepo), la migration est
        # forcément trouvée.
        assert result.status == "ok", (
            f"Migration introuvable — détail : {result.detail}"
        )
        assert "create_iot_events.sql" in result.detail


class TestHttpApiCheck:
    def test_register_iot_routes_exposed(self):
        result = check_http_api_registrable()
        assert result.status == "ok"
        assert "register_iot_routes" in result.detail


class TestInfoChecks:
    def test_mqtt_info_is_skip(self):
        result = info_mqtt_not_tested()
        assert result.status == "skip"
        assert "non testé" in result.detail
        assert "--mqtt" in result.detail

    def test_db_info_is_skip(self):
        result = info_db_not_tested()
        assert result.status == "skip"
        assert "non testée" in result.detail
        assert "--db" in result.detail


# ═══════════════════════════════════════════════════════════════════════════
# Orchestration
# ═══════════════════════════════════════════════════════════════════════════


class TestRunAll:
    def test_run_all_returns_six_results(self):
        results = run_all()
        assert isinstance(results, list)
        assert len(results) == 6
        for r in results:
            assert isinstance(r, CheckResult)

    def test_run_all_includes_expected_labels(self):
        results = run_all()
        labels = {r.label for r in results}
        assert "package forge-mvc-iot" in labels
        assert "configuration IoT" in labels
        assert "migration iot_events" in labels
        assert "API HTTP IoT" in labels
        assert "broker MQTT" in labels
        assert "base iot_events" in labels


class TestHasFailures:
    def test_no_failures_when_only_ok_and_skip(self):
        results = [
            CheckResult(status="ok", label="a"),
            CheckResult(status="ok", label="b"),
            CheckResult(status="skip", label="c"),
        ]
        assert has_failures(results) is False

    def test_warn_does_not_count_as_failure(self):
        results = [
            CheckResult(status="ok", label="a"),
            CheckResult(status="warn", label="b"),
        ]
        assert has_failures(results) is False

    def test_fail_detected(self):
        results = [
            CheckResult(status="ok", label="a"),
            CheckResult(status="fail", label="b"),
        ]
        assert has_failures(results) is True


# ═══════════════════════════════════════════════════════════════════════════
# print_report et main
# ═══════════════════════════════════════════════════════════════════════════


class TestPrintReport:
    def test_report_includes_header_and_tags(self, capsys):
        results = run_all()
        print_report(results)
        out = capsys.readouterr().out
        assert "Forge IoT doctor" in out
        assert "[OK]" in out
        assert "[SKIP]" in out

    def test_report_summary_counts(self, capsys):
        results = [
            CheckResult(status="ok", label="a"),
            CheckResult(status="warn", label="b"),
            CheckResult(status="fail", label="c"),
            CheckResult(status="skip", label="d"),
        ]
        print_report(results)
        out = capsys.readouterr().out
        assert "1 avertissement(s)" in out
        assert "1 erreur(s)" in out
        assert "1 info(s)" in out

    def test_report_shows_multiline_lines(self, capsys):
        result = CheckResult(
            status="ok",
            label="configuration IoT",
            detail="chargée",
            lines=("mqtt_host       : localhost", "mqtt_port       : 1883"),
        )
        print_report([result])
        out = capsys.readouterr().out
        assert "mqtt_host       : localhost" in out
        assert "mqtt_port       : 1883" in out


class TestMainEntry:
    def test_main_returns_zero_in_normal_env(self, capsys):
        rc = main([])
        # Dans le dépôt monorepo en install éditable, tout doit passer.
        assert rc == 0
        out = capsys.readouterr().out
        assert "Forge IoT doctor" in out

    def test_main_accepts_no_args(self, capsys):
        rc = main(None)
        assert rc == 0
        capsys.readouterr()  # nettoyer la sortie

    def test_main_ignores_unknown_args(self, capsys):
        # Les flags reconnus (--db, --mqtt) sont testés dans leurs
        # fichiers dédiés. Ici on vérifie qu'un flag inconnu est
        # silencieusement ignoré et ne casse pas le diagnostic statique.
        rc = main(["--unknown-flag"])
        assert rc == 0
        capsys.readouterr()


# ═══════════════════════════════════════════════════════════════════════════
# Branchement CLI dans forge.py
# ═══════════════════════════════════════════════════════════════════════════


class TestForgePyDispatch:
    """La commande ``iot:doctor`` est branchée dans le dispatcher Forge."""

    def test_iot_doctor_dispatched_in_forge_py(self):
        text = FORGE_PY.read_text(encoding="utf-8")
        assert 'command == "iot:doctor"' in text, (
            "forge.py doit dispatcher la commande iot:doctor"
        )

    def test_dispatch_uses_lazy_import_with_graceful_fallback(self):
        text = FORGE_PY.read_text(encoding="utf-8")
        # On vérifie que le dispatch protège contre l'absence du module
        # opt-in : import dans un try/except ImportError.
        assert "forge_mvc_iot.cli.doctor" in text
        # Le import est lazy (dans la branche de dispatch, pas en tête
        # de fichier).
        assert "from forge_mvc_iot.cli.doctor import" not in text.split(
            "def main(", 1
        )[0], (
            "L'import doit être paresseux pour rester optionnel — "
            "Forge Core doit fonctionner sans forge-mvc-iot installé"
        )

    def test_help_text_lists_iot_doctor(self):
        text = HELP_FILE.read_text(encoding="utf-8")
        assert "iot:doctor" in text

    def test_help_dispatch_describes_iot_doctor(self):
        text = HELP_DISPATCH_FILE.read_text(encoding="utf-8")
        assert '"iot:doctor"' in text
        # Une aide riche aussi (HELP_TEXTS_RICH) pour --help.
        assert "forge iot:doctor" in text


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous périmètre
# ═══════════════════════════════════════════════════════════════════════════


class TestNoRealConnections:
    """Le doctor n'ouvre aucune connexion réseau ou base."""

    def test_doctor_does_not_import_paho_at_module_level(self):
        # Depuis IOT-DOCTOR-MQTT-001, doctor.py PEUT importer paho — mais
        # uniquement de façon paresseuse, dans le corps d'une fonction.
        # Aucun import paho ne doit apparaître au niveau module (avant la
        # première fonction), pour que `forge iot:doctor` sans --mqtt
        # n'importe jamais paho.
        from forge_mvc_iot.cli import doctor as doctor_module
        src = Path(doctor_module.__file__).read_text(encoding="utf-8")
        head = src.split("\ndef ", 1)[0]
        head_imports = [
            line for line in head.splitlines()
            if line.lstrip().startswith(("import ", "from "))
        ]
        offenders = [line for line in head_imports if "paho" in line.lower()]
        assert not offenders, (
            "paho doit être importé paresseusement (dans une fonction), "
            f"jamais au niveau module : {offenders}"
        )

    def test_doctor_does_not_import_subscriber(self):
        from forge_mvc_iot.cli import doctor as doctor_module
        src = Path(doctor_module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in src.splitlines()
            if line.lstrip().startswith(("import ", "from "))
        ]
        offenders = [
            line for line in import_lines
            if "mqtt.subscriber" in line
        ]
        assert not offenders, (
            f"doctor.py ne doit pas importer le subscriber : {offenders}"
        )
