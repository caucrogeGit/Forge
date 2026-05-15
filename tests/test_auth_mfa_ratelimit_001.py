"""Tests SEC-MFA-RATELIMIT-001 — branchement du rate-limit sur verify_mfa_challenge
et verify_mfa_revalidation.

Les tests utilisent now= pour s'affranchir du temps réel et purge_rl pour
isoler le store in-memory entre les cas.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
pytest.importorskip("forge_mvc_mfa")
pytest.importorskip("pyotp")

import pyotp

from core.auth.audit import AUTH_EVENT_MFA_RATE_LIMITED
from forge_mvc_mfa import (
    MFA_CHALLENGE_MAX_ATTEMPTS,
    MFA_CHALLENGE_STARTED_AT_KEY,
    MFA_CHALLENGE_USER_ID_KEY,
    MFA_CHALLENGE_WINDOW_SECONDS,
    MFA_FACTOR_TOTP,
    MFA_REVALIDATION_MAX_ATTEMPTS,
    MFA_STATUS_ACTIVE,
    AuthMfaFactor,
    verify_mfa_challenge,
    verify_mfa_revalidation,
)
from core.auth.rate_limit import purge_all_attempts


@pytest.fixture(autouse=True)
def purge_rl():
    purge_all_attempts()
    yield
    purge_all_attempts()


class FakeRequest:
    def __init__(self):
        self.session = {}


def _make_request_with_challenge(
    user_id: int = 42,
    now: datetime | None = None,
) -> FakeRequest:
    req = FakeRequest()
    ts = now or datetime.now(tz=timezone.utc)
    req.session[MFA_CHALLENGE_USER_ID_KEY] = user_id
    req.session[MFA_CHALLENGE_STARTED_AT_KEY] = ts.isoformat()
    return req


def _make_revalidation_request(user_id: int = 42) -> FakeRequest:
    """Cree une FakeRequest avec session authentifiee pour la revalidation."""
    req = FakeRequest()
    req.session["authenticated"] = True
    req.session["user"] = {"id": user_id, "login": "test"}
    return req


def _make_totp_factor(user_id: int = 42) -> tuple[AuthMfaFactor, str]:
    secret = pyotp.random_base32()
    factor = AuthMfaFactor(
        id=1,
        user_id=user_id,
        factor_type=MFA_FACTOR_TOTP,
        totp_secret=secret,
        status=MFA_STATUS_ACTIVE,
        confirmed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    return factor, secret


# ---------------------------------------------------------------------------
# TestMfaChallengeRateLimit
# ---------------------------------------------------------------------------


class TestMfaChallengeRateLimit:
    def test_allows_attempts_within_limit(self):
        """Les MFA_CHALLENGE_MAX_ATTEMPTS - 1 premiers échecs ne lockent pas."""
        now = datetime.now(tz=timezone.utc)
        req = _make_request_with_challenge(now=now)
        for _ in range(MFA_CHALLENGE_MAX_ATTEMPTS - 1):
            result = verify_mfa_challenge(req, "000000", factors=[], now=now)
            assert result is None  # échec normal, pas lockout

    def test_blocks_after_max_attempts(self):
        """Après MFA_CHALLENGE_MAX_ATTEMPTS échecs, un bon code est aussi refusé."""
        now = datetime.now(tz=timezone.utc)
        factor, secret = _make_totp_factor()
        req = _make_request_with_challenge(now=now)
        for _ in range(MFA_CHALLENGE_MAX_ATTEMPTS):
            verify_mfa_challenge(req, "000000", factors=[factor], now=now)
        # Même un code valide est refusé par le lockout
        code = pyotp.TOTP(secret).at(now)
        result = verify_mfa_challenge(req, code, factors=[factor], now=now)
        assert result is None

    def test_success_clears_counter(self):
        """Un succès remet le compteur à zéro — les tentatives suivantes repartent de 0."""
        from core.auth.rate_limit import is_locked_out, AUTH_RATE_LIMIT_MFA_CHALLENGE

        now = datetime.now(tz=timezone.utc)
        factor, secret = _make_totp_factor()
        req = _make_request_with_challenge(now=now)
        # 4 échecs (max - 1)
        for _ in range(MFA_CHALLENGE_MAX_ATTEMPTS - 1):
            verify_mfa_challenge(req, "000000", factors=[factor], now=now)
        # Succès
        code = pyotp.TOTP(secret).at(now)
        result = verify_mfa_challenge(req, code, factors=[factor], now=now)
        assert result is not None
        # Le compteur est nettoyé : plus de lockout sur cette clé
        assert not is_locked_out(
            AUTH_RATE_LIMIT_MFA_CHALLENGE, "user:42",
            max_attempts=MFA_CHALLENGE_MAX_ATTEMPTS,
            window_seconds=MFA_CHALLENGE_WINDOW_SECONDS,
            now=now,
        )

    def test_audit_event_emitted_on_lockout(self, monkeypatch):
        """AUTH_EVENT_MFA_RATE_LIMITED est journalisé quand le lockout bloque."""
        events: list[str] = []

        def _fake_log(event_type, **kw):
            events.append(event_type)

        monkeypatch.setattr("core.auth.audit.log_auth_event", _fake_log)

        now = datetime.now(tz=timezone.utc)
        req = _make_request_with_challenge(now=now)
        for _ in range(MFA_CHALLENGE_MAX_ATTEMPTS):
            verify_mfa_challenge(req, "000000", factors=[], now=now)
        # Prochain appel → lockout → audit
        verify_mfa_challenge(req, "000000", factors=[], now=now)
        assert AUTH_EVENT_MFA_RATE_LIMITED in events

    def test_no_audit_event_on_normal_failure(self, monkeypatch):
        """L'événement rate_limited n'est pas émis pour un simple échec de code."""
        events: list[str] = []
        monkeypatch.setattr("core.auth.audit.log_auth_event",
                            lambda event_type, **kw: events.append(event_type))
        now = datetime.now(tz=timezone.utc)
        req = _make_request_with_challenge(now=now)
        verify_mfa_challenge(req, "000000", factors=[], now=now)
        assert AUTH_EVENT_MFA_RATE_LIMITED not in events

    def test_independent_users_independent_counters(self):
        """Le lockout d'user A ne bloque pas user B."""
        now = datetime.now(tz=timezone.utc)
        factor42, _ = _make_totp_factor(user_id=42)
        factor43, secret43 = _make_totp_factor(user_id=43)
        # Locker user 42
        req42 = _make_request_with_challenge(user_id=42, now=now)
        for _ in range(MFA_CHALLENGE_MAX_ATTEMPTS):
            verify_mfa_challenge(req42, "000000", factors=[factor42], now=now)
        # User 43 peut encore s'authentifier
        req43 = _make_request_with_challenge(user_id=43, now=now)
        code43 = pyotp.TOTP(secret43).at(now)
        result = verify_mfa_challenge(req43, code43, factors=[factor43], now=now)
        assert result is not None

    def test_expired_window_resets_counter(self):
        """Des tentatives hors de la fenêtre temporelle ne comptent plus."""
        from datetime import timedelta
        from core.auth.rate_limit import is_locked_out, AUTH_RATE_LIMIT_MFA_CHALLENGE

        past = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        future = past + timedelta(seconds=MFA_CHALLENGE_WINDOW_SECONDS + 1)
        factor, secret = _make_totp_factor()
        req = _make_request_with_challenge(now=past)
        # MAX tentatives dans le passé
        for _ in range(MFA_CHALLENGE_MAX_ATTEMPTS):
            verify_mfa_challenge(req, "000000", factors=[factor], now=past)
        # Dans le futur (après la fenêtre), le compteur est expiré
        assert not is_locked_out(
            AUTH_RATE_LIMIT_MFA_CHALLENGE, "user:42",
            max_attempts=MFA_CHALLENGE_MAX_ATTEMPTS,
            window_seconds=MFA_CHALLENGE_WINDOW_SECONDS,
            now=future,
        )


