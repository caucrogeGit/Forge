"""forge-mvc-mail — Envoi d'emails opt-in (extrait du core, ADR-022).

Composition de messages, transports interchangeables (console, SMTP, log…),
rendu de templates Jinja, journalisation, et CLI `mail:*`.
"""
from forge_mvc_mail.config import MailConfig
from forge_mvc_mail.log import MailLogRecord, MailLogger
from forge_mvc_mail.exceptions import (
    MailConfigurationError,
    MailError,
    MailSendError,
    MailTemplateError,
    MailValidationError,
)
from forge_mvc_mail.mailer import Mailer
from forge_mvc_mail.message import MailMessage
from forge_mvc_mail.smtp import SMTPMailer
from forge_mvc_mail.templates import MailTemplateRenderer
from forge_mvc_mail.transports import (
    BaseTransport,
    ConsoleTransport,
    FakeTransport,
    LogTransport,
    NullTransport,
    SmtpTransport,
    TransportResult,
)

__all__ = [
    "BaseTransport",
    "ConsoleTransport",
    "FakeTransport",
    "LogTransport",
    "MailConfig",
    "MailConfigurationError",
    "MailLogRecord",
    "MailLogger",
    "MailError",
    "MailMessage",
    "MailSendError",
    "MailTemplateError",
    "MailTemplateRenderer",
    "MailValidationError",
    "Mailer",
    "NullTransport",
    "SMTPMailer",
    "SmtpTransport",
    "TransportResult",
]

__version__ = "1.0.0b16"
