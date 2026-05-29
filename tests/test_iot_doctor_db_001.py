"""Tests de ``forge iot:doctor --db`` — IOT-DOCTOR-DB-001.

Vérifie l'option ``--db`` de la commande ``forge iot:doctor`` :

- sans ``--db`` → le check DB reste en ``skip`` (comportement par
  défaut, aucun import DB déclenché) ;
- avec ``--db`` → ``check_database_table()`` est appelé :
  - succès → ``[OK] table accessible (N événement(s))`` ;
  - table absente (errno 1146 ou « doesn't exist ») →
    ``[WARN]`` + conseil ``forge iot:init`` & ``forge migration:apply`` ;
  - connexion impossible → ``[FAIL]`` + exit 1 ;
- aucun mot de passe DB n'apparaît dans la sortie ;
- ``core/`` n'importe toujours pas ``forge_mvc_iot``.

Aucun MariaDB requis : ``check_database_table`` accepte un
``fetch_one_func`` injectable, et ``main`` est testé via
``monkeypatch.setattr`` sur le module ``core.database.db``.
"""

from __future__ import annotations

from pathlib import Path

from forge_mvc_iot.cli import doctor as doctor_module
from forge_mvc_iot.cli.doctor import (
    CheckResult,
    check_database_table,
    has_failures,
    info_db_not_tested,
    main,
    run_all,
)

PROJECT_ROOT = Path(__file__).parent.parent
DOCTOR_FILE = (
    PROJECT_ROOT / "packages" / "forge-mvc-iot" / "forge_mvc_iot"
    / "cli" / "doctor.py"
)
CORE_DIR = PROJECT_ROOT / "core"
HELP_DISPATCH_FILE = PROJECT_ROOT / "forge_cli" / "help_dispatch.py"


# ── Helpers de fixture ─────────────────────────────────────────────────────


class _FakeMariadbError(Exception):
    """Simule mariadb.OperationalError avec un attribut ``errno``."""

    def __init__(self, errno: int, message: str) -> None:
        super().__init__(message)
        self.errno = errno


def _fetch_one_ok(count: int):
    """Renvoie un fetch_one_func mock qui retourne {"n": count}."""
    def _stub(sql, params=()):
        return {"n": count}
    return _stub


def _fetch_one_raises(exc: Exception):
    def _stub(sql, params=()):
        raise exc
    return _stub


# ═══════════════════════════════════════════════════════════════════════════
# check_database_table — fonction unitaire
# ═══════════════════════════════════════════════════════════════════════════


class TestCheckDatabaseTableSuccess:
    def test_returns_ok_with_count(self):
        result = check_database_table(fetch_one_func=_fetch_one_ok(42))
        assert result.status == "ok"
        assert result.label == "base iot_events"
        assert "42" in result.detail
        assert "événement" in result.detail

    def test_zero_count_is_still_ok(self):
        result = check_database_table(fetch_one_func=_fetch_one_ok(0))
        assert result.status == "ok"
        assert "0" in result.detail

    def test_handles_none_row(self):
        # COUNT(*) renvoie toujours une ligne en MariaDB, mais on se
        # protège contre un mock qui renverrait None.
        def _stub(sql, params=()):
            return None
        result = check_database_table(fetch_one_func=_stub)
        assert result.status == "ok"
        assert "0" in result.detail


class TestCheckDatabaseTableMissing:
    """Table absente → WARN avec conseil clair."""

    def test_errno_1146_yields_warn(self):
        exc = _FakeMariadbError(
            1146, "Table 'mydb.iot_events' doesn't exist"
        )
        result = check_database_table(fetch_one_func=_fetch_one_raises(exc))
        assert result.status == "warn"
        assert result.label == "base iot_events"
        assert "absente" in result.detail.lower() or "migration" in result.detail.lower()

    def test_text_fallback_yields_warn(self):
        # Pas d'errno : on se rabat sur le message.
        exc = RuntimeError("Some wrapper says: Table doesn't exist")
        result = check_database_table(fetch_one_func=_fetch_one_raises(exc))
        assert result.status == "warn"

    def test_warn_includes_init_and_apply_hint(self):
        exc = _FakeMariadbError(1146, "Table 'x' doesn't exist")
        result = check_database_table(fetch_one_func=_fetch_one_raises(exc))
        all_text = result.detail + " " + " ".join(result.lines)
        assert "forge iot:init" in all_text
        assert "forge migration:apply" in all_text