# ---------------------------------------------------------------------------
# TestMfaRevalidationRateLimit
# ---------------------------------------------------------------------------


class TestMfaRevalidationRateLimit:
    def test_allows_attempts_within_limit(self):
        """Les MFA_REVALIDATION_MAX_ATTEMPTS - 1 premiers échecs ne lockent pas."""
        now = datetime.now(tz=timezone.utc)
        req = _make_revalidation_request(42)
        for _ in range(MFA_REVALIDATION_MAX_ATTEMPTS - 1):
            result = verify_mfa_revalidation(req, 42, "000000", factors=[], now=now)
            assert result is None

    def test_blocks_after_max_attempts(self):
        """Après MFA_REVALIDATION_MAX_ATTEMPTS échecs, un bon code est refusé."""
        now = datetime.now(tz=timezone.utc)
        factor, secret = _make_totp_factor()
        req = _make_revalidation_request(42)
        for _ in range(MFA_REVALIDATION_MAX_ATTEMPTS):
            verify_mfa_revalidation(req, 42, "000000", factors=[factor], now=now)
        code = pyotp.TOTP(secret).at(now)
        result = verify_mfa_revalidation(req, 42, code, factors=[factor], now=now)
        assert result is None

    def test_success_clears_counter(self):
        """Un succès remet le compteur revalidation à zéro."""
        from core.auth.rate_limit import is_locked_out, AUTH_RATE_LIMIT_MFA_REVALIDATION
        from forge_mvc_mfa import MFA_REVALIDATION_WINDOW_SECONDS

        now = datetime.now(tz=timezone.utc)
        factor, secret = _make_totp_factor()
        req = _make_revalidation_request(42)
        for _ in range(MFA_REVALIDATION_MAX_ATTEMPTS - 1):
            verify_mfa_revalidation(req, 42, "000000", factors=[factor], now=now)
        code = pyotp.TOTP(secret).at(now)
        result = verify_mfa_revalidation(req, 42, code, factors=[factor], now=now)
        assert result is not None
        assert not is_locked_out(
            AUTH_RATE_LIMIT_MFA_REVALIDATION, "user:42",
            max_attempts=MFA_REVALIDATION_MAX_ATTEMPTS,
            window_seconds=MFA_REVALIDATION_WINDOW_SECONDS,
            now=now,
        )

    def test_audit_event_emitted_on_lockout(self, monkeypatch):
        """AUTH_EVENT_MFA_RATE_LIMITED est journalisé pour la revalidation lockée."""
        events: list[str] = []
        monkeypatch.setattr("core.auth.audit.log_auth_event",
                            lambda event_type, **kw: events.append(event_type))
        now = datetime.now(tz=timezone.utc)
        req = _make_revalidation_request(42)
        for _ in range(MFA_REVALIDATION_MAX_ATTEMPTS):
            verify_mfa_revalidation(req, 42, "000000", factors=[], now=now)
        verify_mfa_revalidation(req, 42, "000000", factors=[], now=now)  # lockout
        assert AUTH_EVENT_MFA_RATE_LIMITED in events

    def test_independent_users_independent_counters(self):
        """Le lockout de revalidation d'user A ne bloque pas user B."""
        now = datetime.now(tz=timezone.utc)
        factor42, _ = _make_totp_factor(user_id=42)
        factor43, secret43 = _make_totp_factor(user_id=43)
        req42 = _make_revalidation_request(42)
        for _ in range(MFA_REVALIDATION_MAX_ATTEMPTS):
            verify_mfa_revalidation(req42, 42, "000000", factors=[factor42], now=now)
        req43 = _make_revalidation_request(43)
        code43 = pyotp.TOTP(secret43).at(now)
        result = verify_mfa_revalidation(req43, 43, code43, factors=[factor43], now=now)
        assert result is not None


