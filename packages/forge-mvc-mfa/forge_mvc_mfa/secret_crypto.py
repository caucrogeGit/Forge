"""Chiffrement/déchiffrement des secrets TOTP stockés en base.

La clé Fernet est lue depuis la variable d'environnement FORGE_MFA_SECRET_KEY.
Les valeurs chiffrées sont préfixées par "enc:" pour distinguer les secrets
chiffrés des éventuelles valeurs legacy en clair.
"""

from __future__ import annotations

import os

_PREFIX = "enc:"
_ENV_KEY = "FORGE_MFA_SECRET_KEY"


class MfaSecretKeyMissing(Exception):
    """FORGE_MFA_SECRET_KEY absent de l'environnement."""


class MfaSecretInvalidKey(Exception):
    """Clé invalide ou déchiffrement impossible."""


class MfaSecretNotEncrypted(Exception):
    """Secret legacy non chiffré détecté.

    Migrer le secret avec encrypt_totp_secret() avant utilisation.
    Voir SEC-MFA-SECRET-ENCRYPTION-001.
    """


def _get_fernet():
    """Retourne une instance Fernet initialisée depuis FORGE_MFA_SECRET_KEY."""
    from cryptography.fernet import Fernet, InvalidToken  # noqa: F401

    key = os.environ.get(_ENV_KEY)
    if not key:
        raise MfaSecretKeyMissing(
            f"La variable d'environnement {_ENV_KEY} est absente. "
            "Générer une clé avec : python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:
        raise MfaSecretInvalidKey(
            f"{_ENV_KEY} contient une clé Fernet invalide : {exc}"
        ) from exc


def encrypt_totp_secret(raw: str) -> str:
    """Chiffre un secret TOTP brut. Retourne la valeur préfixée "enc:..."."""
    if not isinstance(raw, str) or not raw:
        raise ValueError("raw doit être une chaîne non vide")
    fernet = _get_fernet()
    encrypted = fernet.encrypt(raw.encode()).decode()
    return f"{_PREFIX}{encrypted}"


def decrypt_totp_secret(stored: str) -> str:
    """Déchiffre un secret TOTP stocké. Lève MfaSecretNotEncrypted si non préfixé."""
    if not isinstance(stored, str) or not stored:
        raise ValueError("stored doit être une chaîne non vide")
    if not stored.startswith(_PREFIX):
        raise MfaSecretNotEncrypted(
            "Le secret TOTP stocké n'est pas chiffré (préfixe 'enc:' absent). "
            "Migrer le secret avec encrypt_totp_secret() avant utilisation. "
            "Voir SEC-MFA-SECRET-ENCRYPTION-001."
        )
    payload = stored[len(_PREFIX):]
    fernet = _get_fernet()
    try:
        return fernet.decrypt(payload.encode()).decode()
    except Exception as exc:
        raise MfaSecretInvalidKey(
            f"Impossible de déchiffrer le secret TOTP : {exc}"
        ) from exc
