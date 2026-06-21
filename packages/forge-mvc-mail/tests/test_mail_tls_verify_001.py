"""Garde-fou MAIL-TLS-CERT-VERIFY-001.

L'envoi SMTP doit vérifier le certificat du serveur par défaut (contexte TLS
avec `CERT_REQUIRED` + `check_hostname`), fermant le vecteur MITM. La
vérification ne peut être relâchée qu'explicitement via `MAIL_TLS_VERIFY=false`
(dev contre un serveur local auto-signé).
"""

from __future__ import annotations

import smtplib
import ssl

import pytest

pytest.importorskip("forge_mvc_mail")

from forge_mvc_mail.transports import SmtpTransport, build_smtp_tls_context


def test_contexte_par_defaut_verifie_le_certificat() -> None:
    context = build_smtp_tls_context(verify=True)
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True


def test_contexte_non_verifiant_si_demande() -> None:
    context = build_smtp_tls_context(verify=False)
    assert context.verify_mode == ssl.CERT_NONE
    assert context.check_hostname is False


def test_from_config_verifie_par_defaut(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MAIL_TLS_VERIFY", raising=False)
    assert SmtpTransport.from_config().verify_tls is True


@pytest.mark.parametrize(
    ("valeur", "attendu"),
    [("false", False), ("0", False), ("no", False), ("true", True), ("1", True)],
)
def test_from_config_respecte_mail_tls_verify(
    monkeypatch: pytest.MonkeyPatch, valeur: str, attendu: bool
) -> None:
    monkeypatch.setenv("MAIL_TLS_VERIFY", valeur)
    assert SmtpTransport.from_config().verify_tls is attendu


class _CapturingSMTP:
    """Double SMTP capturant le contexte TLS passé à starttls."""

    last: "_CapturingSMTP | None" = None

    def __init__(self, host: str, port: int, timeout: float | None = None, context: object = None) -> None:
        self.starttls_context: object = None
        type(self).last = self

    def __enter__(self) -> "_CapturingSMTP":
        return self

    def __exit__(self, *args: object) -> bool:
        return False

    def starttls(self, context: object = None) -> None:
        self.starttls_context = context

    def login(self, username: str, password: str) -> None: ...

    def send_message(self, message: object, *, from_addr: str | None = None, to_addrs: object = None) -> None: ...


def test_starttls_recoit_un_contexte_verifiant(monkeypatch: pytest.MonkeyPatch) -> None:
    from forge_mvc_mail.message import MailMessage

    monkeypatch.setattr(smtplib, "SMTP", _CapturingSMTP)
    transport = SmtpTransport(host="smtp.example.test", from_email="a@example.test", use_tls=True)
    transport.send(MailMessage(subject="x", to="b@example.test", body_text="y"))

    captured = _CapturingSMTP.last
    assert captured is not None
    assert isinstance(captured.starttls_context, ssl.SSLContext)
    assert captured.starttls_context.verify_mode == ssl.CERT_REQUIRED
