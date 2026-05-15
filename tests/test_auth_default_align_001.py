"""Tests AUTH-DEFAULT-ALIGN-001 — Alignement du contrôleur auth sur core.auth.

Vérifie que :
- un hash Argon2id est accepté par _check_password (chemin principal) ;
- un mauvais mot de passe est refusé ;
- un hash PBKDF2 legacy reste accepté (rétrocompatibilité) ;
- le contrôleur n'appelle pas verify_password_legacy pour un hash Argon2id.
"""

from __future__ import annotations

from unittest.mock import patch

import hashlib
import os

from core.auth.password import hash_password
from mvc.controllers.auth_controller import _check_password


def _create_pbkdf2_hash(password: str, iterations: int = 600_000) -> str:
    """Crée un hash PBKDF2 directement (helper de test, API supprimée)."""
    sel = os.urandom(16)
    hash_ = hashlib.pbkdf2_hmac("sha256", password.encode(), sel, iterations)
    return f"pbkdf2_sha256${iterations}${sel.hex()}${hash_.hex()}"


# ── _check_password avec hash Argon2id ───────────────────────────────────────

def test_check_password_accepte_hash_argon2id_valide():
    """Un hash Argon2id correct est accepté par _check_password."""
    h = hash_password("motdepasse")
    assert _check_password("motdepasse", h) is True


def test_check_password_refuse_mauvais_mot_de_passe_argon2id():
    """Un mauvais mot de passe est refusé pour un hash Argon2id."""
    h = hash_password("motdepasse")
    assert _check_password("mauvais", h) is False


def test_check_password_refuse_mot_de_passe_vide_argon2id():
    """Un mot de passe vide est refusé pour un hash Argon2id."""
    h = hash_password("motdepasse")
    assert _check_password("", h) is False


# ── _check_password avec hash PBKDF2 (rétrocompatibilité) ────────────────────

def test_check_password_accepte_hash_pbkdf2_valide():
    """Un hash PBKDF2 legacy existant reste vérifiable (rétrocompatibilité ADR-001)."""
    h = _create_pbkdf2_hash("ancienmdp")
    assert _check_password("ancienmdp", h) is True


def test_check_password_refuse_mauvais_mot_de_passe_pbkdf2():
    """Un mauvais mot de passe est refusé pour un hash PBKDF2."""
    h = _create_pbkdf2_hash("ancienmdp")
    assert _check_password("mauvais", h) is False


# ── Chemin principal : verify_password est appelé en premier ─────────────────

def test_check_password_appelle_verify_password_en_premier():
    """verify_password (Argon2id) est le chemin principal — verify_password_legacy
    n'est pas appelé si verify_password retourne True."""
    h = hash_password("secret")
    with patch("mvc.controllers.auth_controller.verify_password_legacy") as mock_pbkdf2:
        result = _check_password("secret", h)
    assert result is True
    mock_pbkdf2.assert_not_called()


def test_check_password_argon2id_repli_non_appele_sur_succes():
    """Si verify_password réussit, verify_password_legacy n'est jamais invoqué."""
    h = hash_password("abc")
    with patch("mvc.controllers.auth_controller.verify_password_legacy") as mock_pbkdf2:
        _check_password("abc", h)
    mock_pbkdf2.assert_not_called()


def test_check_password_pbkdf2_utilise_en_repli_si_verify_password_echoue():
    """verify_password_legacy est utilisé en repli si verify_password renvoie False."""
    h = _create_pbkdf2_hash("legacy")
    with patch("mvc.controllers.auth_controller.verify_password", return_value=False) as mock_argon:
        result = _check_password("legacy", h)
    mock_argon.assert_called_once()
    assert result is True


# ── Robustesse ────────────────────────────────────────────────────────────────

def test_check_password_hash_invalide_retourne_false():
    """Un hash invalide (ni Argon2id ni PBKDF2) retourne False sans lever d'exception."""
    assert _check_password("motdepasse", "pas-un-vrai-hash") is False


def test_check_password_hash_vide_retourne_false():
    """Un hash vide retourne False."""
    assert _check_password("motdepasse", "") is False
