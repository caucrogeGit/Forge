"""Codes de recuperation MFA a usage unique pour Auth/User.

Les codes bruts ne sont jamais stockes. Seul le hash SHA-256 du code normalise
est conserve cote serveur. Un code consomme est marque via used_at.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from core.auth.exceptions import InvalidMfaRecoveryCodeError


# Alphabet sans caracteres ambigus (sans O, 0, I, 1)
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_GROUP_SIZE = 4
_GROUP_COUNT = 4
_SEPARATOR = "-"

# SHA-256 produit 64 caracteres hexadecimaux
_HASH_LENGTH = 64
_HEX_CHARS = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class AuthMfaRecoveryCode:
    """Representation Python d'un code de recuperation MFA stockable cote serveur.

    code_hash contient un SHA-256 du code normalise. Le code brut n'est jamais conserve.
    used_at non nul signifie que le code a deja ete consomme.
    """

    id: int | None
    user_id: int
    code_hash: str
    used_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class RecoveryCodesSetup:
    """Resultat de la generation d'un lot de codes de recuperation.

    raw_codes  : codes bruts a afficher une seule fois a l'utilisateur.
    code_records : enregistrements a stocker en base (sans code brut).
    """

    raw_codes: tuple[str, ...]
    code_records: tuple[AuthMfaRecoveryCode, ...]


# ---------------------------------------------------------------------------
# Generation et normalisation
# ---------------------------------------------------------------------------


def generate_recovery_code() -> str:
    """Genere un code de recuperation lisible au format XXXX-XXXX-XXXX-XXXX.

    Utilise secrets.choice sur un alphabet sans caracteres ambigus.
    """
    groups = [
        "".join(secrets.choice(_ALPHABET) for _ in range(_GROUP_SIZE))
        for _ in range(_GROUP_COUNT)
    ]
    return _SEPARATOR.join(groups)


def normalize_recovery_code(code: str) -> str:
    """Normalise un code de recuperation : supprime les espaces et met en majuscules.

    Refuse None, les types non-chaine et les chaines vides.
    """
    if not isinstance(code, str):
        raise InvalidMfaRecoveryCodeError("le code de recuperation doit etre une chaine")
    code = code.strip().upper()
    if not code:
        raise InvalidMfaRecoveryCodeError("le code de recuperation ne peut pas etre vide")
    return code


# ---------------------------------------------------------------------------
# Hash et verification
# ---------------------------------------------------------------------------


def hash_recovery_code(code: str) -> str:
    """Retourne le SHA-256 hexadecimal (64 chars) du code normalise.

    Ne retourne jamais le code brut.
    SHA-256 est approprie ici car les codes sont generes aleatoirement par Forge
    et ont une entropie suffisante (pas besoin d'Argon2id).
    """
    normalized = normalize_recovery_code(code)
    return hashlib.sha256(normalized.encode()).hexdigest()


def verify_recovery_code(code: str, code_hash: str) -> bool:
    """Verifie un code brut contre son hash stocke.

    Retourne False pour toute entree invalide sans lever d'exception.
    Utilise secrets.compare_digest pour eviter les attaques temporelles.
    """
    try:
        if not isinstance(code, str) or not code.strip():
            return False
        if not isinstance(code_hash, str) or len(code_hash) != _HASH_LENGTH:
            return False
        expected = hash_recovery_code(code)
        return secrets.compare_digest(expected, code_hash)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Validation du contrat
# ---------------------------------------------------------------------------


def _validate_code_hash(code_hash: Any) -> None:
    if not isinstance(code_hash, str) or not code_hash:
        raise InvalidMfaRecoveryCodeError("code_hash doit etre une chaine non vide")
    if len(code_hash) != _HASH_LENGTH:
        raise InvalidMfaRecoveryCodeError(
            f"code_hash doit faire {_HASH_LENGTH} caracteres (SHA-256 hex)"
        )
    if not all(c in _HEX_CHARS for c in code_hash):
        raise InvalidMfaRecoveryCodeError("code_hash doit etre une valeur hexadecimale valide")


def validate_recovery_code_contract(data: Any) -> None:
    """Valide le contrat AuthMfaRecoveryCode minimal.

    Accepte un AuthMfaRecoveryCode ou un dict brut. Ne lit pas la base.
    """
    if isinstance(data, AuthMfaRecoveryCode):
        _validate_record_fields(data.id, data.user_id, data.code_hash)
        return

    if not isinstance(data, dict):
        raise InvalidMfaRecoveryCodeError(
            "les donnees doivent etre un AuthMfaRecoveryCode ou un dict"
        )

    missing = sorted(k for k in ("user_id", "code_hash") if k not in data)
    if missing:
        raise InvalidMfaRecoveryCodeError(f"champs obligatoires manquants : {', '.join(missing)}")

    _validate_record_fields(data.get("id"), data["user_id"], data["code_hash"])


def _validate_record_fields(record_id: Any, user_id: Any, code_hash: Any) -> None:
    if record_id is not None:
        if not isinstance(record_id, int) or isinstance(record_id, bool) or record_id <= 0:
            raise InvalidMfaRecoveryCodeError("id doit etre None ou un entier strictement positif")

    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise InvalidMfaRecoveryCodeError("user_id doit etre un entier strictement positif")

    _validate_code_hash(code_hash)


def normalize_recovery_code_record(data: Any) -> AuthMfaRecoveryCode:
    """Valide et normalise un dict brut en AuthMfaRecoveryCode."""
    if isinstance(data, AuthMfaRecoveryCode):
        validate_recovery_code_contract(data)
        return data

    if not isinstance(data, dict):
        raise InvalidMfaRecoveryCodeError(
            "les donnees doivent etre un AuthMfaRecoveryCode ou un dict"
        )

    validate_recovery_code_contract(data)

    return AuthMfaRecoveryCode(
        id=data.get("id"),
        user_id=data["user_id"],
        code_hash=data["code_hash"],
        used_at=data.get("used_at"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


def is_valid_recovery_code_record(record: Any) -> bool:
    """Retourne True si record est un AuthMfaRecoveryCode structurellement valide."""
    try:
        validate_recovery_code_contract(record)
    except InvalidMfaRecoveryCodeError:
        return False
    return isinstance(record, AuthMfaRecoveryCode)


# ---------------------------------------------------------------------------
# Creation et consommation
# ---------------------------------------------------------------------------


def create_recovery_codes(
    user_id: int,
    count: int = 10,
    now: datetime | None = None,
) -> RecoveryCodesSetup:
    """Genere un lot de codes de recuperation MFA sans ecrire en base.

    Retourne RecoveryCodesSetup avec :
    - raw_codes : a afficher une seule fois a l'utilisateur ;
    - code_records : a stocker en base (hashes uniquement, jamais de code brut).
    """
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise InvalidMfaRecoveryCodeError("user_id doit etre un entier strictement positif")
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise InvalidMfaRecoveryCodeError("count doit etre un entier strictement positif")

    ts = now if now is not None else datetime.now(tz=timezone.utc)

    raw_codes = tuple(generate_recovery_code() for _ in range(count))
    code_records = tuple(
        AuthMfaRecoveryCode(
            id=None,
            user_id=user_id,
            code_hash=hash_recovery_code(raw),
            used_at=None,
            created_at=ts,
            updated_at=ts,
        )
        for raw in raw_codes
    )

    return RecoveryCodesSetup(raw_codes=raw_codes, code_records=code_records)


def consume_recovery_code(
    code: str,
    code_record: Any,
    now: datetime | None = None,
) -> AuthMfaRecoveryCode | None:
    """Marque un code de recuperation comme utilise apres verification.

    Retourne un nouveau AuthMfaRecoveryCode immutable avec used_at renseigne.
    Retourne None si le code est invalide, deja utilise ou si le record est invalide.
    Ne modifie pas l'objet original. N'ecrit pas en base.
    """
    try:
        if isinstance(code_record, dict):
            code_record = normalize_recovery_code_record(code_record)
        elif not isinstance(code_record, AuthMfaRecoveryCode):
            return None

        if not is_valid_recovery_code_record(code_record):
            return None

        if code_record.used_at is not None:
            return None

        if not verify_recovery_code(code, code_record.code_hash):
            return None

        ts = now if now is not None else datetime.now(tz=timezone.utc)
        return AuthMfaRecoveryCode(
            id=code_record.id,
            user_id=code_record.user_id,
            code_hash=code_record.code_hash,
            used_at=ts,
            created_at=code_record.created_at,
            updated_at=ts,
        )
    except Exception:
        return None