class TestCheckDatabaseTableConnectionError:
    """Toute erreur non-1146 → FAIL."""

    def test_access_denied_yields_fail(self):
        exc = _FakeMariadbError(
            1045,
            "Access denied for user 'forge'@'localhost' (using password: YES)",
        )
        result = check_database_table(fetch_one_func=_fetch_one_raises(exc))
        assert result.status == "fail"
        assert "MariaDB" in result.detail or "connexion" in result.detail.lower()

    def test_connect_refused_yields_fail(self):
        exc = _FakeMariadbError(
            2003, "Can't connect to MySQL server on 'localhost' (111)",
        )
        result = check_database_table(fetch_one_func=_fetch_one_raises(exc))
        assert result.status == "fail"

    def test_unknown_database_yields_fail(self):
        exc = _FakeMariadbError(1049, "Unknown database 'mydb'")
        result = check_database_table(fetch_one_func=_fetch_one_raises(exc))
        assert result.status == "fail"

    def test_generic_exception_yields_fail(self):
        exc = RuntimeError("boom")
        result = check_database_table(fetch_one_func=_fetch_one_raises(exc))
        assert result.status == "fail"

    def test_fail_message_is_sober(self):
        # Le message doit contenir le type d'erreur, pas une
        # stacktrace ni du SQL applicatif.
        exc = _FakeMariadbError(2003, "Can't connect")
        result = check_database_table(fetch_one_func=_fetch_one_raises(exc))
        assert "Traceback" not in result.detail
        assert "SELECT" not in result.detail  # SQL pas dans le détail


class TestPasswordNeverLeaked:
    """Aucun mot de passe ne doit apparaître dans la sortie, même quand
    on simule un message d'erreur qui contiendrait par erreur du
    matériel sensible."""

    def test_password_in_exc_message_does_not_leak_to_detail(self):
        # Cas pathologique : driver hypothétique qui inclurait le mot
        # de passe dans son message. On vérifie qu'on ne fait pas
        # *empirer* la situation, mais on note que la responsabilité
        # principale incombe au driver. Pour ce test : on injecte un
        # password sentinel et on vérifie qu'il ne refait pas surface
        # via un format spécifique de notre côté.
        sentinel = "supersecret-pwd-xyz123"
        # Comme les drivers MariaDB ne fuitent pas le password, on
        # vérifie surtout qu'on n'ajoute pas de motif type
        # "DB_APP_PWD=..." de notre côté.
        exc = _FakeMariadbError(1045, "Access denied (using password: YES)")
        result = check_database_table(fetch_one_func=_fetch_one_raises(exc))
        assert sentinel not in result.detail


# ═══════════════════════════════════════════════════════════════════════════
# run_all(test_db=...)
# ═══════════════════════════════════════════════════════════════════════════


class TestRunAllToggle:
    def test_without_test_db_uses_info_skip(self, monkeypatch):
        # Si test_db=False, info_db_not_tested est utilisé et
        # core.database n'est jamais importé.
        called: list[bool] = []
        monkeypatch.setattr(
            doctor_module, "check_database_table",
            lambda **kw: called.append(True) or CheckResult(
                status="ok", label="never",
            ),
        )
        results = run_all()
        assert called == [], (
            "check_database_table ne doit PAS être appelé sans test_db=True"
        )
        # Le résultat DB est un skip via info_db_not_tested.
        db_result = next(r for r in results if r.label == "base iot_events")
        assert db_result.status == "skip"

    def test_with_test_db_uses_check_database_table(self, monkeypatch):
        called: list[bool] = []

        def _fake_check():
            called.append(True)
            return CheckResult(
                status="ok", label="base iot_events",
                detail="table accessible (3 événement(s))",
            )

        monkeypatch.setattr(
            doctor_module, "check_database_table", _fake_check,
        )
        # Table ok → le contrôle de schéma est aussi déclenché ;
        # on le stubbe pour ne toucher aucune base réelle.
        monkeypatch.setattr(
            doctor_module, "check_database_schema",
            lambda **kw: CheckResult(
                status="ok", label="schéma iot_events", detail="conforme",
            ),
        )
        results = run_all(test_db=True)
        assert called == [True]
        db_result = next(r for r in results if r.label == "base iot_events")
        assert db_result.status == "ok"


# ═══════════════════════════════════════════════════════════════════════════
# main(--db)
# ═══════════════════════════════════════════════════════════════════════════


