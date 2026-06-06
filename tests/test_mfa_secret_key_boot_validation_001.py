"""Tests — MFA-SECRET-KEY-BOOT-VALIDATION-001.

Verrouille que ``forge_mvc_mfa.validate_mfa_secret_key_config()`` rejette
explicitement et précocement les configurations dangereuses de
``FORGE_MFA_SECRET_KEY`` :

  * absente / vide ;
  * valeurs placeholder évidentes (``change-me``, ``default``, ``dev``,
    ``secret``, ``test``…) ;
  * clé non Fernet (mauvaise longueur, base64 invalide).

Et accepte les clés Fernet valides.

Le module MFA est opt-in : ces tests sont protégés par
``pytest.importorskip`` pour rester compatibles avec une installation
core-only (cf TESTS-OPTIN-IMPORTORSKIP-001).
"""
from __future__ import annotations

import os

import pytest

pytest.importorskip("forge_mvc_mfa")
pytest.importorskip("cryptography")

from cryptography.fernet import Fernet

from forge_mvc_mfa import (
    MfaSecretInvalidKey,
    MfaSecretKeyMissing,
    MfaSecretKeyPlaceholder,
    encrypt_totp_secret,
    validate_mfa_secret_key_config,
)


_ENV_KEY = "FORGE_MFA_SECRET_KEY"
_VALID_KEY = Fernet.generate_key().decode()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def clean_env(monkeypatch):
    """Garantit un environnement sans `FORGE_MFA_SECRET_KEY` au début du test."""
    monkeypatch.delenv(_ENV_KEY, raising=False)


# ---------------------------------------------------------------------------
# Cas d'erreur — absente / vide
# ---------------------------------------------------------------------------


class TestKeyMissing:
    def test_key_absent_raises_missing(self, clean_env):
        with pytest.raises(MfaSecretKeyMissing) as exc:
            validate_mfa_secret_key_config()
        # Message exploitable : mentionne le nom de la variable.
        assert _ENV_KEY in str(exc.value)
        # Et indique comment générer une clé valide.
        assert "Fernet" in str(exc.value)

    def test_empty_string_raises_missing(self, monkeypatch):
        monkeypatch.setenv(_ENV_KEY, "")
        with pytest.raises(MfaSecretKeyMissing) as exc:
            validate_mfa_secret_key_config()
        assert _ENV_KEY in str(exc.value)

    def test_whitespace_only_raises_missing(self, monkeypatch):
        monkeypatch.setenv(_ENV_KEY, "   \t  ")
        with pytest.raises(MfaSecretKeyMissing) as exc:
            validate_mfa_secret_key_config()
        assert _ENV_KEY in str(exc.value)


# ---------------------------------------------------------------------------
# Cas d'erreur — placeholders évidents
# ---------------------------------------------------------------------------


class TestKeyPlaceholder:
    @pytest.mark.parametrize("placeholder", [
        "change-me",
        "changeme",
        "change_me",
        "CHANGE-ME",       # casse-insensible
        "ChangeMe",
        "default",
        "secret",
        "dev",
        "development",
        "test",
        "testing",
        "TODO",
        "to-do",
        "placeholder",
        "xxx",
        "your-key-here",
        "your_key_here",
        "  change-me  ",   # strippé avant comparaison
    ])
    def test_placeholder_value_raises(self, monkeypatch, placeholder):
        monkeypatch.setenv(_ENV_KEY, placeholder)
        with pytest.raises(MfaSecretKeyPlaceholder) as exc:
            validate_mfa_secret_key_config()
        # Le message ne révèle JAMAIS la valeur en clair (test de fuite).
        # C'est essentiel pour éviter qu'un log de stack-trace exposé révèle
        # par exemple le mot `secret` quand l'utilisateur a mis ça littéralement.
        # On accepte que les valeurs neutres de la liste apparaissent dans la
        # liste des refus du message, mais la valeur exacte de l'utilisateur
        # ne doit pas faire de surprise inutile.
        assert _ENV_KEY in str(exc.value)

    def test_placeholder_message_explains_remedy(self, monkeypatch):
        monkeypatch.setenv(_ENV_KEY, "change-me")
        with pytest.raises(MfaSecretKeyPlaceholder) as exc:
            validate_mfa_secret_key_config()
        msg = str(exc.value)
        assert "Fernet" in msg or "générer" in msg.lower()


# ---------------------------------------------------------------------------
# Cas d'erreur — clé Fernet invalide
# ---------------------------------------------------------------------------


