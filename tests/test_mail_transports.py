"""Tests des transports mail Forge — aucun envoi SMTP réel."""

from __future__ import annotations

import io
import os
import smtplib

import pytest

pytest.importorskip("forge_mvc_mail")
from forge_mvc_mail.exceptions import MailConfigurationError, MailSendError
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


def _msg(
    subject: str = "Test",
    to: str = "dest@example.test",
    body_text: str = "Bonjour",
    **kwargs,
) -> MailMessage:
    return MailMessage(subject=subject, to=to, body_text=body_text, **kwargs)


# ── TransportResult ───────────────────────────────────────────────────────────

def test_transport_result_succes_par_defaut():
    r = TransportResult(success=True, transport="T")
    assert r.success is True
    assert r.skipped is False
    assert r.detail == ""


def test_transport_result_skipped():
    r = TransportResult(success=True, transport="T", skipped=True)
    assert r.skipped is True


def test_transport_result_est_immutable():
    r = TransportResult(success=True, transport="T")
    with pytest.raises(AttributeError):
        r.success = False  # type: ignore[misc]


def test_transport_result_detail():
    r = TransportResult(success=True, transport="T", detail="/some/path")
    assert r.detail == "/some/path"


# ── BaseTransport ─────────────────────────────────────────────────────────────

def test_base_transport_est_abstrait():
    with pytest.raises(TypeError):
        BaseTransport()  # type: ignore[abstract]


def test_transport_name_retourne_nom_classe():
    assert NullTransport().name == "NullTransport"
    assert FakeTransport().name == "FakeTransport"
    assert ConsoleTransport(stream=io.StringIO()).name == "ConsoleTransport"


# ── NullTransport ─────────────────────────────────────────────────────────────

def test_null_retourne_succes():
    r = NullTransport().send(_msg())
    assert r.success is True


def test_null_est_skipped():
    r = NullTransport().send(_msg())
    assert r.skipped is True


def test_null_ne_modifie_pas_message():
    m = _msg()
    NullTransport().send(m)
    assert m.subject == "Test"
    assert m.body_text == "Bonjour"


def test_null_transport_dans_transport_result():
    r = NullTransport().send(_msg())
    assert r.transport == "NullTransport"


# ── FakeTransport ─────────────────────────────────────────────────────────────

def test_fake_capture_message():
    t = FakeTransport()
    m = _msg()
    t.send(m)
    assert t.messages[0] is m


def test_fake_sent_count():
    t = FakeTransport()
    t.send(_msg(subject="A"))
    t.send(_msg(subject="B"))
    assert t.sent_count == 2


def test_fake_reset_vide_la_liste():
    t = FakeTransport()
    t.send(_msg())
    t.reset()
    assert t.sent_count == 0
    assert t.messages == []


def test_fake_retourne_succes_non_skipped():
    r = FakeTransport().send(_msg())
    assert r.success is True
    assert r.skipped is False


def test_fake_ne_modifie_pas_message():
    m = _msg(subject="Original")
    FakeTransport().send(m)
    assert m.subject == "Original"


def test_fake_preserve_les_champs_message():
    m = MailMessage(
        subject="Facture",
        to=["a@x.test", "b@x.test"],
        cc="c@x.test",
        body_text="Corps",
        body_html="<p>Corps</p>",
    )
    t = FakeTransport()
    t.send(m)
    captured = t.messages[0]
    assert captured.subject == "Facture"
    assert captured.to_addresses == ["a@x.test", "b@x.test"]
    assert captured.cc_addresses == ["c@x.test"]
    assert captured.body_html == "<p>Corps</p>"


# ── ConsoleTransport ──────────────────────────────────────────────────────────

def test_console_ecrit_dans_stream():
    stream = io.StringIO()
    ConsoleTransport(stream=stream).send(_msg())
    assert stream.getvalue()


def test_console_contient_subject():
    stream = io.StringIO()
    ConsoleTransport(stream=stream).send(_msg(subject="Bienvenue"))
    assert "Bienvenue" in stream.getvalue()


def test_console_contient_to():
    stream = io.StringIO()
    ConsoleTransport(stream=stream).send(_msg(to="alice@x.test"))
    assert "alice@x.test" in stream.getvalue()


def test_console_contient_body_text():
    stream = io.StringIO()
    ConsoleTransport(stream=stream).send(_msg(body_text="Corps du message"))
    assert "Corps du message" in stream.getvalue()


