"""Tests AUTH-RATE-LIMIT-001 — rate limit Auth/User generique."""

from __future__ import annotations

import inspect
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from core.auth import (
    AUTH_RATE_LIMIT_LOGIN,
    AUTH_RATE_LIMIT_MFA_CHALLENGE,
    AUTH_RATE_LIMIT_PASSWORD_RESET,
    AuthRateLimitAttempt,
    AuthRateLimitDecision,
    AuthRateLimitRule,
    InvalidAuthRateLimitAttemptError,
    InvalidAuthRateLimitRuleError,
    check_auth_rate_limit,
    create_auth_rate_limit_attempt,
    is_valid_auth_rate_limit_attempt,
    is_valid_auth_rate_limit_rule,
    normalize_auth_rate_limit_attempt,
    normalize_auth_rate_limit_rule,
    normalize_rate_limit_key,
)


def _rule(max_attempts: int = 3, window_seconds: int = 60) -> AuthRateLimitRule:
    return AuthRateLimitRule(
        action=AUTH_RATE_LIMIT_LOGIN,
        max_attempts=max_attempts,
        window_seconds=window_seconds,
    )


def _attempt(
    *,
    action: str = AUTH_RATE_LIMIT_LOGIN,
    key: str = "User@Example.Test",
    success: bool = False,
    created_at: datetime,
) -> AuthRateLimitAttempt:
    return AuthRateLimitAttempt(
        id=None,
        action=action,
        key=key,
        success=success,
        created_at=created_at,
    )


def test_normalize_rate_limit_key_trim_lower():
    assert normalize_rate_limit_key(" User@Example.Test ") == "user@example.test"


def test_normalize_rate_limit_key_refuse_chaine_vide():
    with pytest.raises(InvalidAuthRateLimitAttemptError):
        normalize_rate_limit_key(" ")


def test_normalize_rate_limit_key_refuse_none():
    with pytest.raises(InvalidAuthRateLimitAttemptError):
        normalize_rate_limit_key(None)


def test_creation_auth_rate_limit_attempt_valide():
    event_time = datetime(2026, 5, 6, 12, 0, 0)

    attempt = AuthRateLimitAttempt(
        id=None,
        action=AUTH_RATE_LIMIT_LOGIN,
        key="user@example.test",
        ip_address="192.0.2.10",
        user_id=1,
        success=False,
        created_at=event_time,
    )

    assert attempt.action == "login"
    assert attempt.key == "user@example.test"
    assert attempt.created_at == event_time


def test_normalisation_auth_rate_limit_attempt_depuis_dict():
    event_time = datetime(2026, 5, 6, 12, 0, 0)

    attempt = normalize_auth_rate_limit_attempt({
        "id": 4,
        "action": " Login ",
        "key": " User@Example.Test ",
        "ip_address": " 192.0.2.10 ",
        "user_id": 1,
        "success": False,
        "created_at": event_time,
    })

    assert attempt == AuthRateLimitAttempt(
        id=4,
        action=AUTH_RATE_LIMIT_LOGIN,
        key="user@example.test",
        ip_address="192.0.2.10",
        user_id=1,
        success=False,
        created_at=event_time,
    )


def test_normalisation_auth_rate_limit_attempt_depuis_objet():
    original = AuthRateLimitAttempt(
        id=None,
        action=AUTH_RATE_LIMIT_PASSWORD_RESET,
        key="user@example.test",
    )

    assert normalize_auth_rate_limit_attempt(original) == original


def test_action_obligatoire():
    with pytest.raises(InvalidAuthRateLimitAttemptError):
        normalize_auth_rate_limit_attempt({"id": None, "action": " ", "key": "user"})


def test_key_obligatoire():
    with pytest.raises(InvalidAuthRateLimitAttemptError):
        normalize_auth_rate_limit_attempt({"id": None, "action": "login", "key": " "})


def test_user_id_optionnel():
    attempt = normalize_auth_rate_limit_attempt({
        "id": None,
        "action": "login",
        "key": "user",
    })

    assert attempt.user_id is None


@pytest.mark.parametrize("value", [0, -1, True, "1"])
def test_user_id_invalide_refuse(value):
    with pytest.raises(InvalidAuthRateLimitAttemptError):
        normalize_auth_rate_limit_attempt({
            "id": None,
            "action": "login",
            "key": "user",
            "user_id": value,
        })


def test_success_doit_etre_booleen():
    with pytest.raises(InvalidAuthRateLimitAttemptError):
        normalize_auth_rate_limit_attempt({
            "id": None,
            "action": "login",
            "key": "user",
            "success": "false",
        })


