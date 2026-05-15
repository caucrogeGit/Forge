"""Tests SEC-MFA-SECRET-NAMING-001 — renommage secret_hash → totp_secret.

Vérifie (état post-T4 MFA-SECRET-HASH-DEPRECATION-RESOLVE-001) :
- AuthMfaFactor.totp_secret est le champ canonique (unique — secret_hash retiré en 3.0.1)
- create_totp_factor émet un UserWarning unique sur le stockage en clair
- La colonne SQL s'appelle totp_secret dans les deux sources (SQL file et CLI constant)
"""

from __future__ import annotations

import warnings

import pytest

pytest.importorskip("forge_mvc_mfa")

from forge_mvc_mfa import (
    MFA_FACTOR_TOTP,
    MFA_STATUS_PENDING,
    AuthMfaFactor,
    create_totp_factor,
)

pytestmark = pytest.mark.meta


# ---------------------------------------------------------------------------
# TestTotpSecretField — champ canonique et alias déprécié
# ---------------------------------------------------------------------------


class TestTotpSecretField:
    def _factor(self, secret: str = "JBSWY3DPEHPK3PXP") -> AuthMfaFactor:
        return AuthMfaFactor(
            id=None, user_id=1, factor_type=MFA_FACTOR_TOTP,
            totp_secret=secret, status=MFA_STATUS_PENDING,
        )

    def test_totp_secret_field_exists(self):
        factor = self._factor("MYSECRET")
        assert factor.totp_secret == "MYSECRET"

    def test_totp_secret_is_not_auto_generated(self):
        factor = self._factor("PROVIDED_SECRET")
        assert factor.totp_secret == "PROVIDED_SECRET"

    def test_factor_is_immutable(self):
        factor = self._factor()
        with pytest.raises((AttributeError, TypeError)):
            factor.totp_secret = "new"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# TestPlaintextWarning — avertissement stockage en clair
# ---------------------------------------------------------------------------


class TestPlaintextWarning:
    def setup_method(self):
        import forge_mvc_mfa.mfa as _mfa_module
        _mfa_module._PLAINTEXT_SECRET_WARNING_EMITTED = False

    def test_create_totp_factor_emits_user_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            create_totp_factor(user_id=1)
        assert any(issubclass(w.category, UserWarning) for w in caught)

    def test_create_totp_factor_warning_mentions_totp_secret(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            create_totp_factor(user_id=1)
        messages = [str(w.message) for w in caught if issubclass(w.category, UserWarning)]
        assert any("TotpSecret" in m for m in messages)

    def test_create_totp_factor_warning_emitted_once_per_process(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            create_totp_factor(user_id=1)
            create_totp_factor(user_id=2)
            create_totp_factor(user_id=3)
        user_warnings = [w for w in caught if issubclass(w.category, UserWarning)
                         and "TotpSecret" in str(w.message)]
        assert len(user_warnings) == 1


# ---------------------------------------------------------------------------
# TestSqlColumnName — colonne SQL
# ---------------------------------------------------------------------------


class TestSqlColumnName:
    def test_sql_file_uses_totp_secret(self):
        from pathlib import Path
        sql_path = Path(__file__).resolve().parents[2] / "packages" / "forge-mvc-mfa" / "sql" / "auth_mfa_factors.sql"
        content = sql_path.read_text(encoding="utf-8")
        assert "totp_secret VARCHAR(255) NOT NULL" in content
        assert "secret_hash" not in content

    def test_cli_constant_uses_totp_secret(self):
        from forge_cli.auth import AUTH_MFA_FACTORS_SQL
        assert "totp_secret VARCHAR(255) NOT NULL" in AUTH_MFA_FACTORS_SQL
        assert "secret_hash" not in AUTH_MFA_FACTORS_SQL
