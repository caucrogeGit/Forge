"""Journalisation Auth/User generique — contrat et emission.

Ce module fournit deux briques :

- Contrat AuthAuditEvent : structure validee, 20+ types d'evenements normalises.
- Emission Python : safe_log_auth_event() emet vers le logger forge.auth.audit.
  Le handler (et donc le destinataire) est configure par l'application.

Ce module ne fait aucun acces base de donnees. La persistance des audits
est une decision applicative — voir docs/adr/008-auth-audit-architecture.md
pour les approches typiques (handler logging SQL, wrapper applicatif, stream externe).

La table SQL auth_audit_log (mvc/models/sql/auth_audit_log.sql) est
fournie comme infrastructure latente. Forge n'y ecrit pas par defaut.
"""

from __future__ import annotations

import logging as _logging
import threading as _threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.auth.exceptions import InvalidAuthAuditEventError

_audit_logger = _logging.getLogger("forge.auth.audit")

_audit_failure_count: int = 0
_audit_failure_lock = _threading.RLock()


AUTH_EVENT_LOGIN_SUCCESS = "login.success"
AUTH_EVENT_LOGIN_FAILED = "login.failed"
AUTH_EVENT_LOGOUT = "logout"
AUTH_EVENT_PASSWORD_RESET_REQUESTED = "password_reset.requested"
AUTH_EVENT_PASSWORD_RESET_COMPLETED = "password_reset.completed"
AUTH_EVENT_EMAIL_VERIFIED = "email.verified"
AUTH_EVENT_MFA_REQUIRED = "mfa.challenge.required"
AUTH_EVENT_MFA_CHALLENGE_SUCCESS = "mfa.challenge.success"
AUTH_EVENT_MFA_CHALLENGE_FAILED = "mfa.challenge.failed"
AUTH_EVENT_MFA_REVALIDATION_SUCCESS = "mfa.revalidation.success"
AUTH_EVENT_MFA_REVALIDATION_FAILED = "mfa.revalidation.failed"
AUTH_EVENT_MFA_RATE_LIMITED = "mfa.rate_limited"
AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH = "mfa.revalidation.identity_mismatch"
AUTH_EVENT_USER_DISABLED = "user.disabled"
AUTH_EVENT_USER_ENABLED = "user.enabled"
AUTH_EVENT_USER_PASSWORD_CHANGED = "user.password_changed"
AUTH_EVENT_USER_ROLE_ADDED = "user_role.added"
AUTH_EVENT_USER_ROLE_REMOVED = "user_role.removed"
AUTH_EVENT_USER_NOT_FOUND = "user.not_found"

AUTH_AUDIT_EVENT_TYPES = frozenset({
    AUTH_EVENT_LOGIN_SUCCESS,
    AUTH_EVENT_LOGIN_FAILED,
    AUTH_EVENT_LOGOUT,
    AUTH_EVENT_PASSWORD_RESET_REQUESTED,
    AUTH_EVENT_PASSWORD_RESET_COMPLETED,
    AUTH_EVENT_EMAIL_VERIFIED,
    AUTH_EVENT_MFA_REQUIRED,
    AUTH_EVENT_MFA_CHALLENGE_SUCCESS,
    AUTH_EVENT_MFA_CHALLENGE_FAILED,
    AUTH_EVENT_MFA_REVALIDATION_SUCCESS,
    AUTH_EVENT_MFA_REVALIDATION_FAILED,
    AUTH_EVENT_MFA_RATE_LIMITED,
    AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH,
    AUTH_EVENT_USER_DISABLED,
    AUTH_EVENT_USER_ENABLED,
    AUTH_EVENT_USER_PASSWORD_CHANGED,
    AUTH_EVENT_USER_ROLE_ADDED,
    AUTH_EVENT_USER_ROLE_REMOVED,
    AUTH_EVENT_USER_NOT_FOUND,
})

AUTH_AUDIT_SENSITIVE_METADATA_KEYS = frozenset({
    "password",
    "password_hash",
    "token",
    "raw_token",
    "access_token",
    "refresh_token",
    "id_token",
    "secret",
    "client_secret",
    "secret_hash",
    "totp_secret",
    "recovery_code",
    "code_verifier",
})


@dataclass(frozen=True)
class AuthAuditEvent:
    """Evenement d'audit Auth/User lisible et stockable."""

    id: int | None
    event_type: str
    user_id: int | None = None
    actor_user_id: int | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None


def _validate_optional_positive_int(value: Any, field_name: str) -> None:
    if value is None:
        return
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidAuthAuditEventError(
            f"{field_name} doit etre None ou un entier strictement positif"
        )


def _normalize_optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise InvalidAuthAuditEventError(
            f"{field_name} doit etre None ou une chaine non vide"
        )
    return value.strip()


def sanitize_auth_audit_metadata(metadata: dict | None) -> dict | None:
    """Retourne une copie de metadata sans cles sensibles connues."""
    if metadata is None:
        return None
    if not isinstance(metadata, dict):
        raise InvalidAuthAuditEventError("metadata doit etre None ou un dict")

    sanitized = {}
    for key, value in metadata.items():
        if isinstance(key, str) and key.lower() in AUTH_AUDIT_SENSITIVE_METADATA_KEYS:
            continue
        sanitized[key] = value
    return sanitized


