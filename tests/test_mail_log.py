"""Tests MAIL-006 — MailLogRecord, MailLogger, intégration Mailer."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

import core.forge as forge
pytest.importorskip("forge_mvc_mail")
from forge_mvc_mail.log import MailLogRecord, MailLogger
from forge_mvc_mail.mailer import Mailer
from forge_mvc_mail.message import MailMessage
from forge_mvc_mail.transports import FakeTransport, NullTransport


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def restore_forge():
    snapshot = dict(forge._cfg)
    yield
    forge._cfg.clear()
    forge._cfg.update(snapshot)


@pytest.fixture()
def log_enabled(restore_forge):
    forge.configure(mail_log_enabled=True)


@pytest.fixture()
def log_disabled(restore_forge):
    forge.configure(mail_log_enabled=False)


def _simple_message() -> MailMessage:
    return MailMessage(
        subject="Sujet test",
        to="dest@example.com",
        body_text="Corps test",
    )


# ── MailLogRecord ──────────────────────────────────────────────────────────────

def test_record_champs_obligatoires():
    r = MailLogRecord(
        message_type="bienvenue",
        to_email="a@b.com",
        subject="Bonjour",
        transport="fake",
        status="sent",
    )
    assert r.status == "sent"
    assert r.error_message == ""
    assert r.related_entity == ""
    assert r.related_id is None
    assert r.sent_at is None
    assert isinstance(r.created_at, datetime)


def test_record_created_at_utc_par_defaut():
    r = MailLogRecord(
        message_type="", to_email="x@y.com",
        subject="s", transport="t", status="sent",
    )
    assert r.created_at.tzinfo is not None


def test_record_tous_champs():
    now = datetime.now(timezone.utc)
    r = MailLogRecord(
        message_type="confirm",
        to_email="a@b.com",
        subject="Confirm",
        transport="smtp",
        status="failed",
        error_message="connexion refusée",
        related_entity="commande",
        related_id=42,
        created_at=now,
        sent_at=None,
    )
    assert r.related_id == 42
    assert r.error_message == "connexion refusée"


# ── MailLogger.is_enabled ──────────────────────────────────────────────────────

def test_is_enabled_true(log_enabled):
    assert MailLogger.is_enabled() is True


def test_is_enabled_false(log_disabled):
    assert MailLogger.is_enabled() is False


# ── MailLogger.log — disabled ──────────────────────────────────────────────────

def test_log_ne_fait_rien_si_disabled(log_disabled, monkeypatch):
    calls = []
    monkeypatch.setattr("forge_mvc_mail.log._db_insert", lambda sql, p: calls.append(p))
    record = MailLogRecord(
        message_type="", to_email="a@b.com",
        subject="s", transport="t", status="sent",
    )
    MailLogger.log(record)
    assert calls == []


# ── MailLogger.log — enabled ───────────────────────────────────────────────────

def test_log_appelle_insert_si_enabled(log_enabled, monkeypatch):
    calls = []
    monkeypatch.setattr("forge_mvc_mail.log._db_insert", lambda sql, p: calls.append(p))
    record = MailLogRecord(
        message_type="bienvenue",
        to_email="dest@example.com",
        subject="Bonjour",
        transport="fake",
        status="sent",
    )
    MailLogger.log(record)
    assert len(calls) == 1
    params = calls[0]
    assert params[0] == "bienvenue"       # message_type
    assert params[1] == "dest@example.com"  # to_email
    assert params[4] == "sent"             # status


def test_log_status_failed_inclut_erreur(log_enabled, monkeypatch):
    calls = []
    monkeypatch.setattr("forge_mvc_mail.log._db_insert", lambda sql, p: calls.append(p))
    record = MailLogRecord(
        message_type="",
        to_email="a@b.com",
        subject="s",
        transport="smtp",
        status="failed",
        error_message="SMTP timeout",
    )
    MailLogger.log(record)
    assert calls[0][5] == "SMTP timeout"   # error_message


def test_log_silencieux_si_db_leve_exception(log_enabled, monkeypatch):
    def _raise(sql, p):
        raise RuntimeError("DB indisponible")
    monkeypatch.setattr("forge_mvc_mail.log._db_insert", _raise)
    record = MailLogRecord(
        message_type="", to_email="a@b.com",
        subject="s", transport="t", status="sent",
    )
    MailLogger.log(record)  # ne doit pas lever


# ── MailLogger.fetch_recent ────────────────────────────────────────────────────

def test_fetch_recent_appelle_fetch_all(log_enabled, monkeypatch):
    fake_rows = [{"id": 1, "status": "sent"}]
    calls = []
    monkeypatch.setattr(
        "forge_mvc_mail.log._db_fetch_all",
        lambda sql, p: (calls.append(p), fake_rows)[1],
    )
    rows = MailLogger.fetch_recent(5)
    assert rows == fake_rows
    assert calls[0] == (5,)


def test_fetch_recent_limite_par_defaut(log_enabled, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "forge_mvc_mail.log._db_fetch_all",
        lambda sql, p: (calls.append(p), [])[1],
    )
    MailLogger.fetch_recent()
    assert calls[0] == (20,)


# ── Intégration Mailer ─────────────────────────────────────────────────────────

def test_mailer_log_status_sent(log_enabled, monkeypatch):
    calls = []
    monkeypatch.setattr("forge_mvc_mail.log._db_insert", lambda sql, p: calls.append(p))
    mailer = Mailer(FakeTransport())
    mailer.send(_simple_message())
    assert len(calls) == 1
    assert calls[0][4] == "sent"


def test_mailer_log_status_skipped(log_enabled, monkeypatch):
    calls = []
    monkeypatch.setattr("forge_mvc_mail.log._db_insert", lambda sql, p: calls.append(p))
    mailer = Mailer(NullTransport())
    mailer.send(_simple_message())
    assert calls[0][4] == "skipped"


def test_mailer_log_metadata_kwargs(log_enabled, monkeypatch):
    calls = []
    monkeypatch.setattr("forge_mvc_mail.log._db_insert", lambda sql, p: calls.append(p))
    mailer = Mailer(FakeTransport())
    mailer.send(
        _simple_message(),
        message_type="bienvenue",
        related_entity="contact",
        related_id=7,
    )
    params = calls[0]
    assert params[0] == "bienvenue"   # message_type
    assert params[6] == "contact"     # related_entity
    assert params[7] == 7             # related_id


def test_mailer_log_to_email_joint(log_enabled, monkeypatch):
    calls = []
    monkeypatch.setattr("forge_mvc_mail.log._db_insert", lambda sql, p: calls.append(p))
    msg = MailMessage(
        subject="Multi",
        to=["a@b.com", "c@d.com"],
        body_text="Corps",
    )
    Mailer(FakeTransport()).send(msg)
    assert "a@b.com" in calls[0][1]
    assert "c@d.com" in calls[0][1]


def test_mailer_log_sent_at_non_null_si_sent(log_enabled, monkeypatch):
    calls = []
    monkeypatch.setattr("forge_mvc_mail.log._db_insert", lambda sql, p: calls.append(p))
    Mailer(FakeTransport()).send(_simple_message())
    assert calls[0][9] is not None   # sent_at


def test_mailer_log_sent_at_null_si_skipped(log_enabled, monkeypatch):
    calls = []
    monkeypatch.setattr("forge_mvc_mail.log._db_insert", lambda sql, p: calls.append(p))
    Mailer(NullTransport()).send(_simple_message())
    assert calls[0][9] is None       # sent_at


def test_mailer_sans_log_si_disabled(log_disabled, monkeypatch):
    calls = []
    monkeypatch.setattr("forge_mvc_mail.log._db_insert", lambda sql, p: calls.append(p))
    Mailer(FakeTransport()).send(_simple_message())
    assert calls == []


def test_mailer_send_backwards_compatible(log_disabled):
    """send() sans kwargs fonctionne comme avant MAIL-006."""
    mailer = Mailer(FakeTransport())
    result = mailer.send(_simple_message())
    assert result.success is True


def test_mailer_log_status_failed_via_smtp_error(log_enabled, monkeypatch):
    """Mailer.send() intercepte MailSendError → status failed dans mail_log."""
    from forge_mvc_mail.exceptions import MailSendError
    from forge_mvc_mail.transports import BaseTransport, TransportResult

    class _FailingTransport(BaseTransport):
        def send(self, message: MailMessage) -> TransportResult:
            raise MailSendError("connexion SMTP refusée")

    calls = []
    monkeypatch.setattr("forge_mvc_mail.log._db_insert", lambda sql, p: calls.append(p))
    result = Mailer(_FailingTransport()).send(_simple_message())
    assert result.success is False
    assert len(calls) == 1
    assert calls[0][4] == "failed"
    assert "SMTP" in calls[0][5]          # error_message
    assert calls[0][9] is None            # sent_at


def test_mailer_log_skipped_quand_mail_enabled_false(restore_forge, monkeypatch):
    """MAIL_ENABLED=false + MAIL_LOG_ENABLED=true → status skipped dans mail_log."""
    forge.configure(
        mail_enabled=False,
        mail_log_enabled=True,
        mail_transport="fake",
        mail_from="from@x.test",
        mail_host="",
        mail_port=587,
        mail_username="",
        mail_password="",
        mail_use_tls=False,
        mail_use_ssl=False,
        mail_timeout=10,
    )
    calls = []
    monkeypatch.setattr("forge_mvc_mail.log._db_insert", lambda sql, p: calls.append(p))
    mailer = Mailer.from_config()           # doit renvoyer NullTransport
    result = mailer.send(_simple_message())
    assert result.skipped is True
    assert len(calls) == 1
    assert calls[0][4] == "skipped"        # status
    assert calls[0][9] is None             # sent_at


# ── CLI mail:logs ──────────────────────────────────────────────────────────────

@pytest.fixture()
def no_env(monkeypatch):
    monkeypatch.setattr("forge_mvc_mail.cli._load_env_and_configure_forge", lambda root: None)


def test_logs_affiche_warn_si_disabled(no_env, log_disabled, capsys):
    from forge_mvc_mail.cli import cmd_mail_logs
    cmd_mail_logs([], root=Path("/tmp"))
    out, _ = capsys.readouterr()
    assert "MAIL_LOG_ENABLED" in out


def test_logs_limite_par_defaut(no_env, log_enabled, monkeypatch, capsys):
    from forge_mvc_mail.cli import cmd_mail_logs
    calls = []
    monkeypatch.setattr(
        "forge_mvc_mail.log._db_fetch_all",
        lambda sql, p: (calls.append(p), [])[1],
    )
    cmd_mail_logs([], root=Path("/tmp"))
    assert calls[0] == (20,)


def test_logs_limite_custom(no_env, log_enabled, monkeypatch):
    from forge_mvc_mail.cli import cmd_mail_logs
    calls = []
    monkeypatch.setattr(
        "forge_mvc_mail.log._db_fetch_all",
        lambda sql, p: (calls.append(p), [])[1],
    )
    cmd_mail_logs(["--limit", "5"], root=Path("/tmp"))
    assert calls[0] == (5,)


def test_logs_affiche_tableau(no_env, log_enabled, monkeypatch, capsys):
    from forge_mvc_mail.cli import cmd_mail_logs
    fake_rows = [
        {
            "id": 1,
            "created_at": datetime(2026, 5, 1, 10, 0, 0),
            "status": "sent",
            "transport": "log",
            "to_email": "dest@example.com",
            "subject": "Test",
            "error_message": "",
        }
    ]
    monkeypatch.setattr("forge_mvc_mail.log._db_fetch_all", lambda sql, p: fake_rows)
    cmd_mail_logs([], root=Path("/tmp"))
    out, _ = capsys.readouterr()
    assert "dest@example.com" in out
    assert "sent" in out.lower() or "[OK]" in out


def test_logs_sans_valeur_limit_leve_system_exit(no_env, log_enabled):
    from forge_mvc_mail.cli import cmd_mail_logs
    with pytest.raises(SystemExit):
        cmd_mail_logs(["--limit"], root=Path("/tmp"))


def test_logs_limit_invalide_leve_system_exit(no_env, log_enabled):
    from forge_mvc_mail.cli import cmd_mail_logs
    with pytest.raises(SystemExit):
        cmd_mail_logs(["--limit", "abc"], root=Path("/tmp"))


# ── mail:init — crée mail_log.sql ─────────────────────────────────────────────

def test_init_cree_mail_log_sql(tmp_path):
    from forge_mvc_mail.cli import cmd_mail_init
    cmd_mail_init([], root=tmp_path)
    sql_file = tmp_path / "mvc" / "models" / "sql" / "mail_log.sql"
    assert sql_file.exists()
    content = sql_file.read_text(encoding="utf-8")
    assert "mail_log" in content
    assert "CREATE TABLE" in content


def test_init_ne_pas_ecraser_mail_log_sql(tmp_path, capsys):
    from forge_mvc_mail.cli import cmd_mail_init
    cmd_mail_init([], root=tmp_path)
    sql_file = tmp_path / "mvc" / "models" / "sql" / "mail_log.sql"
    sql_file.write_text("MODIFIÉ", encoding="utf-8")

    capsys.readouterr()
    cmd_mail_init([], root=tmp_path)
    out, _ = capsys.readouterr()
    assert "PRÉSERVÉ" in out
    assert sql_file.read_text(encoding="utf-8") == "MODIFIÉ"