def test_created_at_optionnel():
    attempt = normalize_auth_rate_limit_attempt({
        "id": None,
        "action": "login",
        "key": "user",
    })

    assert attempt.created_at is None


def test_is_valid_auth_rate_limit_attempt_retourne_true_sur_tentative_valide():
    attempt = AuthRateLimitAttempt(id=None, action=AUTH_RATE_LIMIT_LOGIN, key="user")

    assert is_valid_auth_rate_limit_attempt(attempt) is True


def test_is_valid_auth_rate_limit_attempt_retourne_false_sur_tentative_invalide():
    assert is_valid_auth_rate_limit_attempt({"id": None, "action": "", "key": "user"}) is False


def test_creation_auth_rate_limit_rule_valide():
    rule = AuthRateLimitRule(action=AUTH_RATE_LIMIT_LOGIN, max_attempts=5, window_seconds=900)

    assert rule.action == "login"
    assert rule.max_attempts == 5
    assert rule.window_seconds == 900


@pytest.mark.parametrize("value", [0, -1, True, "5"])
def test_max_attempts_doit_etre_positif(value):
    with pytest.raises(InvalidAuthRateLimitRuleError):
        normalize_auth_rate_limit_rule({
            "action": AUTH_RATE_LIMIT_LOGIN,
            "max_attempts": value,
            "window_seconds": 60,
        })


@pytest.mark.parametrize("value", [0, -1, False, "60"])
def test_window_seconds_doit_etre_positif(value):
    with pytest.raises(InvalidAuthRateLimitRuleError):
        normalize_auth_rate_limit_rule({
            "action": AUTH_RATE_LIMIT_LOGIN,
            "max_attempts": 5,
            "window_seconds": value,
        })


def test_is_valid_auth_rate_limit_rule_retourne_true_sur_regle_valide():
    assert is_valid_auth_rate_limit_rule(_rule()) is True


def test_is_valid_auth_rate_limit_rule_retourne_false_sur_regle_invalide():
    assert is_valid_auth_rate_limit_rule({
        "action": AUTH_RATE_LIMIT_LOGIN,
        "max_attempts": 0,
        "window_seconds": 60,
    }) is False


def test_create_auth_rate_limit_attempt_normalise_key():
    attempt = create_auth_rate_limit_attempt(
        action=" Login ",
        key=" User@Example.Test ",
        ip_address="192.0.2.10",
        success=False,
    )

    assert attempt.action == AUTH_RATE_LIMIT_LOGIN
    assert attempt.key == "user@example.test"


def test_check_auth_rate_limit_autorise_sous_la_limite():
    now = datetime(2026, 5, 6, 12, 0, 0)
    attempts = [
        _attempt(created_at=now - timedelta(seconds=10)),
        _attempt(created_at=now - timedelta(seconds=20)),
    ]

    decision = check_auth_rate_limit(
        action=AUTH_RATE_LIMIT_LOGIN,
        key="user@example.test",
        attempts=attempts,
        rule=_rule(max_attempts=3, window_seconds=60),
        now=now,
    )

    assert decision == AuthRateLimitDecision(
        allowed=True,
        action=AUTH_RATE_LIMIT_LOGIN,
        key="user@example.test",
        attempts_count=2,
        max_attempts=3,
        window_seconds=60,
        retry_after_seconds=None,
    )


def test_check_auth_rate_limit_bloque_a_la_limite():
    now = datetime(2026, 5, 6, 12, 0, 0)
    attempts = [
        _attempt(created_at=now - timedelta(seconds=10)),
        _attempt(created_at=now - timedelta(seconds=20)),
        _attempt(created_at=now - timedelta(seconds=30)),
    ]

    decision = check_auth_rate_limit(
        action=AUTH_RATE_LIMIT_LOGIN,
        key="user@example.test",
        attempts=attempts,
        rule=_rule(max_attempts=3, window_seconds=60),
        now=now,
    )

    assert decision.allowed is False
    assert decision.attempts_count == 3
    assert decision.retry_after_seconds == 30


def test_check_auth_rate_limit_ignore_les_succes():
    now = datetime(2026, 5, 6, 12, 0, 0)
    attempts = [
        _attempt(success=True, created_at=now - timedelta(seconds=10)),
        _attempt(success=True, created_at=now - timedelta(seconds=20)),
        _attempt(created_at=now - timedelta(seconds=30)),
    ]

    decision = check_auth_rate_limit(
        AUTH_RATE_LIMIT_LOGIN,
        "user@example.test",
        attempts,
        _rule(max_attempts=2, window_seconds=60),
        now=now,
    )

    assert decision.allowed is True
    assert decision.attempts_count == 1


