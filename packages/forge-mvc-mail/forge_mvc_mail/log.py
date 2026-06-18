# pyright: strict
"""core/mail/log.py — Journalisation des envois de mails."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

logger = logging.getLogger(__name__)

_STATUS = Literal["sent", "failed", "skipped"]

_INSERT_SQL = """
INSERT INTO mail_log
    (message_type, to_email, subject, transport, status,
     error_message, related_entity, related_id, created_at, sent_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

_SELECT_SQL = """
SELECT id, message_type, to_email, subject, transport, status,
       error_message, related_entity, related_id, created_at, sent_at
FROM mail_log
ORDER BY id DESC
LIMIT ?
"""


@dataclass
class MailLogRecord:
    """Un enregistrement de journal d'envoi — pas de body_text ni body_html."""
    message_type:   str
    to_email:       str
    subject:        str
    transport:      str
    status:         _STATUS
    error_message:  str = ""
    related_entity: str = ""
    related_id:     int | None = None
    created_at:     datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at:        datetime | None = None


# ── Points d'injection pour les tests ─────────────────────────────────────────

def _db_insert(sql: str, params: tuple[Any, ...]) -> None:
    from core.database.db import insert
    insert(sql, params)


def _db_fetch_all(sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
    from core.database.db import fetch_all
    return fetch_all(sql, params) or []


# ── MailLogger ─────────────────────────────────────────────────────────────────

class MailLogger:
    """Écrit dans mail_log si MAIL_LOG_ENABLED=true. Silencieux en cas d'erreur DB."""

    @staticmethod
    def is_enabled() -> bool:
        from forge_mvc_mail.config import mail_log_enabled
        return mail_log_enabled()

    @classmethod
    def log(cls, record: MailLogRecord) -> None:
        if not cls.is_enabled():
            return
        try:
            _db_insert(
                _INSERT_SQL,
                (
                    record.message_type,
                    record.to_email,
                    record.subject,
                    record.transport,
                    record.status,
                    record.error_message,
                    record.related_entity,
                    record.related_id,
                    record.created_at,
                    record.sent_at,
                ),
            )
        except Exception as exc:
            logger.warning("MailLogger: impossible d'écrire dans mail_log : %s", exc)

    @classmethod
    def fetch_recent(cls, limit: int = 20) -> list[dict[str, Any]]:
        return _db_fetch_all(_SELECT_SQL, (limit,))
