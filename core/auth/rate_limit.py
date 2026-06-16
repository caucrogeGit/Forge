"""Protection anti-bruteforce Auth/User minimale.

Ce module represente des tentatives d'actions sensibles et calcule une decision
de limitation a partir de tentatives deja chargees par l'application. Il ne lit
ni n'ecrit aucune base de donnees, ne cree aucun audit et ne modifie aucune
session.

Les helpers imperatifs (record_attempt, is_locked_out, clear_attempts) stockent
les tentatives en memoire processus (thread-safe via RLock). Meme limitation
que core.security.hashing : en multi-worker chaque processus a son propre compteur.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import ceil
from typing import Any

from core.auth.exceptions import (
    InvalidAuthRateLimitAttemptError,
    InvalidAuthRateLimitRuleError,
)


AUTH_RATE_LIMIT_LOGIN = "login"
AUTH_RATE_LIMIT_PASSWORD_RESET = "password_reset"
AUTH_RATE_LIMIT_MFA_CHALLENGE = "mfa_challenge"
AUTH_RATE_LIMIT_MFA_REVALIDATION = "mfa_revalidation"


@dataclass(frozen=True)
class AuthRateLimitAttempt:
    """Tentative d'action sensible exploitable pour le rate limit."""

    id: int | None
    action: str
    key: str
    ip_address: str | None = None
    user_id: int | None = None
    success: bool = False
    created_at: datetime | None = None


@dataclass(frozen=True)
class AuthRateLimitRule:
    """Regle simple de limitation pour une action Auth/User."""

    action: str
    max_attempts: int
    window_seconds: int


@dataclass(frozen=True)
class AuthRateLimitDecision:
    """Decision calculée a partir d'une regle et d'un historique."""

    allowed: bool
    action: str
    key: str
    attempts_count: int
    max_attempts: int
    window_seconds: int
    retry_after_seconds: int | None = None


def normalize_rate_limit_key(value: object) -> str:
    """Normalise une cle de limitation stable."""
    if not isinstance(value, str):
        raise InvalidAuthRateLimitAttemptError("key doit etre une chaine non vide")
    normalized = value.strip().lower()
    if not normalized:
        raise InvalidAuthRateLimitAttemptError("key doit etre une chaine non vide")
    return normalized


def _normalize_action(value: Any, error_cls: type[Exception]) -> str:
    if not isinstance(value, str) or not value.strip():
        raise error_cls("action doit etre une chaine non vide")
    return value.strip().lower()


def _validate_optional_positive_int(
    value: Any,
    field_name: str,
    error_cls: type[Exception],
) -> None:
    if value is None:
        return
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise error_cls(f"{field_name} doit etre None ou un entier strictement positif")


def _normalize_optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise InvalidAuthRateLimitAttemptError(
            f"{field_name} doit etre None ou une chaine non vide"
        )
    return value.strip()


def validate_auth_rate_limit_attempt_contract(data: Any) -> AuthRateLimitAttempt:
    """Valide et retourne une tentative Auth/User normalisee."""
    if isinstance(data, AuthRateLimitAttempt):
        raw = {
            "id": data.id,
            "action": data.action,
            "key": data.key,
            "ip_address": data.ip_address,
            "user_id": data.user_id,
            "success": data.success,
            "created_at": data.created_at,
        }
    elif isinstance(data, dict):
        raw = data
    else:
        raise InvalidAuthRateLimitAttemptError(
            "les donnees rate limit doivent etre un AuthRateLimitAttempt ou un dict"
        )

    attempt_id = raw.get("id")
    _validate_optional_positive_int(
        attempt_id,
        "id",
        InvalidAuthRateLimitAttemptError,
    )
    _validate_optional_positive_int(
        raw.get("user_id"),
        "user_id",
        InvalidAuthRateLimitAttemptError,
    )

    success = raw.get("success", False)
    if not isinstance(success, bool):
        raise InvalidAuthRateLimitAttemptError("success doit etre un booleen")

    created_at = raw.get("created_at")
    if created_at is not None and not isinstance(created_at, datetime):
        raise InvalidAuthRateLimitAttemptError("created_at doit etre None ou une datetime")

    return AuthRateLimitAttempt(
        id=attempt_id,
        action=_normalize_action(raw.get("action"), InvalidAuthRateLimitAttemptError),
        key=normalize_rate_limit_key(raw.get("key")),
        ip_address=_normalize_optional_text(raw.get("ip_address"), "ip_address"),
        user_id=raw.get("user_id"),
        success=success,
        created_at=created_at,
    )


