"""Lecture de la configuration mail depuis l'environnement.

ADR-031 : `forge-mvc-mail` possède sa configuration de bout en bout. Elle est
lue directement depuis l'environnement (`os.environ`, peuplé par le `config.py`
du projet via `load_dotenv`), sans passer par le registre du noyau `core.forge`.
Le core ne connaît plus le mail.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

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


def _env_bool(key: str, default: bool = False) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_from_email() -> str:
    """Expéditeur effectif : MAIL_FROM prioritaire, sinon MAIL_FROM_NAME + ADDRESS."""
    explicit = os.getenv("MAIL_FROM")
    if explicit:
        return explicit
    name = os.getenv("MAIL_FROM_NAME", "Forge")
    address = os.getenv("MAIL_FROM_ADDRESS", "noreply@localhost")
    return f"{name} <{address}>" if name else address


def mail_templates_dir() -> str:
    """Dossier des templates mail, lu depuis l'environnement."""
    return os.getenv("MAIL_TEMPLATES_DIR", "mvc/mail/templates")


def mail_log_enabled() -> bool:
    """Journalisation SQL des envois, lue depuis l'environnement."""
    return _env_bool("MAIL_LOG_ENABLED")


@dataclass(frozen=True)
class MailConfig:
    """Configuration mail complète, lue depuis l'environnement.

    `MAIL_ENABLED` absent vaut `False` : zéro envoi accidentel par défaut.
    """

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
    def from_env(cls) -> MailConfig:
        return cls(
            enabled=_env_bool("MAIL_ENABLED"),
            transport_name=(os.getenv("MAIL_TRANSPORT") or "log").lower().strip(),
            from_email=_resolve_from_email(),
            log_dir=os.getenv("MAIL_LOG_DIR", "storage/mail"),
            host=os.getenv("MAIL_HOST", ""),
            port=int(os.getenv("MAIL_PORT") or 587),
            username=os.getenv("MAIL_USERNAME", ""),
            password=os.getenv("MAIL_PASSWORD", ""),
            use_tls=_env_bool("MAIL_USE_TLS"),
            use_ssl=_env_bool("MAIL_USE_SSL"),
            timeout=float(os.getenv("MAIL_TIMEOUT") or 10),
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
