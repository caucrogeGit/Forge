"""Lecture de la configuration mail depuis le registre Forge."""

from __future__ import annotations

from dataclasses import dataclass

from core.forge import get as _cfg
from forge_mvc_mail.exceptions import MailConfigurationError
from forge_mvc_mail.transports import (
    BaseTransport,
    ConsoleTransport,
    FakeTransport,
    LogTransport,
    NullTransport,
    SmtpTransport,
)

_VALID_TRANSPORTS = frozenset({"null", "fake", "console", "log", "smtp"})


def _as_bool(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


@dataclass(frozen=True)
class MailConfig:
    """Configuration mail complète, lue depuis le registre Forge."""

    enabled: bool
    transport_name: str
    from_email: str
    log_dir: str
    host: str
    port: int
    username: str
    password: str
    use_tls: bool
    use_ssl: bool
    timeout: float

    @classmethod
    def from_forge(cls) -> MailConfig:
        return cls(
            enabled=_as_bool(_cfg("mail_enabled")),
            transport_name=str(_cfg("mail_transport") or "log").lower().strip(),
            from_email=str(_cfg("mail_from") or ""),
            log_dir=str(_cfg("mail_log_dir") or "storage/mail"),
            host=str(_cfg("mail_host") or ""),
            port=int(_cfg("mail_port") or 587),
            username=str(_cfg("mail_username") or ""),
            password=str(_cfg("mail_password") or ""),
            use_tls=_as_bool(_cfg("mail_use_tls")),
            use_ssl=_as_bool(_cfg("mail_use_ssl")),
            timeout=float(_cfg("mail_timeout") or 10),
        )

    def build_transport(self) -> BaseTransport:
        """Retourne le transport correspondant à la configuration.

        MAIL_ENABLED=false prend toujours le dessus : NullTransport est retourné
        quel que soit MAIL_TRANSPORT, garantissant zéro envoi accidentel.
        """
        if not self.enabled:
            return NullTransport()

        name = self.transport_name
        if name not in _VALID_TRANSPORTS:
            raise MailConfigurationError(
                f"Transport mail inconnu : {name!r}. "
                f"Valeurs valides : {', '.join(sorted(_VALID_TRANSPORTS))}."
            )

        if name == "null":
            return NullTransport()
        if name == "fake":
            return FakeTransport()
        if name == "console":
            return ConsoleTransport()
        if name == "log":
            return LogTransport(log_dir=self.log_dir)
        # smtp
        return SmtpTransport(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            from_email=self.from_email,
            use_tls=self.use_tls,
            use_ssl=self.use_ssl,
            timeout=self.timeout,
        )
