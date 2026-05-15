from core.mail.config import MailConfig
from core.mail.log import MailLogRecord, MailLogger
from core.mail.exceptions import (
    MailConfigurationError,
    MailError,
    MailSendError,
    MailTemplateError,
    MailValidationError,
)
from core.mail.mailer import Mailer
from core.mail.message import MailMessage
from core.mail.smtp import SMTPMailer
from core.mail.templates import MailTemplateRenderer
from core.mail.transports import (
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
