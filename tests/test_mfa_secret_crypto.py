"""Tests SEC-MFA-SECRET-ENCRYPTION-001 — chiffrement des secrets TOTP."""

from __future__ import annotations

import pytest
pytest.importorskip("forge_mvc_mfa")
pytest.importorskip("cryptography")

from forge_mvc_mfa.secret_crypto import (
    MfaSecretInvalidKey,
    MfaSecretKeyMissing,
    MfaSecretNotEncrypted,
    decrypt_totp_secret,
    encrypt_totp_secret,
)

_TEST_KEY = "zTXlmDcTEiMkxDmNKyPaxQsXaujLxJ9-vptH3Pt8Ico="
_OTHER_KEY = "U3BlY2lhbFNlY3JldEtleVRlc3QxMjM0NTY3ODkwMTI="


@pytest.fixture(autouse=True)
def _set_key(monkeypatch):
    monkeypatch.setenv("FORGE_MFA_SECRET_KEY", _TEST_KEY)


# ---------------------------------------------------------------------------
# encrypt_totp_secret
# ---------------------------------------------------------------------------

def test_encrypt_returns_enc_prefix():
    result = encrypt_totp_secret("JBSWY3DPEHPK3PXP")
    assert result.startswith("enc:")


def test_encrypt_not_equal_to_raw():
    raw = "JBSWY3DPEHPK3PXP"
    result = encrypt_totp_secret(raw)
    assert result != raw


def test_encrypt_two_calls_differ():
    """Fernet produit un chiffré non déterministe (IV aléatoire)."""
    raw = "JBSWY3DPEHPK3PXP"
    assert encrypt_totp_secret(raw) != encrypt_totp_secret(raw)


def test_encrypt_empty_raises():
    with pytest.raises(ValueError):
        encrypt_totp_secret("")


def test_encrypt_non_string_raises():
    with pytest.raises((ValueError, TypeError)):
        encrypt_totp_secret(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# decrypt_totp_secret
# ---------------------------------------------------------------------------

def test_roundtrip():
    raw = "JBSWY3DPEHPK3PXP"
    stored = encrypt_totp_secret(raw)
    assert decrypt_totp_secret(stored) == raw


def test_decrypt_missing_prefix_raises():
    with pytest.raises(MfaSecretNotEncrypted):
        decrypt_totp_secret("JBSWY3DPEHPK3PXP")


def test_decrypt_empty_raises():
    with pytest.raises(ValueError):
        decrypt_totp_secret("")


def test_decrypt_corrupted_payload_raises():
    with pytest.raises(MfaSecretInvalidKey):
        decrypt_totp_secret("enc:notvalidbase64!!")


# ---------------------------------------------------------------------------
# Erreurs clé manquante / invalide
# ---------------------------------------------------------------------------

def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("FORGE_MFA_SECRET_KEY", raising=False)
    with pytest.raises(MfaSecretKeyMissing):
        encrypt_totp_secret("JBSWY3DPEHPK3PXP")


def test_invalid_key_raises(monkeypatch):
    monkeypatch.setenv("FORGE_MFA_SECRET_KEY", "notavalidkey")
    with pytest.raises(MfaSecretInvalidKey):
        encrypt_totp_secret("JBSWY3DPEHPK3PXP")


def test_wrong_key_decrypt_raises(monkeypatch):
    """Un secret chiffré avec _TEST_KEY ne peut pas être déchiffré avec _OTHER_KEY."""
    stored = encrypt_totp_secret("JBSWY3DPEHPK3PXP")
    monkeypatch.setenv("FORGE_MFA_SECRET_KEY", _OTHER_KEY)
    with pytest.raises(MfaSecretInvalidKey):
        decrypt_totp_secret(stored)
