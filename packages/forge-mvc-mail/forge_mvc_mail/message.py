# pyright: strict
"""Représentation d'un message mail — aucune dépendance SMTP."""

from __future__ import annotations

from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Iterable

from forge_mvc_mail.exceptions import MailValidationError


def _coupe_une_ligne(value: str) -> bool:
    """Vrai si `value` contient un séparateur de ligne, au sens de Python.

    `MAIL-SEPARATEURS-LIGNE-001` : le contrôle ne cherchait que `[\\r\\n]`, alors
    que Python coupe une ligne sur huit autres caractères, dont la tabulation
    verticale, le saut de page, la nouvelle ligne NEL et les deux séparateurs
    Unicode de ligne et de paragraphe. Mesuré, les huit passaient ce contrôle,
    puis `EmailMessage` levait un `ValueError` de la bibliothèque standard.

    Aucune en-tête forgée ne partait, la bibliothèque standard refusant ces
    valeurs. Mais l'appelant recevait une exception d'un autre type que le
    `MailValidationError` annoncé, donc une panne là où il attendait un refus.

    `splitlines()` plutôt qu'une liste écrite à la main : c'est la définition
    que la bibliothèque standard applique elle-même, et une liste en dériverait
    en silence à la première version de Python qui l'étendrait.

    La comparaison ne peut pas être `len(...) > 1` : un séparateur **final** ne
    crée pas de seconde ligne, si bien que « abc\\n » y passerait. C'est le même
    piège que l'ancrage `$` d'une expression rationnelle.
    """
    return bool(value) and value.splitlines() != [value]


def _check_no_injection(value: str, label: str) -> str:
    if _coupe_une_ligne(value):
        raise MailValidationError(
            f"{label} contient des caractères interdits (injection de headers)."
        )
    return value


def _normalize_addresses(
    value: str | Iterable[str] | None, field_name: str
) -> list[str]:
    if value is None:
        return []
    addresses = [value] if isinstance(value, str) else list(value)
    cleaned = [str(a).strip() for a in addresses if str(a).strip()]
    if not cleaned:
        raise MailValidationError(
            f"{field_name} doit contenir au moins une adresse valide."
        )
    return [_check_no_injection(a, field_name) for a in cleaned]


@dataclass
class MailMessage:
    subject: str
    to: str | Iterable[str]
    body_text: str | None = None
    body_html: str | None = None
    from_email: str | None = None
    cc: str | Iterable[str] | None = None
    bcc: str | Iterable[str] | None = None
    reply_to: str | Iterable[str] | None = None
    to_addresses: list[str] = field(init=False, repr=False)
    cc_addresses: list[str] = field(init=False, repr=False)
    bcc_addresses: list[str] = field(init=False, repr=False)
    reply_to_addresses: list[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        subject = str(self.subject).strip()
        if not subject:
            raise MailValidationError("subject ne peut pas être vide.")
        self.subject = _check_no_injection(subject, "subject")

        if self.body_text is None and self.body_html is None:
            raise MailValidationError("body_text ou body_html est obligatoire.")
        self.body_text = None if self.body_text is None else str(self.body_text)
        self.body_html = None if self.body_html is None else str(self.body_html)

        if self.from_email:
            self.from_email = _check_no_injection(
                self.from_email.strip(), "from_email"
            )
        else:
            self.from_email = None

        self.to_addresses = _normalize_addresses(self.to, "to")
        if not self.to_addresses:
            raise MailValidationError("to doit contenir au moins une adresse.")
        self.cc_addresses = _normalize_addresses(self.cc, "cc") if self.cc is not None else []
        self.bcc_addresses = _normalize_addresses(self.bcc, "bcc") if self.bcc is not None else []
        self.reply_to_addresses = _normalize_addresses(self.reply_to, "reply_to") if self.reply_to is not None else []

    @property
    def envelope_recipients(self) -> list[str]:
        """Destinataires SMTP réels : to + cc + bcc (bcc exclu des headers)."""
        return [*self.to_addresses, *self.cc_addresses, *self.bcc_addresses]

    def as_email_message(self, from_email: str) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = self.subject
        msg["From"] = from_email
        msg["To"] = ", ".join(self.to_addresses)
        if self.cc_addresses:
            msg["Cc"] = ", ".join(self.cc_addresses)
        if self.reply_to_addresses:
            msg["Reply-To"] = ", ".join(self.reply_to_addresses)

        if self.body_text is not None and self.body_html is not None:
            msg.set_content(self.body_text)
            msg.add_alternative(self.body_html, subtype="html")
        elif self.body_text is not None:
            msg.set_content(self.body_text)
        else:
            msg.set_content(self.body_html, subtype="html")

        return msg