def normalize_auth_rate_limit_attempt(data: Any) -> AuthRateLimitAttempt:
    """Normalise un AuthRateLimitAttempt ou un dict."""
    return validate_auth_rate_limit_attempt_contract(data)


def is_valid_auth_rate_limit_attempt(attempt: Any) -> bool:
    """Retourne True si attempt est un AuthRateLimitAttempt valide."""
    try:
        validate_auth_rate_limit_attempt_contract(attempt)
    except InvalidAuthRateLimitAttemptError:
        return False
    return isinstance(attempt, AuthRateLimitAttempt)


def validate_auth_rate_limit_rule_contract(data: Any) -> AuthRateLimitRule:
    """Valide et retourne une regle Auth/User normalisee."""
    if isinstance(data, AuthRateLimitRule):
        raw = {
            "action": data.action,
            "max_attempts": data.max_attempts,
            "window_seconds": data.window_seconds,
        }
    elif isinstance(data, dict):
        raw = data
    else:
        raise InvalidAuthRateLimitRuleError(
            "les donnees regle rate limit doivent etre un AuthRateLimitRule ou un dict"
        )

    max_attempts = raw.get("max_attempts")
    if (
        not isinstance(max_attempts, int)
        or isinstance(max_attempts, bool)
        or max_attempts <= 0
    ):
        raise InvalidAuthRateLimitRuleError(
            "max_attempts doit etre un entier strictement positif"
        )

    window_seconds = raw.get("window_seconds")
    if (
        not isinstance(window_seconds, int)
        or isinstance(window_seconds, bool)
        or window_seconds <= 0
    ):
        raise InvalidAuthRateLimitRuleError(
            "window_seconds doit etre un entier strictement positif"
        )

    return AuthRateLimitRule(
        action=_normalize_action(raw.get("action"), InvalidAuthRateLimitRuleError),
        max_attempts=max_attempts,
        window_seconds=window_seconds,
    )


def normalize_auth_rate_limit_rule(data: Any) -> AuthRateLimitRule:
    """Normalise une regle AuthRateLimitRule ou un dict."""
    return validate_auth_rate_limit_rule_contract(data)


def is_valid_auth_rate_limit_rule(rule: Any) -> bool:
    """Retourne True si rule est un AuthRateLimitRule valide."""
    try:
        validate_auth_rate_limit_rule_contract(rule)
    except InvalidAuthRateLimitRuleError:
        return False
    return isinstance(rule, AuthRateLimitRule)


def create_auth_rate_limit_attempt(
    action: str,
    key: str,
    ip_address: str | None = None,
    user_id: int | None = None,
    success: bool = False,
    created_at: datetime | None = None,
) -> AuthRateLimitAttempt:
    """Construit une tentative rate limit Auth/User sans effet de bord."""
    return normalize_auth_rate_limit_attempt({
        "id": None,
        "action": action,
        "key": key,
        "ip_address": ip_address,
        "user_id": user_id,
        "success": success,
        "created_at": created_at,
    })


def check_auth_rate_limit(
    action: str,
    key: str,
    attempts: Any,
    rule: Any,
    now: datetime | None = None,
) -> AuthRateLimitDecision:
    """Calcule si action/key reste autorise dans la fenetre de la regle."""
    checked_action = _normalize_action(action, InvalidAuthRateLimitAttemptError)
    checked_key = normalize_rate_limit_key(key)
    checked_rule = normalize_auth_rate_limit_rule(rule)
    if checked_rule.action != checked_action:
        raise InvalidAuthRateLimitRuleError("la regle ne correspond pas a l'action")

    if attempts is None:
        attempts_iterable = ()
    else:
        attempts_iterable = tuple(attempts)

    now = now or datetime.now()
    window_start = now - timedelta(seconds=checked_rule.window_seconds)
    matching_failures: list[AuthRateLimitAttempt] = []

    for raw_attempt in attempts_iterable:
        attempt = normalize_auth_rate_limit_attempt(raw_attempt)
        if attempt.action != checked_action:
            continue
        if attempt.key != checked_key:
            continue
        if attempt.success:
            continue
        if attempt.created_at is None:
            continue
        if not (window_start <= attempt.created_at <= now):
            continue
        matching_failures.append(attempt)

    attempts_count = len(matching_failures)
    if attempts_count < checked_rule.max_attempts:
        return AuthRateLimitDecision(
            allowed=True,
            action=checked_action,
            key=checked_key,
            attempts_count=attempts_count,
            max_attempts=checked_rule.max_attempts,
            window_seconds=checked_rule.window_seconds,
            retry_after_seconds=None,
        )

    oldest = min(attempt.created_at for attempt in matching_failures if attempt.created_at)
    retry_after = max(
        0,
        ceil((oldest + timedelta(seconds=checked_rule.window_seconds) - now).total_seconds()),
    )
    return AuthRateLimitDecision(
        allowed=False,
        action=checked_action,
        key=checked_key,
        attempts_count=attempts_count,
        max_attempts=checked_rule.max_attempts,
        window_seconds=checked_rule.window_seconds,
        retry_after_seconds=retry_after,
    )


