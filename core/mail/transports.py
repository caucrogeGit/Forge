"""Transports mail Forge — interface commune et cinq implémentations."""

from __future__ import annotations

import smtplib
import sys
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TextIO

from core.forge import get as _cfg
from core.mail.exceptions import MailConfigurationError, MailSendError
from core.mail.message import MailMessage


def _as_bool(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


@dataclass(frozen=True)
class TransportResult:
    """Résultat d'un envoi mail, qu'il ait eu lieu ou non."""
    success: bool
    transport: str
    skipped: bool = False
    detail: str = ""


class BaseTransport(ABC):
    """Interface commune pour tous les transports mail Forge."""

    @abstractmethod
    def send(self, message: MailMessage) -> TransportResult: ...

    @property
    def name(self) -> str:
        return type(self).__name__


# ── NullTransport ─────────────────────────────────────────────────────────────

class NullTransport(BaseTransport):
    """No-op : n'envoie rien, ne journalise rien. Utile pour désactiver le mail."""

    def send(self, message: MailMessage) -> TransportResult:
        return TransportResult(success=True, transport=self.name, skipped=True)


# ── FakeTransport ─────────────────────────────────────────────────────────────

class FakeTransport(BaseTransport):
    """Capture les messages en mémoire. Conçu pour les tests unitaires."""

    def __init__(self) -> None:
        self.messages: list[MailMessage] = []

    def send(self, message: MailMessage) -> TransportResult:
        self.messages.append(message)
        return TransportResult(success=True, transport=self.name)

    def reset(self) -> None:
        self.messages.clear()

    @property
    def sent_count(self) -> int:
        return len(self.messages)


# ── ConsoleTransport ──────────────────────────────────────────────────────────

class ConsoleTransport(BaseTransport):
    """Écrit une représentation lisible du mail dans un flux de sortie (stdout par défaut)."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream or sys.stdout

    def send(self, message: MailMessage) -> TransportResult:
        from_email = message.from_email or "noreply@localhost"
        sep = "─" * 64
        lines = [
            sep,
            f"[MAIL] {self.name}",
            f"From    : {from_email}",
            f"To      : {', '.join(message.to_addresses)}",
        ]
        if message.cc_addresses:
            lines.append(f"Cc      : {', '.join(message.cc_addresses)}")
        if message.bcc_addresses:
            lines.append(f"Bcc     : {', '.join(message.bcc_addresses)}")
        lines.append(f"Subject : {message.subject}")
        lines.append(sep)
        if message.body_text is not None:
            lines.append(message.body_text)
        else:
            lines.append(f"[HTML] {message.body_html}")
        lines.append(sep)
        print("\n".join(lines), file=self._stream)
        return TransportResult(success=True, transport=self.name)


# ── LogTransport ──────────────────────────────────────────────────────────────

class LogTransport(BaseTransport):
    """Écrit un fichier .eml dans storage/mail/ sans envoyer quoi que ce soit."""

    def __init__(self, log_dir: str | Path = "storage/mail") -> None:
        self.log_dir = Path(log_dir)

    def send(self, message: MailMessage) -> TransportResult:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        from_email = message.from_email or "noreply@localhost"
        email = message.as_email_message(from_email)
        uid = uuid.uuid4().hex[:8]
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uid}.eml"
        path = self.log_dir / filename
        path.write_bytes(bytes(email))
        return TransportResult(success=True, transport=self.name, detail=str(path))


# ── SmtpTransport ─────────────────────────────────────────────────────────────

@dataclass
class SmtpTransport(BaseTransport):
    """Envoi SMTP réel via smtplib. Ne pas utiliser par défaut en développement."""

    host: str = ""
    port: int = 587
    username: str = ""
    password: str = ""
    from_email: str = ""
    use_tls: bool = False
    use_ssl: bool = False
    timeout: float = 10.0

    @classmethod
    def from_config(cls) -> SmtpTransport:
        return cls(
            host=str(_cfg("mail_host") or ""),
            port=int(_cfg("mail_port") or 587),
            username=str(_cfg("mail_username") or ""),
            password=str(_cfg("mail_password") or ""),
            from_email=str(_cfg("mail_from") or ""),
            use_tls=_as_bool(_cfg("mail_use_tls")),
            use_ssl=_as_bool(_cfg("mail_use_ssl")),
            timeout=float(_cfg("mail_timeout") or 10),
        )

    def send(self, message: MailMessage) -> TransportResult:
        if not self.host:
            raise MailConfigurationError("MAIL_HOST est requis pour envoyer un email.")

        from_email = message.from_email or self.from_email
        if not from_email:
            raise MailConfigurationError(
                "MAIL_FROM est requis si le message ne définit pas from_email."
            )

        email = message.as_email_message(from_email)
        smtp_class = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP

        try:
            with smtp_class(self.host, self.port, timeout=self.timeout) as smtp:
                if self.use_tls and not self.use_ssl:
                    smtp.starttls()
                if self.username:
                    smtp.login(self.username, self.password)
                smtp.send_message(
                    email, from_addr=from_email, to_addrs=message.envelope_recipients
                )
        except (OSError, smtplib.SMTPException) as exc:
            raise MailSendError(f"Envoi SMTP impossible : {exc}") from exc

        return TransportResult(success=True, transport=self.name)
