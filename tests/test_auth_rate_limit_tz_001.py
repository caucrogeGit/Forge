"""Garde-fou SEC-RATELIMIT-TZ-001 : le rate limit tolere naif et aware.

Regression du deni de service MFA : record_attempt cote MFA enregistrait un
created_at tz-aware (UTC) tandis que is_locked_out(), appele sans now sur le
chemin de production, recalculait un datetime.now() naif. La comparaison
naif/aware levait TypeError, verrouillant toute connexion MFA de la victime
jusqu'au redemarrage du worker, y compris avec un code correct.

Le controle anti-bruteforce doit desormais renvoyer un booleen dans tous les
melanges naif/aware, jamais lever.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from core.auth.rate_limit import (
    AuthRateLimitRule,
    check_auth_rate_limit,
    create_auth_rate_limit_attempt,
    is_locked_out,
    purge_all_attempts,
    record_attempt,
)


@pytest.fixture(autouse=True)
def _clean_store():
    purge_all_attempts()
    yield
    purge_all_attempts()


def test_record_aware_then_is_locked_out_sans_now_ne_leve_pas():
    """Le scenario exact du DoS MFA : enregistrement aware, controle sans now."""
    record_attempt(
        "mfa_challenge",
        "user:1",
        now=datetime.now(tz=timezone.utc),
    )
    # Chemin de production : is_locked_out sans now (now interne = aware UTC).
    result = is_locked_out("mfa_challenge", "user:1", 5, 300)
    assert result is False  # une seule tentative, pas de verrou, surtout pas de crash


def test_is_locked_out_verrouille_apres_le_seuil_sans_now():
    for _ in range(5):
        record_attempt("mfa_challenge", "user:2", now=datetime.now(tz=timezone.utc))
    assert is_locked_out("mfa_challenge", "user:2", 5, 300) is True


@pytest.mark.parametrize("now_tz", ["naive", "aware"])
def test_check_tolere_created_at_naif_et_now_mixte(now_tz):
    """created_at naif (ex. charge d'une base sans tz) reste comparable."""
    base = datetime.now(tz=timezone.utc)
    naive_attempt = create_auth_rate_limit_attempt(
        "login",
        "10.0.0.1",
        created_at=base.replace(tzinfo=None),  # naif, comme une colonne DATETIME
    )
    now = base if now_tz == "aware" else base.replace(tzinfo=None)
    rule = AuthRateLimitRule(action="login", max_attempts=3, window_seconds=300)
    decision = check_auth_rate_limit("login", "10.0.0.1", [naive_attempt], rule, now=now)
    assert decision.allowed is True
    assert decision.attempts_count == 1


def test_check_melange_aware_et_naif_dans_le_meme_lot():
    base = datetime.now(tz=timezone.utc)
    aware = create_auth_rate_limit_attempt("login", "10.0.0.2", created_at=base)
    naive = create_auth_rate_limit_attempt(
        "login", "10.0.0.2", created_at=(base - timedelta(seconds=10)).replace(tzinfo=None)
    )
    rule = AuthRateLimitRule(action="login", max_attempts=5, window_seconds=300)
    decision = check_auth_rate_limit("login", "10.0.0.2", [aware, naive], rule, now=base)
    assert decision.attempts_count == 2
    assert decision.allowed is True
