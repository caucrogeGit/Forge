"""Chiffrement/déchiffrement des secrets TOTP stockés en base.

La clé Fernet est lue depuis la variable d'environnement FORGE_MFA_SECRET_KEY.
Les valeurs chiffrées sont préfixées par "enc:" pour distinguer les secrets
chiffrés des éventuelles valeurs legacy en clair.

Validation au boot — MFA-SECRET-KEY-BOOT-VALIDATION-001
-------------------------------------------------------
``validate_mfa_secret_key_config()`` permet à l'application de valider la
configuration MFA **explicitement et tôt** (au démarrage, plutôt qu'au
premier chiffrement). MFA reste opt-in : installer le package ne force
pas la validation — c'est l'application qui choisit de l'appeler quand
elle active MFA.

Les erreurs ne révèlent jamais la valeur de la clé en clair, même
partiellement.
"""

from __future__ import annotations

import os

_PREFIX = "enc:"
_ENV_KEY = "FORGE_MFA_SECRET_KEY"

# Valeurs placeholder évidentes à refuser explicitement. Ces chaînes
# apparaissent souvent dans les `.env.example` ou les templates et ne
# doivent JAMAIS atteindre la production. La comparaison est faite en
# minuscules et sur la chaîne complète strippée.
_PLACEHOLDER_KEYS: frozenset[str] = frozenset({
    "change-me",
    "changeme",
    "change_me",
    "default",
    "secret",
    "dev",
    "development",
    "test",
    "testing",
    "todo",
    "to-do",
    "placeholder",
    "xxx",
    "your-key-here",
    "your_key_here",
})


class MfaSecretKeyMissing(Exception):
    """FORGE_MFA_SECRET_KEY absent de l'environnement."""


class MfaSecretInvalidKey(Exception):
    """Clé invalide ou déchiffrement impossible."""


class MfaSecretKeyPlaceholder(Exception):
    """FORGE_MFA_SECRET_KEY contient une valeur placeholder évidente.

    Forge refuse les chaînes comme ``change-me``, ``default``, ``dev`` —
    voir ``_PLACEHOLDER_KEYS`` pour la liste exacte. Générer une vraie
    clé Fernet et la poser dans l'environnement de production.
    """


class MfaSecretNotEncrypted(Exception):
    """Secret legacy non chiffré détecté.

    Migrer le secret avec encrypt_totp_secret() avant utilisation.
    Voir SEC-MFA-SECRET-ENCRYPTION-001.
    """


def _generation_hint() -> str:
    """Commande exacte pour produire une clé Fernet valide.

    Centralisé pour que chaque message d'erreur renvoie le même conseil.
    """
    return (
        "Générer une clé avec : "
        "python -c \"from cryptography.fernet import Fernet; "
        "print(Fernet.generate_key().decode())\". "
        "Ne JAMAIS commiter cette clé dans le dépôt."
    )


def validate_mfa_secret_key_config() -> None:
    """Valide la configuration de la clé MFA — à appeler au démarrage.

    Vérifie, dans l'ordre :

    1. ``FORGE_MFA_SECRET_KEY`` est présent dans l'environnement ;
    2. la valeur est non vide (après ``strip()``) ;
    3. la valeur n'est pas un placeholder évident (``change-me``, etc.) ;
    4. la valeur est une clé Fernet valide (longueur, base64 url-safe,
       compatible avec ``cryptography.fernet.Fernet``).

    Aucune valeur de clé n'apparaît dans les messages d'erreur. Si la
    validation passe, la fonction retourne ``None`` sans effet de bord
    (aucune trace, aucun log).

    Raises:
        MfaSecretKeyMissing: variable d'environnement absente ou vide.
        MfaSecretKeyPlaceholder: valeur placeholder évidente refusée.
        MfaSecretInvalidKey: la valeur n'est pas une clé Fernet valide.
    """
    raw = os.environ.get(_ENV_KEY)
    if raw is None or not raw.strip():
        raise MfaSecretKeyMissing(
            f"La variable d'environnement {_ENV_KEY} est requise lorsque "
            "MFA est activé. " + _generation_hint()
        )
    stripped = raw.strip()
    if stripped.lower() in _PLACEHOLDER_KEYS:
        # On NE révèle PAS la valeur — on dit juste qu'elle est placeholder.
        raise MfaSecretKeyPlaceholder(
            f"{_ENV_KEY} contient une valeur placeholder évidente. "
            "Forge refuse les chaînes comme « change-me », « default », "
            "« dev », « secret », etc. " + _generation_hint()
        )
    # Validation Fernet par construction effective. Ne logue rien.
    from cryptography.fernet import Fernet  # noqa: F401
    try:
        Fernet(stripped.encode() if isinstance(stripped, str) else stripped)
    except Exception:
        # Le message d'origine de `cryptography` peut contenir des fragments
        # de la clé. On le masque (`from None`) pour ne pas fuir la valeur
        # dans les logs applicatifs.
        raise MfaSecretInvalidKey(
            f"{_ENV_KEY} contient une clé Fernet invalide "
            "(format attendu : 32 octets URL-safe base64). " + _generation_hint()
        ) from None


def _get_fernet():
    """Retourne une instance Fernet initialisée depuis FORGE_MFA_SECRET_KEY."""
    from cryptography.fernet import Fernet, InvalidToken  # noqa: F401

    key = os.environ.get(_ENV_KEY)
    if not key or not key.strip():
        raise MfaSecretKeyMissing(
            f"La variable d'environnement {_ENV_KEY} est absente. "
            + _generation_hint()
        )
    if key.strip().lower() in _PLACEHOLDER_KEYS:
        raise MfaSecretKeyPlaceholder(
            f"{_ENV_KEY} contient une valeur placeholder évidente. "
            + _generation_hint()
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        # Masque le message d'origine pour ne pas fuir la valeur de la clé.
        raise MfaSecretInvalidKey(
            f"{_ENV_KEY} contient une clé Fernet invalide. "
            + _generation_hint()
        ) from None


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
