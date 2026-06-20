# pyright: strict
"""core/mail/smtp.py — SMTPMailer legacy (conservé pour compatibilité ascendante).

SMTPMailer est conservé provisoirement pour les projets et tests qui l'utilisent.
Le système recommandé depuis Forge 1.2 est Mailer + SmtpTransport :

    from forge_mvc_mail import Mailer, MailMessage
    result = Mailer.from_config().send(message)
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import smtplib

from forge_mvc_mail.exceptions import MailConfigurationError, MailSendError
from forge_mvc_mail.message import MailMessage
from forge_mvc_mail.transports import build_smtp_tls_context


def _as_bool(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


@dataclass
class SMTPMailer:
    host: str = ""
    port: int = 587
    username: str = ""
    password: str = ""
    from_email: str = ""
    use_tls: bool = False
    use_ssl: bool = False
    timeout: float = 10.0
    enabled: bool = True
    verify_tls: bool = True

    @classmethod
    def from_config(cls) -> "SMTPMailer":
        _verify_raw = os.getenv("MAIL_TLS_VERIFY")
        return cls(
            host=os.getenv("MAIL_HOST", ""),
            port=int(os.getenv("MAIL_PORT") or 587),
            username=os.getenv("MAIL_USERNAME", ""),
            password=os.getenv("MAIL_PASSWORD", ""),
            from_email=os.getenv("MAIL_FROM", ""),
            use_tls=_as_bool(os.getenv("MAIL_USE_TLS")),
            use_ssl=_as_bool(os.getenv("MAIL_USE_SSL")),
            timeout=float(os.getenv("MAIL_TIMEOUT") or 10),
            enabled=_as_bool(os.getenv("MAIL_ENABLED")),
            verify_tls=True if _verify_raw is None else _as_bool(_verify_raw),
        )

    def send(self, message: MailMessage) -> bool:
        if not self.enabled:
            raise MailConfigurationError("MAIL_ENABLED=false : l'envoi de mail est desactive.")

        if not self.host:
            raise MailConfigurationError("MAIL_HOST est requis pour envoyer un email.")

        from_email = message.from_email or self.from_email
        if not from_email:
            raise MailConfigurationError(
                "MAIL_FROM est requis si le message ne definit pas from_email."
            )

        email = message.as_email_message(from_email)
        recipients = message.envelope_recipients
        # Vérification de certificat activée par défaut (MAIL-TLS-CERT-VERIFY-001).
        context = build_smtp_tls_context(self.verify_tls)

        try:
            if self.use_ssl:
                connection = smtplib.SMTP_SSL(
                    self.host, self.port, timeout=self.timeout, context=context
                )
            else:
                connection = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            with connection as smtp:
                if self.use_tls and not self.use_ssl:
                    smtp.starttls(context=context)
                if self.username:
                    smtp.login(self.username, self.password)
                smtp.send_message(email, from_addr=from_email, to_addrs=recipients)
        except (OSError, smtplib.SMTPException) as exc:
            raise MailSendError(f"Envoi SMTP impossible : {exc}") from exc

        return True
