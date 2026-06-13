"""Tests du Mailer et de MailConfig — aucun envoi SMTP réel."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("forge_mvc_mail")
from forge_mvc_mail.config import MailConfig
from forge_mvc_mail.exceptions import MailConfigurationError, MailSendError
from forge_mvc_mail.mailer import Mailer
from forge_mvc_mail.message import MailMessage
from forge_mvc_mail.transports import (
    BaseTransport,
    ConsoleTransport,
    FakeTransport,
    LogTransport,
    NullTransport,
    SmtpTransport,
    TransportResult,
)


def _msg(subject: str = "Test", to: str = "dest@example.test", body_text: str = "x") -> MailMessage:
    return MailMessage(subject=subject, to=to, body_text=body_text)


@pytest.fixture(autouse=True)
def _clean_mail_env(monkeypatch):
    """Supprime toute variable MAIL_* du shell avant chaque test."""
    for key in list(os.environ):
        if key.startswith("MAIL_"):
            monkeypatch.delenv(key, raising=False)


# ── MailConfig.from_env ───────────────────────────────────────────────────────

def test_mail_config_lit_enabled(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "true")
    assert MailConfig.from_env().enabled is True


def test_mail_config_lit_enabled_false(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "false")
    assert MailConfig.from_env().enabled is False


def test_mail_config_lit_transport(monkeypatch):
    monkeypatch.setenv("MAIL_TRANSPORT", "console")
    assert MailConfig.from_env().transport_name == "console"


def test_mail_config_transport_normalise_en_minuscules(monkeypatch):
    monkeypatch.setenv("MAIL_TRANSPORT", "SMTP")
    assert MailConfig.from_env().transport_name == "smtp"


def test_mail_config_lit_from_email(monkeypatch):
    monkeypatch.setenv("MAIL_FROM", "expediteur@example.test")
    assert MailConfig.from_env().from_email == "expediteur@example.test"


def test_mail_config_transport_par_defaut_nest_pas_smtp():
    cfg = MailConfig.from_env()
    assert cfg.transport_name != "smtp"


# ── MailConfig.build_transport ────────────────────────────────────────────────

def test_build_transport_null(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "true")
    monkeypatch.setenv("MAIL_TRANSPORT", "null")
    assert isinstance(MailConfig.from_env().build_transport(), NullTransport)


def test_build_transport_fake(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "true")
    monkeypatch.setenv("MAIL_TRANSPORT", "fake")
    assert isinstance(MailConfig.from_env().build_transport(), FakeTransport)


def test_build_transport_console(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "true")
    monkeypatch.setenv("MAIL_TRANSPORT", "console")
    assert isinstance(MailConfig.from_env().build_transport(), ConsoleTransport)


def test_build_transport_log(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "true")
    monkeypatch.setenv("MAIL_TRANSPORT", "log")
    assert isinstance(MailConfig.from_env().build_transport(), LogTransport)


def test_build_transport_smtp(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "true")
    monkeypatch.setenv("MAIL_TRANSPORT", "smtp")
    assert isinstance(MailConfig.from_env().build_transport(), SmtpTransport)


def test_build_transport_log_transmet_log_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("MAIL_ENABLED", "true")
    monkeypatch.setenv("MAIL_TRANSPORT", "log")
    monkeypatch.setenv("MAIL_LOG_DIR", str(tmp_path))
    transport = MailConfig.from_env().build_transport()
    assert isinstance(transport, LogTransport)
    assert str(tmp_path) in str(transport.log_dir)


def test_build_transport_enabled_false_retourne_null_malgre_smtp(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "false")
    monkeypatch.setenv("MAIL_TRANSPORT", "smtp")
    assert isinstance(MailConfig.from_env().build_transport(), NullTransport)


def test_build_transport_enabled_false_retourne_null_malgre_console(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "false")
    monkeypatch.setenv("MAIL_TRANSPORT", "console")
    assert isinstance(MailConfig.from_env().build_transport(), NullTransport)


def test_build_transport_inconnu_leve_erreur(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "true")
    monkeypatch.setenv("MAIL_TRANSPORT", "pigeon")
    with pytest.raises(MailConfigurationError, match="pigeon"):
        MailConfig.from_env().build_transport()


def test_build_transport_inconnu_liste_valeurs_valides(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "true")
    monkeypatch.setenv("MAIL_TRANSPORT", "telepathe")
    with pytest.raises(MailConfigurationError, match="smtp"):
        MailConfig.from_env().build_transport()


# ── Mailer — construction ─────────────────────────────────────────────────────

def test_mailer_transport_accessible():
    t = FakeTransport()
    assert Mailer(t).transport is t


def test_mailer_from_config_retourne_mailer(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "false")
    assert isinstance(Mailer.from_config(), Mailer)


def test_mailer_from_config_enabled_false_utilise_null(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "false")
    monkeypatch.setenv("MAIL_TRANSPORT", "smtp")
    assert isinstance(Mailer.from_config().transport, NullTransport)


def test_mailer_from_config_transport_par_defaut_nest_pas_smtp(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "true")
    assert not isinstance(Mailer.from_config().transport, SmtpTransport)


def test_mailer_from_config_null(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "true")
    monkeypatch.setenv("MAIL_TRANSPORT", "null")
    assert isinstance(Mailer.from_config().transport, NullTransport)


# ── Mailer.send ───────────────────────────────────────────────────────────────

def test_mailer_send_retourne_transport_result():
    result = Mailer(NullTransport()).send(_msg())
    assert isinstance(result, TransportResult)


def test_mailer_send_null_retourne_skipped():
    result = Mailer(NullTransport()).send(_msg())
    assert result.success is True
    assert result.skipped is True


def test_mailer_send_fake_capture_message():
    t = FakeTransport()
    Mailer(t).send(_msg(subject="Bienvenue"))
    assert t.sent_count == 1
    assert t.messages[0].subject == "Bienvenue"


def test_mailer_send_fake_retourne_succes():
    result = Mailer(FakeTransport()).send(_msg())
    assert result.success is True
    assert result.skipped is False


def test_mailer_send_ne_modifie_pas_message():
    m = _msg(subject="Original")
    Mailer(FakeTransport()).send(m)
    assert m.subject == "Original"


def test_mailer_send_attrape_mail_send_error():
    class FailingTransport(BaseTransport):
        def send(self, message: MailMessage) -> TransportResult:
            raise MailSendError("serveur inaccessible")

    result = Mailer(FailingTransport()).send(_msg())
    assert result.success is False
    assert "serveur inaccessible" in result.detail
    assert result.transport == "FailingTransport"


def test_mailer_send_detail_vide_sur_succes():
    result = Mailer(FakeTransport()).send(_msg())
    assert result.detail == ""


def test_mailer_send_propage_mail_configuration_error():
    t = SmtpTransport(host="", from_email="")
    with pytest.raises(MailConfigurationError):
        Mailer(t).send(_msg())


def test_mailer_send_plusieurs_messages():
    t = FakeTransport()
    mailer = Mailer(t)
    mailer.send(_msg(subject="A"))
    mailer.send(_msg(subject="B"))
    mailer.send(_msg(subject="C"))
    assert t.sent_count == 3


# ── Import public depuis forge_mvc_mail ────────────────────────────────────────────

def test_import_public_mailer_et_mail_config():
    from forge_mvc_mail import MailConfig, Mailer  # noqa: F401 — test d'import