def validate_auth_audit_event_contract(data: Any) -> AuthAuditEvent:
    """Valide et retourne un evenement d'audit Auth/User normalise.

    Les types d'evenement standards sont fournis par constantes, mais les
    applications peuvent utiliser des event_type personnalises non vides pour
    couvrir leurs propres actions sensibles.
    """
    if isinstance(data, AuthAuditEvent):
        raw = {
            "id": data.id,
            "event_type": data.event_type,
            "user_id": data.user_id,
            "actor_user_id": data.actor_user_id,
            "ip_address": data.ip_address,
            "user_agent": data.user_agent,
            "metadata": data.metadata,
            "created_at": data.created_at,
        }
    elif isinstance(data, dict):
        raw = data
    else:
        raise InvalidAuthAuditEventError(
            "les donnees audit auth doivent etre un AuthAuditEvent ou un dict"
        )

    event_type = raw.get("event_type")
    if not isinstance(event_type, str) or not event_type.strip():
        raise InvalidAuthAuditEventError("event_type doit etre une chaine non vide")

    event_id = raw.get("id")
    _validate_optional_positive_int(event_id, "id")
    _validate_optional_positive_int(raw.get("user_id"), "user_id")
    _validate_optional_positive_int(raw.get("actor_user_id"), "actor_user_id")

    metadata = raw.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        raise InvalidAuthAuditEventError("metadata doit etre None ou un dict")

    created_at = raw.get("created_at")
    if created_at is not None and not isinstance(created_at, datetime):
        raise InvalidAuthAuditEventError("created_at doit etre None ou une datetime")

    return AuthAuditEvent(
        id=event_id,
        event_type=event_type.strip(),
        user_id=raw.get("user_id"),
        actor_user_id=raw.get("actor_user_id"),
        ip_address=_normalize_optional_text(raw.get("ip_address"), "ip_address"),
        user_agent=_normalize_optional_text(raw.get("user_agent"), "user_agent"),
        metadata=sanitize_auth_audit_metadata(metadata),
        created_at=created_at,
    )


def normalize_auth_audit_event(data: Any) -> AuthAuditEvent:
    """Normalise un AuthAuditEvent ou un dict en AuthAuditEvent valide."""
    return validate_auth_audit_event_contract(data)


def is_valid_auth_audit_event(event: Any) -> bool:
    """Retourne True si event est un AuthAuditEvent structurellement valide."""
    try:
        validate_auth_audit_event_contract(event)
    except InvalidAuthAuditEventError:
        return False
    return isinstance(event, AuthAuditEvent)


def create_auth_audit_event(
    event_type: str,
    user_id: int | None = None,
    actor_user_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
    created_at: datetime | None = None,
) -> AuthAuditEvent:
    """Construit un evenement audit Auth/User sans effet de bord."""
    return normalize_auth_audit_event({
        "id": None,
        "event_type": event_type,
        "user_id": user_id,
        "actor_user_id": actor_user_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "metadata": sanitize_auth_audit_metadata(metadata),
        "created_at": created_at,
    })


_FAILURE_EVENT_TYPES: frozenset[str] = frozenset({
    AUTH_EVENT_LOGIN_FAILED,
    AUTH_EVENT_MFA_CHALLENGE_FAILED,
    AUTH_EVENT_MFA_REVALIDATION_FAILED,
    AUTH_EVENT_USER_DISABLED,
})


def log_auth_event(
    event_type: str,
    user_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
) -> None:
    """Journalise un evenement d'audit auth via le logger forge.auth.audit.

    Ne journalise jamais mot de passe, token, cookie ou code MFA — la
    sanitisation est appliquee via sanitize_auth_audit_metadata().

    Leve InvalidAuthAuditEventError si les parametres sont invalides.
    Pour un appel resilient qui n'interrompt jamais le flux metier, utiliser
    safe_log_auth_event().
    """
    event = create_auth_audit_event(
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata,
    )
    level = _logging.WARNING if event_type in _FAILURE_EVENT_TYPES else _logging.INFO
    _audit_logger.log(
        level,
        "%s user_id=%s ip=%s",
        event.event_type,
        event.user_id,
        event.ip_address,
    )


def safe_log_auth_event(*args: Any, **kwargs: Any) -> bool:
    """Emet un evenement audit sans propager d'exception.

    Tente d'appeler log_auth_event(*args, **kwargs). En cas d'echec :
    - L'exception n'est pas propagee (l'audit ne doit jamais bloquer une
      verification de securite).
    - Un avertissement est emis via le logger Python forge.auth.audit
      avec le traceback complet (exc_info=True).
    - Le compteur interne _audit_failure_count est incremente.

    Retourne True si succes, False si echec. Le retour est generalement
    ignore par les appelants — il sert principalement aux tests.
    """
    try:
        log_auth_event(*args, **kwargs)
        return True
    except Exception:
        global _audit_failure_count
        with _audit_failure_lock:
            _audit_failure_count += 1
        event_name = args[0] if args else kwargs.get("event_type", "<unknown>")
        _audit_logger.warning(
            "Audit event lost: failed to record %r (metadata=%r)",
            event_name,
            kwargs,
            exc_info=True,
        )
        return False


def get_audit_failure_count() -> int:
    """Retourne le nombre cumulatif d'echecs de safe_log_auth_event.

    Utile pour le monitoring ou les tests.
    """
    with _audit_failure_lock:
        return _audit_failure_count


def reset_audit_failure_count() -> None:
    """Remet le compteur d'echecs a zero. Reserve aux tests."""
    global _audit_failure_count
    with _audit_failure_lock:
        _audit_failure_count = 0
