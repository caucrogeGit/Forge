"""Tests du Mailer et de MailConfig — aucun envoi SMTP réel."""

from __future__ import annotations

import pytest

import core.forge as forge
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


@pytest.fixture()
def restore_forge():
    snapshot = dict(forge._cfg)
    yield
    forge._cfg.clear()
    forge._cfg.update(snapshot)


# ── MailConfig.from_forge ─────────────────────────────────────────────────────

def test_mail_config_lit_enabled(restore_forge):
    forge.configure(mail_enabled=True)
    assert MailConfig.from_forge().enabled is True


def test_mail_config_lit_enabled_false(restore_forge):
    forge.configure(mail_enabled=False)
    assert MailConfig.from_forge().enabled is False


def test_mail_config_lit_transport(restore_forge):
    forge.configure(mail_transport="console")
    assert MailConfig.from_forge().transport_name == "console"


def test_mail_config_transport_normalise_en_minuscules(restore_forge):
    forge.configure(mail_transport="SMTP")
    assert MailConfig.from_forge().transport_name == "smtp"


def test_mail_config_lit_from_email(restore_forge):
    forge.configure(mail_from="expediteur@example.test")
    assert MailConfig.from_forge().from_email == "expediteur@example.test"


def test_mail_config_transport_par_defaut_nest_pas_smtp():
    cfg = MailConfig.from_forge()
    assert cfg.transport_name != "smtp"


# ── MailConfig.build_transport ────────────────────────────────────────────────

def test_build_transport_null(restore_forge):
    forge.configure(mail_enabled=True, mail_transport="null")
    assert isinstance(MailConfig.from_forge().build_transport(), NullTransport)


def test_build_transport_fake(restore_forge):
    forge.configure(mail_enabled=True, mail_transport="fake")
    assert isinstance(MailConfig.from_forge().build_transport(), FakeTransport)


def test_build_transport_console(restore_forge):
    forge.configure(mail_enabled=True, mail_transport="console")
    assert isinstance(MailConfig.from_forge().build_transport(), ConsoleTransport)


def test_build_transport_log(restore_forge):
    forge.configure(mail_enabled=True, mail_transport="log")
    assert isinstance(MailConfig.from_forge().build_transport(), LogTransport)


def test_build_transport_smtp(restore_forge):
    forge.configure(mail_enabled=True, mail_transport="smtp")
    assert isinstance(MailConfig.from_forge().build_transport(), SmtpTransport)


def test_build_transport_log_transmet_log_dir(restore_forge, tmp_path):
    forge.configure(mail_enabled=True, mail_transport="log", mail_log_dir=str(tmp_path))
    transport = MailConfig.from_forge().build_transport()
    assert isinstance(transport, LogTransport)
    assert str(tmp_path) in str(transport.log_dir)


def test_build_transport_enabled_false_retourne_null_malgre_smtp(restore_forge):
    forge.configure(mail_enabled=False, mail_transport="smtp")
    assert isinstance(MailConfig.from_forge().build_transport(), NullTransport)


def test_build_transport_enabled_false_retourne_null_malgre_console(restore_forge):
    forge.configure(mail_enabled=False, mail_transport="console")
    assert isinstance(MailConfig.from_forge().build_transport(), NullTransport)


def test_build_transport_inconnu_leve_erreur(restore_forge):
    forge.configure(mail_enabled=True, mail_transport="pigeon")
    with pytest.raises(MailConfigurationError, match="pigeon"):
        MailConfig.from_forge().build_transport()


def test_build_transport_inconnu_liste_valeurs_valides(restore_forge):
    forge.configure(mail_enabled=True, mail_transport="telepathe")
    with pytest.raises(MailConfigurationError, match="smtp"):
        MailConfig.from_forge().build_transport()


# ── Mailer — construction ─────────────────────────────────────────────────────

def test_mailer_transport_accessible():
    t = FakeTransport()
    assert Mailer(t).transport is t


def test_mailer_from_config_retourne_mailer(restore_forge):
    forge.configure(mail_enabled=False)
    assert isinstance(Mailer.from_config(), Mailer)


def test_mailer_from_config_enabled_false_utilise_null(restore_forge):
    forge.configure(mail_enabled=False, mail_transport="smtp")
    assert isinstance(Mailer.from_config().transport, NullTransport)


def test_mailer_from_config_transport_par_defaut_nest_pas_smtp(restore_forge):
    forge.configure(mail_enabled=True)
    assert not isinstance(Mailer.from_config().transport, SmtpTransport)


def test_mailer_from_config_null(restore_forge):
    forge.configure(mail_enabled=True, mail_transport="null")
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