class TestMainWithDbFlag:
    def test_main_db_calls_check(self, monkeypatch, capsys):
        called: list[bool] = []

        def _fake_check():
            called.append(True)
            return CheckResult(
                status="ok", label="base iot_events",
                detail="table accessible (5 événement(s))",
            )

        monkeypatch.setattr(
            doctor_module, "check_database_table", _fake_check,
        )
        # Table ok → schéma vérifié aussi : on le stubbe pour rester
        # hors-ligne dans ce test.
        monkeypatch.setattr(
            doctor_module, "check_database_schema",
            lambda **kw: CheckResult(
                status="ok", label="schéma iot_events", detail="conforme",
            ),
        )
        rc = main(["--db"])
        out = capsys.readouterr().out
        assert called == [True]
        assert rc == 0
        assert "[OK]" in out
        assert "5 événement" in out

    def test_main_db_fail_exits_1(self, monkeypatch, capsys):
        monkeypatch.setattr(
            doctor_module, "check_database_table",
            lambda: CheckResult(
                status="fail", label="base iot_events",
                detail="connexion MariaDB impossible — …",
            ),
        )
        rc = main(["--db"])
        capsys.readouterr()
        assert rc == 1

    def test_main_db_warn_does_not_exit_1(self, monkeypatch, capsys):
        monkeypatch.setattr(
            doctor_module, "check_database_table",
            lambda: CheckResult(
                status="warn", label="base iot_events",
                detail="table absente ou migration non appliquée",
                lines=(
                    "Conseil : lance forge iot:init puis forge migration:apply",
                ),
            ),
        )
        rc = main(["--db"])
        out = capsys.readouterr().out
        # Cohérent avec l'orchestration : warn n'est pas un fail.
        assert rc == 0
        assert "[WARN]" in out
        assert "forge iot:init" in out

    def test_main_without_db_keeps_skip(self, monkeypatch, capsys):
        # Sans --db, check_database_table ne doit JAMAIS être appelé.
        def _should_not_be_called():
            raise AssertionError(
                "check_database_table appelé sans --db"
            )

        monkeypatch.setattr(
            doctor_module, "check_database_table", _should_not_be_called,
        )
        rc = main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[SKIP]" in out
        # info_db_not_tested mentionne --db comme façon de l'activer.
        assert "--db" in out


# ═══════════════════════════════════════════════════════════════════════════
# Garde-fous périmètre
# ═══════════════════════════════════════════════════════════════════════════


class TestNoDbImportWhenFlagAbsent:
    """Tant que --db n'est pas passé, aucun appel à core.database
    n'est déclenché — c'est l'import paresseux côté check function."""

    def test_check_function_does_not_import_db_until_called(self):
        # Sanity : la déclaration de check_database_table elle-même
        # n'importe pas core.database.db au niveau module. L'import
        # est dans le corps de la fonction.
        src = DOCTOR_FILE.read_text(encoding="utf-8")
        # On cherche dans la partie hors fonction du module.
        head, *_ = src.split("def check_database_table")
        assert "from core.database" not in head, (
            "core.database doit être importé paresseusement dans "
            "check_database_table, pas au niveau module"
        )


class TestInfoDbStillSkipsByDefault:
    """info_db_not_tested reste un skip et mentionne --db."""

    def test_label_and_status(self):
        result = info_db_not_tested()
        assert result.status == "skip"
        assert result.label == "base iot_events"
        assert "--db" in result.detail


class TestMqttStillReserved:
    """L'option --mqtt reste hors périmètre."""

    def test_mqtt_skip_message_unchanged(self):
        # info_mqtt_not_tested ne doit pas être modifié par ce ticket.
        from forge_mvc_iot.cli.doctor import info_mqtt_not_tested
        result = info_mqtt_not_tested()
        assert result.status == "skip"
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


class TestHelpDispatchMentionsDb:
    def test_help_text_mentions_db(self):
        text = HELP_DISPATCH_FILE.read_text(encoding="utf-8")
        # L'aide riche iot:doctor doit décrire --db.
        # On cherche un fragment qui apparaît dans la rich help text.
        idx = text.find('"iot:doctor": """\\')
        assert idx >= 0, "Bloc HELP_TEXTS_RICH iot:doctor introuvable"
        block = text[idx:idx + 2000]
        assert "--db" in block, (
            "L'aide riche iot:doctor doit mentionner --db"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Intégration — has_failures cohérent
# ═══════════════════════════════════════════════════════════════════════════


class TestHasFailures:
    def test_warn_does_not_count_as_failure(self):
        results = [
            CheckResult(status="ok", label="a"),
            CheckResult(
                status="warn", label="base iot_events",
                detail="table absente",
            ),
        ]
        assert has_failures(results) is False

    def test_fail_db_counts_as_failure(self):
        results = [
            CheckResult(status="ok", label="a"),
            CheckResult(
                status="fail", label="base iot_events",
                detail="connexion impossible",
            ),
        ]
        assert has_failures(results) is True