def test_console_html_seul_affiche_html():
    stream = io.StringIO()
    ConsoleTransport(stream=stream).send(
        MailMessage(subject="T", to="a@x.test", body_html="<p>Hello</p>")
    )
    assert "<p>Hello</p>" in stream.getvalue()


def test_console_contient_cc_si_present():
    stream = io.StringIO()
    ConsoleTransport(stream=stream).send(
        MailMessage(subject="T", to="a@x.test", cc="b@x.test", body_text="x")
    )
    assert "b@x.test" in stream.getvalue()


def test_console_from_email_fallback_noreply():
    stream = io.StringIO()
    ConsoleTransport(stream=stream).send(_msg())
    assert "noreply@localhost" in stream.getvalue()


def test_console_from_email_depuis_message():
    stream = io.StringIO()
    ConsoleTransport(stream=stream).send(
        MailMessage(subject="T", to="a@x.test", body_text="x", from_email="exp@x.test")
    )
    assert "exp@x.test" in stream.getvalue()


def test_console_retourne_succes_non_skipped():
    r = ConsoleTransport(stream=io.StringIO()).send(_msg())
    assert r.success is True
    assert r.skipped is False


# ── LogTransport ──────────────────────────────────────────────────────────────

def test_log_cree_dossier_si_absent(tmp_path):
    log_dir = tmp_path / "mail_log"
    assert not log_dir.exists()
    LogTransport(log_dir=log_dir).send(_msg())
    assert log_dir.is_dir()


def test_log_cree_sous_dossiers_imbriques(tmp_path):
    log_dir = tmp_path / "a" / "b" / "mail"
    LogTransport(log_dir=log_dir).send(_msg())
    assert log_dir.is_dir()


def test_log_cree_fichier_eml(tmp_path):
    LogTransport(log_dir=tmp_path).send(_msg())
    assert len(list(tmp_path.glob("*.eml"))) == 1


def test_log_fichier_contient_subject(tmp_path):
    LogTransport(log_dir=tmp_path).send(_msg(subject="Confirmation"))
    eml = list(tmp_path.glob("*.eml"))[0].read_text()
    assert "Confirmation" in eml


def test_log_fichier_contient_destinataire(tmp_path):
    LogTransport(log_dir=tmp_path).send(_msg(to="dest@example.test"))
    eml = list(tmp_path.glob("*.eml"))[0].read_text()
    assert "dest@example.test" in eml


def test_log_fichier_contient_body(tmp_path):
    LogTransport(log_dir=tmp_path).send(_msg(body_text="Texte important"))
    eml = list(tmp_path.glob("*.eml"))[0].read_text()
    assert "Texte important" in eml


def test_log_retourne_succes(tmp_path):
    r = LogTransport(log_dir=tmp_path).send(_msg())
    assert r.success is True
    assert r.skipped is False


def test_log_detail_contient_chemin(tmp_path):
    r = LogTransport(log_dir=tmp_path).send(_msg())
    assert str(tmp_path) in r.detail
    assert r.detail.endswith(".eml")


def test_log_deux_envois_deux_fichiers(tmp_path):
    t = LogTransport(log_dir=tmp_path)
    t.send(_msg(subject="A"))
    t.send(_msg(subject="B"))
    assert len(list(tmp_path.glob("*.eml"))) == 2


def test_log_idempotent_dossier_existant(tmp_path):
    log_dir = tmp_path / "mail"
    log_dir.mkdir()
    LogTransport(log_dir=log_dir).send(_msg())
    assert log_dir.is_dir()


# ── SmtpTransport ─────────────────────────────────────────────────────────────

class FakeSMTP:
    instances: list[FakeSMTP] = []

    def __init__(self, host: str, port: int, timeout: float | None = None) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.login_args: tuple | None = None
        self.sent: list[tuple] = []
        type(self).instances.append(self)

    def __enter__(self) -> FakeSMTP:
        return self

    def __exit__(self, *args: object) -> bool:
        return False

    def starttls(self) -> None:
        self.started_tls = True

    def login(self, username: str, password: str) -> None:
        self.login_args = (username, password)

    def send_message(self, message: object, *, from_addr: str | None = None, to_addrs: list | None = None) -> None:
        self.sent.append((message, from_addr, list(to_addrs or [])))


class FailingSMTP(FakeSMTP):
    def send_message(self, message: object, *, from_addr: str | None = None, to_addrs: list | None = None) -> None:
        raise smtplib.SMTPException("boom")


