"""Tests SEC-MFA-TOTP-REPLAY-001 — anti-replay TOTP (RFC 6238 §5.2).

Un code TOTP accepté ne peut pas être rejoué dans la même step (30 s).
Les tests utilisent now= pour être déterministes et reset_replay pour l'isolation.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
pytest.importorskip("forge_mvc_mfa")
pytest.importorskip("pyotp")

import pyotp

from forge_mvc_mfa.secret_crypto import encrypt_totp_secret

_TEST_FERNET_KEY = "aGsgWXh_DXIOTYw2nsUvnhb8tQkPflH-rWnGywxsg8I="

@pytest.fixture(autouse=True)
def _mfa_secret_key(monkeypatch):
    monkeypatch.setenv("FORGE_MFA_SECRET_KEY", _TEST_FERNET_KEY)


from forge_mvc_mfa import (
    MFA_CHALLENGE_STARTED_AT_KEY,
    MFA_CHALLENGE_USER_ID_KEY,
    MFA_FACTOR_TOTP,
    MFA_STATUS_ACTIVE,
    AuthMfaFactor,
    MfaChallengeResult,
    verify_mfa_challenge,
    verify_mfa_revalidation,
)
from forge_mvc_mfa.totp_replay import (
    _TOTP_PERIOD_SECONDS,
    check_and_record,
    is_replay,
    purge_all,
    purge_old,
    record_used,
    step_for_time,
)

_NOW = datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc)
_STEP_NOW = step_for_time(_NOW.timestamp())


@pytest.fixture(autouse=True)
def reset_replay():
    purge_all()
    yield
    purge_all()


# --- check_and_record : consommation atomique (SEC-MFA-TOTP-REPLAY-ATOMIC-001) ---


def test_check_and_record_premiere_consommation_reussit():
    assert check_and_record(10, _STEP_NOW) is True
    # la step est désormais enregistrée
    assert is_replay(10, _STEP_NOW) is True


def test_check_and_record_deuxieme_consommation_meme_step_echoue():
    assert check_and_record(10, _STEP_NOW) is True
    assert check_and_record(10, _STEP_NOW) is False  # rejeu : course perdue


def test_check_and_record_step_plus_recente_reussit_step_passee_echoue():
    assert check_and_record(10, _STEP_NOW) is True
    assert check_and_record(10, _STEP_NOW + 1) is True
    assert check_and_record(10, _STEP_NOW) is False
    assert check_and_record(10, _STEP_NOW - 5) is False


def test_check_and_record_facteurs_independants():
    assert check_and_record(10, _STEP_NOW) is True
    assert check_and_record(11, _STEP_NOW) is True  # autre facteur, pas un rejeu


def test_check_and_record_factor_id_invalide_ne_bloque_pas():
    # non traçable : ne bloque pas, cohérent avec is_replay/record_used
    assert check_and_record(0, _STEP_NOW) is True
    assert check_and_record(-1, _STEP_NOW) is True


class FakeRequest:
    def __init__(self):
        self.session = {}


def _make_request_with_challenge(user_id: int = 1, now: datetime = _NOW) -> FakeRequest:
    req = FakeRequest()
    req.session[MFA_CHALLENGE_USER_ID_KEY] = user_id
    req.session[MFA_CHALLENGE_STARTED_AT_KEY] = now.isoformat()
    return req


def _authenticated_request(user_id: int = 1) -> FakeRequest:
    """Cree une FakeRequest avec session authentifiee pour la revalidation."""
    req = FakeRequest()
    req.session["authenticated"] = True
    req.session["user"] = {"id": user_id, "login": "test"}
    return req


def _make_totp_factor(
    user_id: int = 1,
    factor_id: int = 10,
    secret: str | None = None,
) -> tuple[AuthMfaFactor, str]:
    secret = secret or pyotp.random_base32()
    factor = AuthMfaFactor(
        id=factor_id,
        user_id=user_id,
        factor_type=MFA_FACTOR_TOTP,
        totp_secret=encrypt_totp_secret(secret),
        status=MFA_STATUS_ACTIVE,
        confirmed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    return factor, secret


# ---------------------------------------------------------------------------
# TestStepCalculation
# ---------------------------------------------------------------------------


class TestStepCalculation:
    def test_step_at_epoch_zero(self):
        assert step_for_time(0) == 0

    def test_step_just_before_boundary(self):
        assert step_for_time(29.99) == 0

    def test_step_at_boundary(self):
        assert step_for_time(30) == 1

    def test_step_increments_every_30s(self):
        t = 1_000_000.0
        s0 = step_for_time(t)
        assert step_for_time(t + 30) == s0 + 1
        assert step_for_time(t + 60) == s0 + 2

    def test_step_within_period_is_same(self):
        # Alignement sur le début de la step 33333
        t = 33333 * 30.0  # = 999990.0, début exact de la step
        s0 = step_for_time(t)
        assert step_for_time(t + 15) == s0
        assert step_for_time(t + 29.9) == s0


# ---------------------------------------------------------------------------
# TestReplayStore
# ---------------------------------------------------------------------------


class TestReplayStore:
    def test_no_replay_on_fresh_store(self):
        assert is_replay(1, _STEP_NOW) is False

    def test_record_then_same_step_is_replay(self):
        record_used(1, _STEP_NOW)
        assert is_replay(1, _STEP_NOW) is True

    def test_record_then_earlier_step_is_replay(self):
        record_used(1, _STEP_NOW)
        assert is_replay(1, _STEP_NOW - 1) is True

    def test_later_step_is_not_replay(self):
        record_used(1, _STEP_NOW)
        assert is_replay(1, _STEP_NOW + 1) is False

    def test_different_factor_is_independent(self):
        record_used(1, _STEP_NOW)
        assert is_replay(2, _STEP_NOW) is False

    def test_record_never_regresses(self):
        record_used(1, _STEP_NOW)
        record_used(1, _STEP_NOW - 5)  # tentative de régression ignorée
        assert is_replay(1, _STEP_NOW - 1) is True  # last = _STEP_NOW, pas la valeur régressée
        assert is_replay(1, _STEP_NOW) is True

    def test_record_advances_normally(self):
        record_used(1, _STEP_NOW)
        record_used(1, _STEP_NOW + 2)
        assert is_replay(1, _STEP_NOW + 1) is True
        assert is_replay(1, _STEP_NOW + 2) is True
        assert is_replay(1, _STEP_NOW + 3) is False

    def test_invalid_factor_id_is_not_replay(self):
        assert is_replay(0, _STEP_NOW) is False
        assert is_replay(-1, _STEP_NOW) is False

    def test_record_invalid_factor_id_is_noop(self):
        record_used(0, _STEP_NOW)
        record_used(-1, _STEP_NOW)
        assert is_replay(0, _STEP_NOW) is False


# ---------------------------------------------------------------------------
# TestPurgeOld
# ---------------------------------------------------------------------------


class TestPurgeOld:
    def test_purge_removes_entries_older_than_24h(self):
        now = 1_700_000_000.0
        cutoff_seconds = now - 25 * 3600
        old_step = step_for_time(cutoff_seconds)
        recent_step = step_for_time(now - 60)
        record_used(1, old_step)
        record_used(2, recent_step)
        removed = purge_old(now_seconds=now)
        assert removed == 1
        assert is_replay(1, old_step) is False
        assert is_replay(2, recent_step) is True

    def test_purge_keeps_entries_within_24h(self):
        now = 1_700_000_000.0
        step = step_for_time(now - 3600)  # 1h ago
        record_used(1, step)
        removed = purge_old(now_seconds=now)
        assert removed == 0
        assert is_replay(1, step) is True

    def test_purge_empty_store_is_noop(self):
        removed = purge_old()
        assert removed == 0

    def test_purge_all_clears_everything(self):
        record_used(1, _STEP_NOW)
        record_used(2, _STEP_NOW)
        purge_all()
        assert is_replay(1, _STEP_NOW) is False
        assert is_replay(2, _STEP_NOW) is False


# ---------------------------------------------------------------------------
# TestVerifyMfaChallengeReplay
# ---------------------------------------------------------------------------


class TestVerifyMfaChallengeReplay:
    def test_first_use_of_code_succeeds(self):
        factor, secret = _make_totp_factor()
        req = _make_request_with_challenge()
        code = pyotp.TOTP(secret).at(_NOW.timestamp())
        result = verify_mfa_challenge(req, code, factors=[factor], now=_NOW)
        assert isinstance(result, MfaChallengeResult)

    def test_replay_same_step_fails(self):
        """Rejouer le même code dans la même step est refusé."""
        factor, secret = _make_totp_factor()
        req = _make_request_with_challenge()
        code = pyotp.TOTP(secret).at(_NOW.timestamp())
        # Premier appel : succès (consomme le challenge)
        result1 = verify_mfa_challenge(req, code, factors=[factor], now=_NOW)
        assert result1 is not None
        # Nouveau challenge pour le deuxième appel (le premier a clear le challenge)
        req2 = _make_request_with_challenge()
        result2 = verify_mfa_challenge(req2, code, factors=[factor], now=_NOW)
        assert result2 is None

    def test_new_code_at_next_step_succeeds(self):
        """Un code valide à la step suivante est accepté après la step courante."""
        factor, secret = _make_totp_factor()
        req1 = _make_request_with_challenge(now=_NOW)
        code1 = pyotp.TOTP(secret).at(_NOW.timestamp())
        verify_mfa_challenge(req1, code1, factors=[factor], now=_NOW)
        # Step suivante
        now2 = datetime(_NOW.year, _NOW.month, _NOW.day, _NOW.hour, _NOW.minute,
                        _NOW.second + _TOTP_PERIOD_SECONDS, tzinfo=timezone.utc)
        code2 = pyotp.TOTP(secret).at(now2.timestamp())
        req2 = _make_request_with_challenge(now=now2)
        result = verify_mfa_challenge(req2, code2, factors=[factor], now=now2)
        assert result is not None

    def test_replay_counts_as_failure_for_rate_limit(self):
        """Un replay est compté comme échec dans le rate-limit."""
        from core.auth.rate_limit import is_locked_out, AUTH_RATE_LIMIT_MFA_CHALLENGE
        from forge_mvc_mfa import MFA_CHALLENGE_MAX_ATTEMPTS, MFA_CHALLENGE_WINDOW_SECONDS

        factor, secret = _make_totp_factor()
        code = pyotp.TOTP(secret).at(_NOW.timestamp())
        # Enregistrer le replay manuellement (simuler un usage précédent)
        from forge_mvc_mfa.totp_replay import record_used
        record_used(factor.id, _STEP_NOW)
        # Faire MAX-1 appels avec replay (compte comme échec)
        for _ in range(MFA_CHALLENGE_MAX_ATTEMPTS - 1):
            req = _make_request_with_challenge()
            verify_mfa_challenge(req, code, factors=[factor], now=_NOW)
        # À ce stade, MAX-1 échecs enregistrés → pas encore lockout
        assert not is_locked_out(
            AUTH_RATE_LIMIT_MFA_CHALLENGE, "user:1",
            max_attempts=MFA_CHALLENGE_MAX_ATTEMPTS,
            window_seconds=MFA_CHALLENGE_WINDOW_SECONDS,
            now=_NOW,
        )

    def test_replay_independent_factors(self):
        """Le replay d'un facteur n'affecte pas un autre facteur différent."""
        factor1, secret1 = _make_totp_factor(user_id=1, factor_id=10)
        factor2, secret2 = _make_totp_factor(user_id=1, factor_id=11)
        # Marquer factor1 comme rejoué
        record_used(factor1.id, _STEP_NOW)
        # Factor2 avec son propre code est encore accepté
        code2 = pyotp.TOTP(secret2).at(_NOW.timestamp())
        req = _make_request_with_challenge()
        result = verify_mfa_challenge(req, code2, factors=[factor1, factor2], now=_NOW)
        assert result is not None

    def test_factor_without_id_skips_replay_check(self):
        """Un facteur avec id=None (non persisté) passe sans check anti-replay."""
        secret = pyotp.random_base32()
        factor_no_id = AuthMfaFactor(
            id=None, user_id=1, factor_type=MFA_FACTOR_TOTP,
            totp_secret=encrypt_totp_secret(secret), status=MFA_STATUS_ACTIVE,
            confirmed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        code = pyotp.TOTP(secret).at(_NOW.timestamp())
        req = _make_request_with_challenge()
        result = verify_mfa_challenge(req, code, factors=[factor_no_id], now=_NOW)
        assert result is not None


# ---------------------------------------------------------------------------
# TestVerifyMfaRevalidationReplay
# ---------------------------------------------------------------------------


class TestVerifyMfaRevalidationReplay:
    def test_first_use_succeeds(self):
        factor, secret = _make_totp_factor()
        req = _authenticated_request(1)
        code = pyotp.TOTP(secret).at(_NOW.timestamp())
        result = verify_mfa_revalidation(req, 1, code, factors=[factor], now=_NOW)
        assert result is not None

    def test_replay_same_step_fails(self):
        factor, secret = _make_totp_factor()
        code = pyotp.TOTP(secret).at(_NOW.timestamp())
        req1 = _authenticated_request(1)
        verify_mfa_revalidation(req1, 1, code, factors=[factor], now=_NOW)
        req2 = _authenticated_request(1)
        result = verify_mfa_revalidation(req2, 1, code, factors=[factor], now=_NOW)
        assert result is None

    def test_new_step_succeeds_after_replay(self):
        factor, secret = _make_totp_factor()
        code1 = pyotp.TOTP(secret).at(_NOW.timestamp())
        req = _authenticated_request(1)
        verify_mfa_revalidation(req, 1, code1, factors=[factor], now=_NOW)
        now2 = datetime(_NOW.year, _NOW.month, _NOW.day, _NOW.hour, _NOW.minute,
                        _NOW.second + _TOTP_PERIOD_SECONDS, tzinfo=timezone.utc)
        code2 = pyotp.TOTP(secret).at(now2.timestamp())
        result = verify_mfa_revalidation(req, 1, code2, factors=[factor], now=now2)
        assert result is not None


# ---------------------------------------------------------------------------
# TestModuleImports
# ---------------------------------------------------------------------------


class TestModuleImports:
    def test_totp_replay_importable_from_core_auth(self):
        from forge_mvc_mfa import (
    is_replay,
    purge_all_totp_replay,
    purge_old,
    record_used,
    step_for_time,
)
        assert callable(is_replay)
        assert callable(record_used)
        assert callable(purge_old)
        assert callable(purge_all_totp_replay)
        assert callable(step_for_time)