# ---------------------------------------------------------------------------
# TestRateLimitStoreAPI
# ---------------------------------------------------------------------------


class TestRateLimitStoreAPI:
    def test_record_then_is_locked_out(self):
        """record_attempt + is_locked_out sont cohérents."""
        from core.auth.rate_limit import (
            record_attempt, is_locked_out, AUTH_RATE_LIMIT_MFA_CHALLENGE,
        )
        now = datetime.now(tz=timezone.utc)
        for _ in range(MFA_CHALLENGE_MAX_ATTEMPTS):
            record_attempt(AUTH_RATE_LIMIT_MFA_CHALLENGE, "user:99", user_id=99, now=now)
        assert is_locked_out(
            AUTH_RATE_LIMIT_MFA_CHALLENGE, "user:99",
            max_attempts=MFA_CHALLENGE_MAX_ATTEMPTS,
            window_seconds=MFA_CHALLENGE_WINDOW_SECONDS,
            now=now,
        )

    def test_clear_attempts_unlocks(self):
        """clear_attempts() supprime le lockout."""
        from core.auth.rate_limit import (
            record_attempt, is_locked_out, clear_attempts, AUTH_RATE_LIMIT_MFA_CHALLENGE,
        )
        now = datetime.now(tz=timezone.utc)
        for _ in range(MFA_CHALLENGE_MAX_ATTEMPTS):
            record_attempt(AUTH_RATE_LIMIT_MFA_CHALLENGE, "user:77", user_id=77, now=now)
        clear_attempts(AUTH_RATE_LIMIT_MFA_CHALLENGE, "user:77")
        assert not is_locked_out(
            AUTH_RATE_LIMIT_MFA_CHALLENGE, "user:77",
            max_attempts=MFA_CHALLENGE_MAX_ATTEMPTS,
            window_seconds=MFA_CHALLENGE_WINDOW_SECONDS,
            now=now,
        )

    def test_purge_all_clears_everything(self):
        """purge_all_attempts() vide tout le store."""
        from core.auth.rate_limit import (
            record_attempt, is_locked_out, AUTH_RATE_LIMIT_MFA_CHALLENGE,
        )
        now = datetime.now(tz=timezone.utc)
        for _ in range(MFA_CHALLENGE_MAX_ATTEMPTS):
            record_attempt(AUTH_RATE_LIMIT_MFA_CHALLENGE, "user:55", user_id=55, now=now)
        purge_all_attempts()
        assert not is_locked_out(
            AUTH_RATE_LIMIT_MFA_CHALLENGE, "user:55",
            max_attempts=MFA_CHALLENGE_MAX_ATTEMPTS,
            window_seconds=MFA_CHALLENGE_WINDOW_SECONDS,
            now=now,
        )

    def test_importable_from_core_auth(self):
        """Les helpers imperatifs sont importables depuis core.auth."""
        from core.auth import (
            clear_attempts,
            is_locked_out,
            purge_all_attempts,
            record_attempt,
        )
        assert callable(record_attempt)
        assert callable(is_locked_out)
        assert callable(clear_attempts)
        assert callable(purge_all_attempts)

    def test_new_audit_event_importable_from_core_auth(self):
        """AUTH_EVENT_MFA_RATE_LIMITED est importable depuis core.auth."""
        from core.auth import AUTH_EVENT_MFA_RATE_LIMITED as evt
        assert evt == "mfa.rate_limited"

    def test_new_audit_event_in_known_types(self):
        """AUTH_EVENT_MFA_RATE_LIMITED est dans AUTH_AUDIT_EVENT_TYPES."""
        from core.auth.audit import AUTH_AUDIT_EVENT_TYPES
        assert AUTH_EVENT_MFA_RATE_LIMITED in AUTH_AUDIT_EVENT_TYPES

    def test_mfa_challenge_constants_exported(self):
        """Les constantes de rate-limit MFA sont importables depuis core.auth.mfa."""
        from forge_mvc_mfa import (
            MFA_CHALLENGE_MAX_ATTEMPTS,
            MFA_CHALLENGE_WINDOW_SECONDS,
            MFA_REVALIDATION_MAX_ATTEMPTS,
            MFA_REVALIDATION_WINDOW_SECONDS,
        )
        assert MFA_CHALLENGE_MAX_ATTEMPTS == 5
        assert MFA_CHALLENGE_WINDOW_SECONDS == 300
        assert MFA_REVALIDATION_MAX_ATTEMPTS == 3
        assert MFA_REVALIDATION_WINDOW_SECONDS == 300