@pytest.fixture(autouse=True)
def _clean_mail_env(monkeypatch):
    """Supprime toute variable MAIL_* du shell avant chaque test."""
    for key in list(os.environ):
        if key.startswith("MAIL_"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture()
def smtp_config(monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setenv("MAIL_HOST", "smtp.example.test")
    monkeypatch.setenv("MAIL_PORT", "2525")
    monkeypatch.setenv("MAIL_USERNAME", "")
    monkeypatch.setenv("MAIL_PASSWORD", "")
    monkeypatch.setenv("MAIL_FROM", "default@example.test")
    monkeypatch.setenv("MAIL_USE_TLS", "false")
    monkeypatch.setenv("MAIL_USE_SSL", "false")
    monkeypatch.setenv("MAIL_TIMEOUT", "3")
    yield


def test_smtp_envoie_message(smtp_config):
    SmtpTransport.from_config().send(_msg())
    assert len(FakeSMTP.instances[0].sent) == 1


def test_smtp_retourne_transport_result(smtp_config):
    r = SmtpTransport.from_config().send(_msg())
    assert isinstance(r, TransportResult)
    assert r.success is True
    assert r.transport == "SmtpTransport"
    assert r.skipped is False


def test_smtp_from_email_depuis_message(smtp_config):
    SmtpTransport.from_config().send(
        MailMessage(subject="T", to="a@x.test", body_text="x", from_email="exp@x.test")
    )
    _, from_addr, _ = FakeSMTP.instances[0].sent[0]
    assert from_addr == "exp@x.test"


def test_smtp_from_email_depuis_config(smtp_config):
    SmtpTransport.from_config().send(_msg())
    _, from_addr, _ = FakeSMTP.instances[0].sent[0]
    assert from_addr == "default@example.test"


def test_smtp_leve_erreur_si_host_absent():
    t = SmtpTransport(host="", from_email="x@x.test")
    with pytest.raises(MailConfigurationError, match="MAIL_HOST"):
        t.send(_msg())


def test_smtp_leve_erreur_si_from_email_absent():
    t = SmtpTransport(host="smtp.test", from_email="")
    with pytest.raises(MailConfigurationError, match="MAIL_FROM"):
        t.send(_msg())


def test_smtp_erreur_smtplib_devient_mail_send_error(monkeypatch, smtp_config):
    monkeypatch.setattr(smtplib, "SMTP", FailingSMTP)
    with pytest.raises(MailSendError, match="Envoi SMTP impossible"):
        SmtpTransport.from_config().send(_msg())


def test_smtp_starttls_si_use_tls(smtp_config, monkeypatch):
    monkeypatch.setenv("MAIL_USE_TLS", "true")
    SmtpTransport.from_config().send(_msg())
    assert FakeSMTP.instances[0].started_tls is True


def test_smtp_ssl_utilise_smtp_ssl(monkeypatch, smtp_config):
    class PlainSMTP(FakeSMTP):
        instances: list = []
    class SecureSMTP(FakeSMTP):
        instances: list = []
    monkeypatch.setattr(smtplib, "SMTP", PlainSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", SecureSMTP)
    monkeypatch.setenv("MAIL_USE_SSL", "true")
    SmtpTransport.from_config().send(_msg())
    assert len(PlainSMTP.instances) == 0
    assert len(SecureSMTP.instances) == 1


def test_smtp_login_si_username(smtp_config, monkeypatch):
    monkeypatch.setenv("MAIL_USERNAME", "roger")
    monkeypatch.setenv("MAIL_PASSWORD", "secret")
    SmtpTransport.from_config().send(_msg())
    assert FakeSMTP.instances[0].login_args == ("roger", "secret")


def test_smtp_envelope_recipients_to_cc_bcc(smtp_config):
    SmtpTransport.from_config().send(
        MailMessage(subject="T", to="a@x.test", cc="b@x.test", bcc="c@x.test", body_text="x")
    )
    _, _, recipients = FakeSMTP.instances[0].sent[0]
    assert "a@x.test" in recipients
    assert "b@x.test" in recipients
    assert "c@x.test" in recipients


def test_smtp_bcc_absent_des_headers(smtp_config):
    SmtpTransport.from_config().send(
        MailMessage(subject="T", to="a@x.test", bcc="hidden@x.test", body_text="x")
    )
    sent_msg, _, _ = FakeSMTP.instances[0].sent[0]
    assert "Bcc" not in sent_msg


def test_smtp_host_port_passes_a_smtplib(smtp_config):
    SmtpTransport.from_config().send(_msg())
    smtp = FakeSMTP.instances[0]
    assert smtp.host == "smtp.example.test"
    assert smtp.port == 2525