# ---------------------------------------------------------------------------
# Store in-memory process-local — API impérative (helpers stateful)
# ---------------------------------------------------------------------------
# Limitation assumée : en multi-worker (gunicorn, uWSGI) chaque processus a son
# propre _attempts_store. Comportement cohérent avec core.security.hashing.
# Solution multi-worker : backend partagé (DB, Redis) hors scope de ce ticket.

_attempts_store: dict[str, list[AuthRateLimitAttempt]] = {}
_store_lock = threading.RLock()


def record_attempt(
    action: str,
    key: str,
    user_id: int | None = None,
    ip_address: str | None = None,
    success: bool = False,
    now: datetime | None = None,
) -> None:
    """Enregistre une tentative dans le store in-memory."""
    ts = now if now is not None else datetime.now()
    attempt = create_auth_rate_limit_attempt(
        action=action,
        key=key,
        ip_address=ip_address,
        user_id=user_id,
        success=success,
        created_at=ts,
    )
    store_key = f"{attempt.action}:{attempt.key}"
    with _store_lock:
        _attempts_store.setdefault(store_key, []).append(attempt)


def is_locked_out(
    action: str,
    key: str,
    max_attempts: int,
    window_seconds: int,
    now: datetime | None = None,
) -> bool:
    """Retourne True si la clé a dépassé max_attempts échecs dans la fenêtre."""
    checked_action = _normalize_action(action, InvalidAuthRateLimitAttemptError)
    checked_key = normalize_rate_limit_key(key)
    store_key = f"{checked_action}:{checked_key}"
    rule = AuthRateLimitRule(
        action=checked_action,
        max_attempts=max_attempts,
        window_seconds=window_seconds,
    )
    with _store_lock:
        attempts = list(_attempts_store.get(store_key, []))
    decision = check_auth_rate_limit(checked_action, checked_key, attempts, rule, now=now)
    return not decision.allowed


def clear_attempts(action: str, key: str) -> None:
    """Supprime toutes les tentatives mémorisées pour cette action/clé."""
    checked_action = _normalize_action(action, InvalidAuthRateLimitAttemptError)
    checked_key = normalize_rate_limit_key(key)
    store_key = f"{checked_action}:{checked_key}"
    with _store_lock:
        _attempts_store.pop(store_key, None)


def purge_all_attempts() -> None:
    """Vide le store complet — réservé aux tests."""
    with _store_lock:
        _attempts_store.clear()


# ── Rate limiting de connexion — API IP-based ──────────────────────────────────
# Migré depuis core.security.hashing (HASHING-RATELIMIT-MOVE-001).
# Ces constantes et helpers exposent une API simple (IP uniquement) utilisée
# par auth_controller et re-exportée depuis core.security.hashing pour
# la rétro-compatibilité.

LOGIN_MAX_ATTEMPTS = 5
LOGIN_RATE_LIMIT_WINDOW = 60  # secondes (fenêtre glissante)


def record_login_attempt(ip: str) -> None:
    """Enregistre une tentative de connexion échouée pour cette IP."""
    record_attempt("login", ip)


def is_login_rate_limited(ip: str) -> bool:
    """Retourne True si l'IP a atteint la limite de tentatives de connexion."""
    return is_locked_out("login", ip, LOGIN_MAX_ATTEMPTS, LOGIN_RATE_LIMIT_WINDOW)