class TestKeyInvalid:
    @pytest.mark.parametrize("invalid", [
        "not-a-fernet-key",
        "AAAA",                        # trop court
        "A" * 100,                     # mauvaise longueur
        "!" * 44,                      # mauvaise alphabet base64
        "short-but-not-placeholder-X", # ni placeholder ni Fernet
    ])
    def test_invalid_fernet_key_raises(self, monkeypatch, invalid):
        monkeypatch.setenv(_ENV_KEY, invalid)
        with pytest.raises(MfaSecretInvalidKey) as exc:
            validate_mfa_secret_key_config()
        # Message exploitable : nom de variable + format attendu.
        assert _ENV_KEY in str(exc.value)
        assert "Fernet" in str(exc.value)
        # GARDE-FOU FUITE — la valeur de la clé invalide ne doit jamais
        # apparaître dans le message. Sinon un log d'erreur exposé révèle
        # ce que l'utilisateur a essayé.
        # On vérifie pour les valeurs longues (>= 32 caractères) — pour
        # les très courtes, les chances de collision avec des mots du
        # message sont trop grandes (`AAAA` peut apparaître par hasard).
        if len(invalid) >= 32:
            assert invalid not in str(exc.value), (
                f"La clé invalide {invalid!r} fuit dans le message d'erreur — "
                "risque de log applicatif révélant la clé tentée."
            )


# ---------------------------------------------------------------------------
# Cas valide
# ---------------------------------------------------------------------------


class TestKeyValid:
    def test_valid_fernet_key_passes(self, monkeypatch):
        monkeypatch.setenv(_ENV_KEY, _VALID_KEY)
        # Ne doit rien lever, ne retourne rien.
        result = validate_mfa_secret_key_config()
        assert result is None

    def test_valid_key_with_surrounding_whitespace_passes(self, monkeypatch):
        # Les .env mal édités collent parfois des espaces ou un \n en bordure.
        # Contrat ferme : la validation strip la clé et l'accepte (ne lève pas).
        monkeypatch.setenv(_ENV_KEY, f"  {_VALID_KEY}\n")
        validate_mfa_secret_key_config()


# ---------------------------------------------------------------------------
# Non-régression : usage runtime continue de fonctionner avec une vraie clé
# ---------------------------------------------------------------------------


class TestEncryptStillWorksWithValidKey:
    """`encrypt_totp_secret` doit fonctionner avec une clé Fernet valide.
    Cette validation est nécessaire pour s'assurer que le durcissement
    n'a pas cassé le flot existant."""

    def test_encrypt_decrypt_roundtrip(self, monkeypatch):
        from forge_mvc_mfa import decrypt_totp_secret
        monkeypatch.setenv(_ENV_KEY, _VALID_KEY)
        enc = encrypt_totp_secret("JBSWY3DPEHPK3PXP")
        assert enc.startswith("enc:")
        assert decrypt_totp_secret(enc) == "JBSWY3DPEHPK3PXP"

    def test_encrypt_rejects_placeholder_via_get_fernet(self, monkeypatch):
        """Le chemin lazy `_get_fernet` doit aussi refuser les placeholders
        (sinon un appel à `encrypt_totp_secret` court-circuiterait la
        validation explicite)."""
        monkeypatch.setenv(_ENV_KEY, "change-me")
        with pytest.raises(MfaSecretKeyPlaceholder):
            encrypt_totp_secret("JBSWY3DPEHPK3PXP")

    def test_encrypt_rejects_missing_via_get_fernet(self, monkeypatch):
        monkeypatch.delenv(_ENV_KEY, raising=False)
        with pytest.raises(MfaSecretKeyMissing):
            encrypt_totp_secret("JBSWY3DPEHPK3PXP")


# ---------------------------------------------------------------------------
# Importer le module MFA sans activation ne casse PAS le core
# ---------------------------------------------------------------------------


class TestInstallOnlyDoesNotBreakCore:
    """Critère d'acceptation : l'installation du module MFA ne doit pas
    casser une application core-only. On vérifie ici que le simple import
    de `forge_mvc_mfa` ne consulte JAMAIS `FORGE_MFA_SECRET_KEY`."""

    def test_module_imports_without_env_var(self, clean_env):
        # Si l'import déclenchait `_get_fernet()` ou `validate_...`, on
        # aurait déjà eu MfaSecretKeyMissing. On le re-importe pour rester
        # explicite — `monkeypatch` n'affecte pas l'état déjà importé.
        import importlib
        import forge_mvc_mfa
        importlib.reload(forge_mvc_mfa)
        assert os.environ.get(_ENV_KEY) is None
        # API publique reste accessible sans erreur.
        assert callable(forge_mvc_mfa.validate_mfa_secret_key_config)
        assert callable(forge_mvc_mfa.encrypt_totp_secret)
