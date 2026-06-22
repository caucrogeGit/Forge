"""Tests SEC-MFA-SECRET-NAMING-001 — renommage secret_hash → totp_secret.

Vérifie (état post-SEC-MFA-SECRET-ENCRYPTION-001) :
- AuthMfaFactor.totp_secret est le champ canonique (unique — secret_hash retiré en 3.0.1)
- create_totp_factor chiffre le secret (préfixe "enc:") — plus de UserWarning plaintext
- La colonne SQL s'appelle totp_secret dans les deux sources (SQL file et CLI constant)
"""

from __future__ import annotations

import warnings

import pytest

pytest.importorskip("forge_mvc_mfa")
pytest.importorskip("cryptography")

from forge_mvc_mfa import (
    MFA_FACTOR_TOTP,
    MFA_STATUS_PENDING,
    AuthMfaFactor,
    create_totp_factor,
    decrypt_totp_secret,
)

pytestmark = pytest.mark.meta

_TEST_KEY = "zTXlmDcTEiMkxDmNKyPaxQsXaujLxJ9-vptH3Pt8Ico="


@pytest.fixture(autouse=True)
def _mfa_key(monkeypatch):
    monkeypatch.setenv("FORGE_MFA_SECRET_KEY", _TEST_KEY)


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
# TestEncryptedSecret — chiffrement remplace l'avertissement plaintext
# (SEC-MFA-SECRET-ENCRYPTION-001 : _warn_plaintext_secret_storage supprimé)
# ---------------------------------------------------------------------------


class TestEncryptedSecret:
    def test_create_totp_factor_totp_secret_is_encrypted(self):
        result = create_totp_factor(user_id=1)
        assert result.factor.totp_secret.startswith("enc:")

    def test_create_totp_factor_raw_secret_decryptable(self):
        result = create_totp_factor(user_id=1)
        assert decrypt_totp_secret(result.factor.totp_secret) == result.secret

    def test_create_totp_factor_no_plaintext_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            create_totp_factor(user_id=1)
        plaintext_warnings = [
            w for w in caught
            if issubclass(w.category, UserWarning) and "clair" in str(w.message).lower()
        ]
        assert not plaintext_warnings, (
            "Aucun UserWarning 'en clair' ne doit être émis depuis "
            "SEC-MFA-SECRET-ENCRYPTION-001."
        )


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
        from cli.security.auth import AUTH_MFA_FACTORS_SQL
        assert "totp_secret VARCHAR(255) NOT NULL" in AUTH_MFA_FACTORS_SQL
        assert "secret_hash" not in AUTH_MFA_FACTORS_SQL
