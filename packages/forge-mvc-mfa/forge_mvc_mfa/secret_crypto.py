# pyright: strict
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

Rotation de clé — MFA-KEY-ROTATION-001
--------------------------------------
``FORGE_MFA_SECRET_KEY_PREVIOUS`` liste les clés retirées, séparées par des
virgules. Elles servent **uniquement au déchiffrement** : le chiffrement utilise
toujours ``FORGE_MFA_SECRET_KEY``. Une rotation ne casse donc aucun facteur
existant, et l'application rechiffre à son rythme avec
``rotate_totp_secret()``.

Forge ne balaie pas la base lui-même : la table des facteurs appartient à
l'application (voir ``tables.py``), et Forge ne peut pas en présumer le nom.
Il fournit la primitive, l'application décide où elle s'applique.

Les erreurs ne révèlent jamais la valeur de la clé en clair, même
partiellement.
"""

from __future__ import annotations

import os

from core.security.secrets import PLACEHOLDER_VALUES

_PREFIX = "enc:"
_ENV_KEY = "FORGE_MFA_SECRET_KEY"
_ENV_PREVIOUS_KEYS = "FORGE_MFA_SECRET_KEY_PREVIOUS"

# Les valeurs d'amorçage refusées vivent dans le cœur depuis
# DEPLOY-CHECK-SECRETS-001 : le pré-vol de déploiement en avait besoin pour les
# mots de passe de base et les jetons d'API, et un opt-in ne peut pas dépendre
# d'un autre. La liste était ici, elle a remonté plutôt que d'être recopiée.
_PLACEHOLDER_KEYS = PLACEHOLDER_VALUES


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
        Fernet(stripped.encode() if isinstance(stripped, str) else stripped)  # pyright: ignore[reportUnnecessaryIsInstance]
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
    from cryptography.fernet import Fernet

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
        return Fernet(key.encode() if isinstance(key, str) else key)  # pyright: ignore[reportUnnecessaryIsInstance]
    except Exception:
        # Masque le message d'origine pour ne pas fuir la valeur de la clé.
        raise MfaSecretInvalidKey(
            f"{_ENV_KEY} contient une clé Fernet invalide. "
            + _generation_hint()
        ) from None


def _build_fernet(key: str, *, source: str):
    """Construit un Fernet depuis une clé, en refusant les valeurs douteuses.

    `source` nomme la variable d'environnement d'origine, pour que le message
    dise laquelle des deux est en cause sans jamais montrer sa valeur.
    """
    from cryptography.fernet import Fernet

    stripped = key.strip()
    if stripped.lower() in _PLACEHOLDER_KEYS:
        raise MfaSecretKeyPlaceholder(
            f"{source} contient une valeur placeholder évidente. "
            + _generation_hint()
        )
    try:
        return Fernet(stripped.encode())
    except Exception:
        # Masque le message d'origine pour ne pas fuir la valeur de la clé.
        raise MfaSecretInvalidKey(
            f"{source} contient une clé Fernet invalide. " + _generation_hint()
        ) from None


def previous_keys() -> list[str]:
    """Clés retirées encore acceptées au déchiffrement, dans l'ordre déclaré.

    Lues depuis ``FORGE_MFA_SECRET_KEY_PREVIOUS``, séparées par des virgules.
    Les entrées vides sont ignorées, pour qu'une virgule finale ou un retour à
    la ligne dans un fichier ``env/`` ne fasse pas échouer le démarrage.
    """
    raw = os.environ.get(_ENV_PREVIOUS_KEYS)
    if not raw or not raw.strip():
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _get_decryptor():
    """Fernet acceptant la clé courante **et** les clés retirées.

    L'ordre compte : la clé courante d'abord, si bien qu'un rechiffrement par
    ``MultiFernet.rotate`` produit toujours un jeton lisible par elle seule.
    """
    from cryptography.fernet import MultiFernet

    fernets = [_get_fernet()]
    fernets.extend(
        _build_fernet(key, source=_ENV_PREVIOUS_KEYS) for key in previous_keys()
    )
    return MultiFernet(fernets)


def uses_current_key(stored: str) -> bool:
    """Vrai si `stored` est déchiffrable par la clé courante seule.

    Sert à repérer ce qui reste à rechiffrer après une rotation, sans avoir à
    tenter l'écriture. Un secret non chiffré rend `False` plutôt que de lever :
    l'appelant balaie une table et veut un tri, pas une interruption.
    """
    if not isinstance(stored, str) or not stored.startswith(_PREFIX):  # pyright: ignore[reportUnnecessaryIsInstance]
        return False
    try:
        _get_fernet().decrypt(stored[len(_PREFIX):].encode())
    except Exception:
        return False
    return True


def rotate_totp_secret(stored: str) -> str:
    """Rechiffre un secret stocké avec la clé courante.

    Accepte un secret chiffré par la clé courante ou par l'une des clés
    retirées, et rend une valeur préfixée ``enc:`` lisible par la seule clé
    courante. L'appelant écrit le résultat dans **sa** table.

    Le secret en clair n'est jamais rendu ni journalisé : le rechiffrement
    passe par ``MultiFernet.rotate``, qui travaille de jeton à jeton.

    Raises:
        MfaSecretNotEncrypted: la valeur stockée n'est pas préfixée.
        MfaSecretInvalidKey: aucune clé connue ne déchiffre la valeur.
    """
    if not isinstance(stored, str) or not stored:  # pyright: ignore[reportUnnecessaryIsInstance]
        raise ValueError("stored doit être une chaîne non vide")
    if not stored.startswith(_PREFIX):
        raise MfaSecretNotEncrypted(
            "Le secret TOTP stocké n'est pas chiffré (préfixe 'enc:' absent). "
            "Migrer le secret avec encrypt_totp_secret() avant utilisation. "
            "Voir SEC-MFA-SECRET-ENCRYPTION-001."
        )
    payload = stored[len(_PREFIX):]
    try:
        rotated = _get_decryptor().rotate(payload.encode()).decode()
    except (MfaSecretKeyMissing, MfaSecretKeyPlaceholder, MfaSecretInvalidKey):
        raise
    except Exception as exc:
        raise MfaSecretInvalidKey(
            "Impossible de rechiffrer le secret TOTP : aucune clé connue ne le "
            f"déchiffre. Déclarer l'ancienne clé dans {_ENV_PREVIOUS_KEYS} le "
            "temps de la rotation."
        ) from exc
    return f"{_PREFIX}{rotated}"


def encrypt_totp_secret(raw: str) -> str:
    """Chiffre un secret TOTP brut. Retourne la valeur préfixée "enc:..."."""
    if not isinstance(raw, str) or not raw:  # pyright: ignore[reportUnnecessaryIsInstance]
        raise ValueError("raw doit être une chaîne non vide")
    fernet = _get_fernet()
    encrypted = fernet.encrypt(raw.encode()).decode()
    return f"{_PREFIX}{encrypted}"


def decrypt_totp_secret(stored: str) -> str:
    """Déchiffre un secret TOTP stocké. Lève MfaSecretNotEncrypted si non préfixé."""
    if not isinstance(stored, str) or not stored:  # pyright: ignore[reportUnnecessaryIsInstance]
        raise ValueError("stored doit être une chaîne non vide")
    if not stored.startswith(_PREFIX):
        raise MfaSecretNotEncrypted(
            "Le secret TOTP stocké n'est pas chiffré (préfixe 'enc:' absent). "
            "Migrer le secret avec encrypt_totp_secret() avant utilisation. "
            "Voir SEC-MFA-SECRET-ENCRYPTION-001."
        )
    payload = stored[len(_PREFIX):]
    # Accepte la clé courante et les clés retirées : une rotation ne doit pas
    # fermer la connexion des porteurs de facteur (MFA-KEY-ROTATION-001).
    decryptor = _get_decryptor()
    try:
        return decryptor.decrypt(payload.encode()).decode()
    except Exception as exc:
        raise MfaSecretInvalidKey(
            "Impossible de déchiffrer le secret TOTP."
        ) from exc
