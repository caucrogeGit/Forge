# pyright: strict
"""Mailer Forge — point d'entrée unique pour envoyer un mail."""
from __future__ import annotations

from datetime import datetime

from forge_mvc_mail.config import MailConfig
from forge_mvc_mail.exceptions import MailSendError
from core.database.timestamps import utc_now
from forge_mvc_mail.log import MailLogRecord, MailLogger
from forge_mvc_mail.message import MailMessage
from forge_mvc_mail.transports import BaseTransport, TransportResult


class Mailer:
    """Envoie un MailMessage via le transport configuré.

    Instanciation directe (tests) :
        mailer = Mailer(FakeTransport())

    Instanciation depuis la configuration Forge (production) :
        mailer = Mailer.from_config()

    MailSendError (échec SMTP transitoire) est intercepté et retourné comme
    TransportResult(success=False). MailConfigurationError (mauvaise config)
    se propage : c'est une erreur à corriger, pas à avaler.

    Journalisation (optionnelle, via MAIL_LOG_ENABLED) :
        mailer.send(msg, message_type="bienvenue", related_entity="contact", related_id=42)
    """

    def __init__(self, transport: BaseTransport) -> None:
        self._transport = transport

    @classmethod
    def from_config(cls) -> Mailer:
        return cls(MailConfig.from_env().build_transport())

    @property
    def transport(self) -> BaseTransport:
        return self._transport

    def send(
        self,
        message: MailMessage,
        *,
        message_type: str = "",
        related_entity: str = "",
        related_id: int | None = None,
    ) -> TransportResult:
        created_at = utc_now()
        try:
            result = self._transport.send(message)
        except MailSendError as exc:
            result = TransportResult(
                success=False,
                transport=self._transport.name,
                detail=str(exc),
            )

        _log_result(
            message=message,
            result=result,
            message_type=message_type,
            related_entity=related_entity,
            related_id=related_id,
            created_at=created_at,
        )
        return result


def _log_result(
    *,
    message: MailMessage,
    result: TransportResult,
    message_type: str,
    related_entity: str,
    related_id: int | None,
    created_at: datetime,
) -> None:
    if result.skipped:
        status = "skipped"
    elif result.success:
        status = "sent"
    else:
        status = "failed"

    to_email = ", ".join(message.to_addresses)[:255]
    sent_at = utc_now() if status == "sent" else None

    record = MailLogRecord(
        message_type=message_type,
        to_email=to_email,
        subject=message.subject,
        transport=result.transport,
        status=status,
        error_message=result.detail if status == "failed" else "",
        related_entity=related_entity,
        related_id=related_id,
        created_at=created_at,
        sent_at=sent_at,
    )
    MailLogger.log(record)