def test_check_auth_rate_limit_ignore_les_autres_actions():
    now = datetime(2026, 5, 6, 12, 0, 0)
    attempts = [
        _attempt(action=AUTH_RATE_LIMIT_MFA_CHALLENGE, created_at=now - timedelta(seconds=10)),
        _attempt(action=AUTH_RATE_LIMIT_PASSWORD_RESET, created_at=now - timedelta(seconds=20)),
    ]

    decision = check_auth_rate_limit(
        AUTH_RATE_LIMIT_LOGIN,
        "user@example.test",
        attempts,
        _rule(max_attempts=1, window_seconds=60),
        now=now,
    )

    assert decision.allowed is True
    assert decision.attempts_count == 0


def test_check_auth_rate_limit_ignore_les_autres_keys():
    now = datetime(2026, 5, 6, 12, 0, 0)
    attempts = [
        _attempt(key="other@example.test", created_at=now - timedelta(seconds=10)),
        _attempt(key="another@example.test", created_at=now - timedelta(seconds=20)),
    ]

    decision = check_auth_rate_limit(
        AUTH_RATE_LIMIT_LOGIN,
        "user@example.test",
        attempts,
        _rule(max_attempts=1, window_seconds=60),
        now=now,
    )

    assert decision.allowed is True
    assert decision.attempts_count == 0


def test_check_auth_rate_limit_ignore_tentatives_hors_fenetre():
    now = datetime(2026, 5, 6, 12, 0, 0)
    attempts = [
        _attempt(created_at=now - timedelta(seconds=61)),
        _attempt(created_at=now - timedelta(seconds=120)),
    ]

    decision = check_auth_rate_limit(
        AUTH_RATE_LIMIT_LOGIN,
        "user@example.test",
        attempts,
        _rule(max_attempts=1, window_seconds=60),
        now=now,
    )

    assert decision.allowed is True
    assert decision.attempts_count == 0


def test_check_auth_rate_limit_calcule_retry_after_seconds():
    now = datetime(2026, 5, 6, 12, 0, 0)
    attempts = [
        _attempt(created_at=now - timedelta(seconds=50)),
        _attempt(created_at=now - timedelta(seconds=10)),
    ]

    decision = check_auth_rate_limit(
        AUTH_RATE_LIMIT_LOGIN,
        "user@example.test",
        attempts,
        _rule(max_attempts=2, window_seconds=60),
        now=now,
    )

    assert decision.allowed is False
    assert decision.retry_after_seconds == 10


def test_check_auth_rate_limit_ne_modifie_pas_les_tentatives():
    now = datetime(2026, 5, 6, 12, 0, 0)
    attempts = [
        {"id": None, "action": " Login ", "key": " User@Example.Test ", "created_at": now},
    ]
    before = [dict(attempts[0])]

    check_auth_rate_limit(
        AUTH_RATE_LIMIT_LOGIN,
        "user@example.test",
        attempts,
        _rule(max_attempts=2, window_seconds=60),
        now=now,
    )

    assert attempts == before


def test_api_importable_depuis_core_auth():
    import core.auth as auth

    assert auth.AuthRateLimitAttempt is AuthRateLimitAttempt
    assert auth.AuthRateLimitRule is AuthRateLimitRule
    assert auth.AUTH_RATE_LIMIT_LOGIN == "login"
    assert auth.check_auth_rate_limit is check_auth_rate_limit


def test_authenticate_user_non_modifie_par_rate_limit():
    source = Path("core/auth/session.py").read_text(encoding="utf-8")

    assert "auth_rate_limit" not in source
    assert "AuthRateLimit" not in source


def test_login_user_non_modifie_par_rate_limit():
    source = Path("core/auth/session.py").read_text(encoding="utf-8")

    assert "check_auth_rate_limit" not in source
    assert "create_auth_rate_limit_attempt" not in source


def test_module_necrit_pas_directement_en_base():
    import core.auth.rate_limit as module

    source = inspect.getsource(module)
    for forbidden in ("core.database", "fetch_", "insert(", "execute(", "commit("):
        assert forbidden not in source


def test_aucune_route_ou_interface_rate_limit_creee():
    candidates = "\n".join(
        path.as_posix()
        for root in ("mvc/controllers", "mvc/views")
        for path in Path(root).rglob("*")
    )

    assert "rate_limit" not in candidates.lower()
    assert "bruteforce" not in candidates.lower()
