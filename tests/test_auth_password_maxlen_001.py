"""Tests SEC-AUTH-PASSWORD-MAXLEN-001 — borne haute de longueur de mot de passe.

Sans plafond, un mot de passe tres long envoye a Argon2 (hash() a l'inscription/
reset, verify() au login non authentifie) ouvre un vecteur de deni de service :
Argon2 pre-hache l'entree entiere avant la partie memoire-dure. La borne haute
rejette l'entree AVANT tout calcul Argon2.
"""
from __future__ import annotations

import pytest

from core.auth import AuthError, hash_password, verify_password
from core.auth.password import _MAX_PASSWORD_LENGTH
from core.auth.exceptions import InvalidNewPasswordError
from core.auth.reset import validate_new_password


def test_max_password_length_is_128():
    assert _MAX_PASSWORD_LENGTH == 128


# --- hash_password (inscription / reset) --------------------------------------


def test_hash_password_accepts_exactly_max_length():
    password = "a" * _MAX_PASSWORD_LENGTH
    assert isinstance(hash_password(password), str)


def test_hash_password_rejects_over_max_length():
    password = "a" * (_MAX_PASSWORD_LENGTH + 1)
    with pytest.raises(AuthError, match="depasser"):
        hash_password(password)


def test_hash_password_rejects_megabyte_password_without_hashing():
    # Le rejet doit survenir avant Argon2 (pas de DoS).
    password = "a" * (1024 * 1024)
    with pytest.raises(AuthError, match="depasser"):
        hash_password(password)


# --- verify_password (login, non authentifie) ---------------------------------


def test_verify_password_false_for_over_max_length_without_raising():
    # Un mot de passe trop long au login echoue proprement (False), sans Argon2.
    password_hash = hash_password("secret123")
    over = "a" * (_MAX_PASSWORD_LENGTH + 1)
    assert verify_password(over, password_hash) is False


def test_verify_password_true_at_max_length_roundtrip():
    password = "b" * _MAX_PASSWORD_LENGTH
    password_hash = hash_password(password)
    assert verify_password(password, password_hash) is True


# --- validate_new_password (reset, message utilisateur propre) -----------------


def test_validate_new_password_accepts_max_length():
    assert validate_new_password("a" * _MAX_PASSWORD_LENGTH) is None


def test_validate_new_password_rejects_over_max_length():
    with pytest.raises(InvalidNewPasswordError, match="depasser"):
        validate_new_password("a" * (_MAX_PASSWORD_LENGTH + 1))


def test_validate_new_password_still_rejects_too_short():
    with pytest.raises(InvalidNewPasswordError, match="au moins"):
        validate_new_password("short")
