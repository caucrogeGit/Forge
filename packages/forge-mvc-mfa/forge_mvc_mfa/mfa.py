# pyright: strict
"""Contrat MFA generique, stockage des facteurs, TOTP, challenge connexion et revalidation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from collections.abc import Callable
from functools import wraps
from typing import Any, cast

import pyotp

from core.auth.exceptions import AuthError, InvalidAuthUserError, InvalidMfaFactorError
from core.sessions.keys import session_get as _session_get
from forge_mvc_mfa.secret_crypto import decrypt_totp_secret, encrypt_totp_secret


MFA_FACTOR_TOTP = "totp"
MFA_FACTOR_RECOVERY = "recovery"

MFA_STATUS_PENDING = "pending"
MFA_STATUS_ACTIVE = "active"
MFA_STATUS_DISABLED = "disabled"

_KNOWN_FACTOR_TYPES = frozenset({MFA_FACTOR_TOTP, MFA_FACTOR_RECOVERY})
_KNOWN_STATUSES = frozenset({MFA_STATUS_PENDING, MFA_STATUS_ACTIVE, MFA_STATUS_DISABLED})



@dataclass(frozen=True)
class AuthMfaFactor:
    """Representation Python minimale d'un facteur MFA stockable cote serveur."""

    id: int | None
    user_id: int
    factor_type: str
    totp_secret: str
    status: str = MFA_STATUS_PENDING
    label: str | None = None
    confirmed_at: datetime | None = None
    last_used_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None



def _validate_fields(
    factor_id: Any,
    user_id: Any,
    factor_type: Any,
    totp_secret: Any,
    status: Any,
) -> None:
    if factor_id is not None:
        if not isinstance(factor_id, int) or isinstance(factor_id, bool) or factor_id <= 0:
            raise InvalidMfaFactorError("id doit etre None ou un entier strictement positif")

    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise InvalidMfaFactorError("user_id doit etre un entier strictement positif")

    if not isinstance(factor_type, str) or not factor_type.strip():
        raise InvalidMfaFactorError("factor_type doit etre une chaine non vide")
    if factor_type not in _KNOWN_FACTOR_TYPES:
        raise InvalidMfaFactorError(
            f"factor_type inconnu : '{factor_type}'. Types reconnus : {sorted(_KNOWN_FACTOR_TYPES)}"
        )

    if not isinstance(totp_secret, str) or not totp_secret:
        raise InvalidMfaFactorError("totp_secret doit etre une chaine non vide")

    if not isinstance(status, str) or not status:
        raise InvalidMfaFactorError("status doit etre une chaine non vide")
    if status not in _KNOWN_STATUSES:
        raise InvalidMfaFactorError(
            f"status inconnu : '{status}'. Statuts reconnus : {sorted(_KNOWN_STATUSES)}"
        )


def _resolve_dict_secret(data: dict[str, Any]) -> Any:
    return data.get("totp_secret")


def validate_mfa_factor_contract(data: Any) -> None:
    """Valide le contrat AuthMfaFactor minimal.

    Accepte un AuthMfaFactor deja construit ou un dict brut. Ne cree aucune
    session et ne lit aucune base de donnees.
    """
    if isinstance(data, AuthMfaFactor):
        _validate_fields(data.id, data.user_id, data.factor_type, data.totp_secret, data.status)
        return

    if not isinstance(data, dict):
        raise InvalidMfaFactorError("les donnees MFA doivent etre un AuthMfaFactor ou un dict")

    data = cast("dict[str, Any]", data)
    totp_secret = _resolve_dict_secret(data)

    missing = sorted(k for k in ("user_id", "factor_type", "status") if k not in data)
    if totp_secret is None:
        missing = sorted(missing + ["totp_secret"])
    if missing:
        raise InvalidMfaFactorError(f"champs obligatoires manquants : {', '.join(missing)}")

    _validate_fields(
        data.get("id"),
        data["user_id"],
        data["factor_type"],
        totp_secret,
        data["status"],
    )


def normalize_mfa_factor(data: Any) -> AuthMfaFactor:
    """Valide et normalise un dict brut en AuthMfaFactor."""
    if isinstance(data, AuthMfaFactor):
        validate_mfa_factor_contract(data)
        return data

    if not isinstance(data, dict):
        raise InvalidMfaFactorError("les donnees MFA doivent etre un AuthMfaFactor ou un dict")

    data = cast("dict[str, Any]", data)
    totp_secret = _resolve_dict_secret(data)

    missing = sorted(k for k in ("user_id", "factor_type", "status") if k not in data)
    if totp_secret is None:
        missing = sorted(missing + ["totp_secret"])
    if missing:
        raise InvalidMfaFactorError(f"champs obligatoires manquants : {', '.join(missing)}")

    _validate_fields(data.get("id"), data["user_id"], data["factor_type"], totp_secret, data["status"])

    return AuthMfaFactor(
        id=data.get("id"),
        user_id=data["user_id"],
        factor_type=data["factor_type"],
        totp_secret=cast("str", totp_secret),
        status=data.get("status", MFA_STATUS_PENDING),
        label=data.get("label"),
        confirmed_at=data.get("confirmed_at"),
        last_used_at=data.get("last_used_at"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


def is_valid_mfa_factor(factor: Any) -> bool:
    """Retourne True si factor est un AuthMfaFactor structurellement valide."""
    try:
        validate_mfa_factor_contract(factor)
    except InvalidMfaFactorError:
        return False
    return isinstance(factor, AuthMfaFactor)


def is_mfa_factor_active(factor: Any) -> bool:
    """Retourne True si le facteur a le statut active."""
    try:
        if isinstance(factor, AuthMfaFactor):
            return factor.status == MFA_STATUS_ACTIVE
        if isinstance(factor, dict):
            return cast("dict[str, Any]", factor).get("status") == MFA_STATUS_ACTIVE
    except Exception:
        pass
    return False


def is_mfa_enabled(factors: Any) -> bool:
    """Retourne True si au moins un facteur de la liste est actif.

    Ne fait aucun acces base de donnees. Ignore proprement les elements invalides.
    """
    try:
        for factor in factors:
            try:
                if is_mfa_factor_active(factor):
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# TOTP
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TotpSetup:
    """Resultat de la creation d'un facteur TOTP.

    secret   : secret base32 brut a afficher une fois ou utiliser pour generer un QR.
    factor   : AuthMfaFactor en statut pending pret a etre stocke.
               factor.totp_secret est chiffre (prefixe "enc:") via FORGE_MFA_SECRET_KEY.
    provisioning_uri : URI otpauth:// a passer a l'application d'authentification.
    """

    secret: str
    factor: AuthMfaFactor
    provisioning_uri: str


def generate_totp_secret() -> str:
    """Genere un secret TOTP base32 cryptographiquement sur."""
    return pyotp.random_base32()


def totp_provisioning_uri(
    secret: str,
    account_name: str,
    issuer_name: str = "Forge",
) -> str:
    """Construit une URI otpauth://totp/ compatible avec les applications d'authentification.

    Refuse secret, account_name ou issuer_name vides.
    """
    if not isinstance(secret, str) or not secret:  # pyright: ignore[reportUnnecessaryIsInstance]
        raise ValueError("secret doit etre une chaine non vide")
    if not isinstance(account_name, str) or not account_name:  # pyright: ignore[reportUnnecessaryIsInstance]
        raise ValueError("account_name doit etre une chaine non vide")
    if not isinstance(issuer_name, str) or not issuer_name:  # pyright: ignore[reportUnnecessaryIsInstance]
        raise ValueError("issuer_name doit etre une chaine non vide")

    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=account_name, issuer_name=issuer_name)


def create_totp_factor(
    user_id: int,
    label: str | None = None,
    issuer_name: str = "Forge",
    account_name: str | None = None,
    now: datetime | None = None,
) -> TotpSetup:
    """Cree un facteur TOTP pending sans ecrire en base.

    Retourne un TotpSetup contenant :
    - le secret brut (a montrer une seule fois a l'utilisateur) ;
    - un AuthMfaFactor en statut pending pret au stockage ;
    - l'URI otpauth:// de provisioning.
    """
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:  # pyright: ignore[reportUnnecessaryIsInstance]
        raise InvalidMfaFactorError("user_id doit etre un entier strictement positif")

    ts = now if now is not None else datetime.now(tz=timezone.utc)
    secret = generate_totp_secret()
    effective_account = account_name if account_name else str(user_id)

    factor = AuthMfaFactor(
        id=None,
        user_id=user_id,
        factor_type=MFA_FACTOR_TOTP,
        totp_secret=encrypt_totp_secret(secret),
        status=MFA_STATUS_PENDING,
        label=label,
        confirmed_at=None,
        last_used_at=None,
        created_at=ts,
        updated_at=ts,
    )
    uri = totp_provisioning_uri(secret, effective_account, issuer_name)
    return TotpSetup(secret=secret, factor=factor, provisioning_uri=uri)


def verify_totp_code(
    secret: str,
    code: str,
    valid_window: int = 1,
    now: datetime | None = None,
) -> bool:
    """Verifie un code TOTP.

    Retourne False pour toute entree invalide sans lever d'exception.
    valid_window : nombre de periodes de tolerance de chaque cote de la periode courante.
    """
    try:
        if not isinstance(secret, str) or not secret:  # pyright: ignore[reportUnnecessaryIsInstance]
            return False
        if not isinstance(code, str) or not code:  # pyright: ignore[reportUnnecessaryIsInstance]
            return False
        if not isinstance(valid_window, int) or isinstance(valid_window, bool) or valid_window < 0:  # pyright: ignore[reportUnnecessaryIsInstance]
            return False

        totp = pyotp.TOTP(secret)
        if now is not None:
            for_time = now.timestamp() if hasattr(now, "timestamp") else None
            return totp.verify(code, valid_window=valid_window, for_time=for_time)  # pyright: ignore[reportArgumentType]
        return totp.verify(code, valid_window=valid_window)
    except Exception:
        return False


def confirm_totp_factor(
    factor: Any,
    code: str,
    now: datetime | None = None,
) -> AuthMfaFactor | None:
    """Confirme un facteur TOTP pending apres verification du code.

    Retourne un nouveau AuthMfaFactor avec status=active et confirmed_at renseigne.
    Retourne None si le code est invalide, le facteur incorrect ou deja actif.
    Ne modifie pas l'objet original. Ne touche pas la base.
    """
    try:
        if isinstance(factor, dict):
            factor = normalize_mfa_factor(factor)
        elif not isinstance(factor, AuthMfaFactor):
            return None

        if not is_valid_mfa_factor(factor):
            return None
        if factor.factor_type != MFA_FACTOR_TOTP:
            return None
        if factor.status != MFA_STATUS_PENDING:
            return None

        raw_secret = decrypt_totp_secret(factor.totp_secret)
        if not verify_totp_code(raw_secret, code, now=now):
            return None

        ts = now if now is not None else datetime.now(tz=timezone.utc)
        return AuthMfaFactor(
            id=factor.id,
            user_id=factor.user_id,
            factor_type=factor.factor_type,
            totp_secret=factor.totp_secret,
            status=MFA_STATUS_ACTIVE,
            label=factor.label,
            confirmed_at=ts,
            last_used_at=factor.last_used_at,
            created_at=factor.created_at,
            updated_at=ts,
        )
    except Exception:
        return None


# ---------------------------------------------------------------------------
# MFA Challenge (AUTH-MFA-004)
# ---------------------------------------------------------------------------


MFA_CHALLENGE_USER_ID_KEY = "_auth_mfa_user_id"
MFA_CHALLENGE_STARTED_AT_KEY = "_auth_mfa_started_at"

MFA_CHALLENGE_MAX_ATTEMPTS = 5
MFA_CHALLENGE_WINDOW_SECONDS = 300

MFA_REVALIDATION_MAX_ATTEMPTS = 3
MFA_REVALIDATION_WINDOW_SECONDS = 300


@dataclass(frozen=True)
class MfaChallengeResult:
    """Resultat d'un challenge MFA verifie avec succes.

    method est "totp" ou "recovery".
    factor est renseigne pour TOTP, recovery_code pour un code consomme.
    Aucun code brut ni secret brut n'est contenu dans ce resultat.
    L'application est responsable de persister last_used_at ou used_at.
    """

    user_id: int
    method: str
    verified_at: datetime
    factor: AuthMfaFactor | None = None
    recovery_code: Any = None  # AuthMfaRecoveryCode | None


def _session_user_matches(request: Any, expected_user_id: int) -> bool:
    """Retourne True si la session courante est authentifiee pour expected_user_id.

    Criteres : session existante, authentifie=True, utilisateur["id"] == expected_user_id.
    Retourne False sans lever d'exception.
    """
    if not isinstance(expected_user_id, int) or isinstance(expected_user_id, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
        return False
    if expected_user_id <= 0:
        return False
    session = _resolve_mfa_session(request)
    if session is None:
        return False
    if not _session_get(session, "authenticated"):
        return False
    user: object = _session_get(session, "user") or {}
    if not isinstance(user, dict):
        return False
    session_user_id = cast("dict[str, Any]", user).get("id")
    if not isinstance(session_user_id, int) or isinstance(session_user_id, bool):
        return False
    return session_user_id == expected_user_id


def _resolve_mfa_session(request: Any) -> "dict[str, Any] | None":
    session = getattr(request, "session", None)
    if isinstance(session, dict):
        return cast("dict[str, Any]", session)
    try:
        from core.security.session import get_session_id
        from core.sessions.manager import get_session_store

        session_id = get_session_id(request)
        return get_session_store().get(session_id) if session_id else None
    except Exception:
        return None


def _persist_session_changes(
    request: Any,
    *,
    set_keys: "dict[str, Any] | None" = None,
    unset_keys: "list[str] | None" = None,
) -> None:
    """Persiste des modifications de session de facon compatible avec tous les backends.

    Pour les backends File et MariaDB, store.get() retourne une copie deserialisee ;
    les mutations en place sont silencieusement perdues. Ce helper effectue un cycle
    read-modify-write explicite sur le store pour garantir la persistence.
    """
    raw_session = getattr(request, "session", None)
    if isinstance(raw_session, dict):
        mutable_session = cast("dict[str, Any]", raw_session)
        if set_keys:
            mutable_session.update(set_keys)
        if unset_keys:
            for k in unset_keys:
                mutable_session.pop(k, None)
        return

    try:
        from core.security.session import get_session_id
        from core.sessions.manager import get_session_store

        session_id = get_session_id(request)
        if not session_id:
            return
        store = get_session_store()
        data = store.get(session_id)
        if data is None:
            return
        if set_keys:
            data.update(set_keys)
        if unset_keys:
            for k in unset_keys:
                data.pop(k, None)
        store.replace(session_id, data)
    except Exception:
        pass


def start_mfa_challenge(
    request: Any,
    user: Any,
    now: datetime | None = None,
) -> None:
    """Demarre un challenge MFA temporaire en session apres authentification primaire.

    Accepte un AuthUser ou un dict normalisable. Refuse utilisateur invalide ou inactif.
    Stocke uniquement user.id et un timestamp ISO. Ne connecte pas l'utilisateur.
    Ne modifie pas la base de donnees.
    """
    from core.auth.user import AuthUser, normalize_auth_user, validate_auth_user_contract

    session = _resolve_mfa_session(request)
    if session is None:
        raise AuthError("session introuvable")

    if isinstance(user, dict):
        user = normalize_auth_user(user)
    elif not isinstance(user, AuthUser):
        raise InvalidAuthUserError("user doit etre un AuthUser ou un dict normalisable")

    validate_auth_user_contract(user)

    if not user.is_active:
        raise InvalidAuthUserError(
            "impossible de demarrer un challenge MFA pour un utilisateur inactif"
        )

    ts = now if now is not None else datetime.now(tz=timezone.utc)
    _persist_session_changes(request, set_keys={
        MFA_CHALLENGE_USER_ID_KEY: user.id,
        MFA_CHALLENGE_STARTED_AT_KEY: ts.isoformat(),
    })


def get_mfa_challenge_user_id(request: Any) -> int | None:
    """Retourne l'id utilisateur du challenge MFA en attente, ou None.

    Ne charge pas l'utilisateur. N'acced`de pas a la base.
    """
    session = _resolve_mfa_session(request)
    if session is None:
        return None
    user_id = session.get(MFA_CHALLENGE_USER_ID_KEY)
    if isinstance(user_id, int) and not isinstance(user_id, bool) and user_id > 0:
        return user_id
    return None


def has_pending_mfa_challenge(
    request: Any,
    max_age_minutes: int = 10,
    now: datetime | None = None,
) -> bool:
    """Retourne True si un challenge MFA est en attente et non expire.

    Utilise max_age_minutes (defaut 10). Accepte now pour les tests.
    Ne modifie pas la session.
    """
    if not isinstance(max_age_minutes, int) or isinstance(max_age_minutes, bool) or max_age_minutes <= 0:  # pyright: ignore[reportUnnecessaryIsInstance]
        return False

    session = _resolve_mfa_session(request)
    if session is None:
        return False

    user_id = session.get(MFA_CHALLENGE_USER_ID_KEY)
    if not (isinstance(user_id, int) and not isinstance(user_id, bool) and user_id > 0):
        return False

    started_at_raw = session.get(MFA_CHALLENGE_STARTED_AT_KEY)
    if not isinstance(started_at_raw, str):
        return False

    try:
        started_at = datetime.fromisoformat(started_at_raw)
    except (ValueError, TypeError):
        return False

    current = now if now is not None else datetime.now(tz=timezone.utc)

    if started_at.tzinfo is None and current.tzinfo is not None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    elif started_at.tzinfo is not None and current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    elapsed = (current - started_at).total_seconds()
    return 0 <= elapsed <= max_age_minutes * 60


def clear_mfa_challenge(request: Any) -> None:
    """Supprime les cles MFA du challenge en session. Idempotent.

    Preserve flash, CSRF et toutes les autres cles de session.
    """
    _persist_session_changes(
        request,
        unset_keys=[MFA_CHALLENGE_USER_ID_KEY, MFA_CHALLENGE_STARTED_AT_KEY],
    )


def verify_mfa_challenge(
    request: Any,
    code: str,
    factors: Any,
    recovery_codes: Any = None,
    max_age_minutes: int = 10,
    now: datetime | None = None,
) -> MfaChallengeResult | None:
    """Verifie un code TOTP ou de recuperation contre le challenge MFA en session.

    Tente d'abord les facteurs TOTP actifs de l'utilisateur, puis les codes de
    recuperation si recovery_codes est fourni.

    Retourne MfaChallengeResult apres succes et nettoie le challenge de session.
    Retourne None sans exception en cas d'echec. Ne nettoie pas sur echec non expire.
    Ne connecte pas l'utilisateur. N'ecrit pas en base.
    """
    from core.auth import rate_limit as _rl
    from forge_mvc_mfa import totp_replay as _replay
    from core.auth.audit import AUTH_EVENT_MFA_RATE_LIMITED
    from forge_mvc_mfa.recovery import AuthMfaRecoveryCode, consume_recovery_code, normalize_recovery_code_record

    if not isinstance(code, str) or not code.strip():  # pyright: ignore[reportUnnecessaryIsInstance]
        return None

    user_id = get_mfa_challenge_user_id(request)
    if user_id is None:
        return None

    if not has_pending_mfa_challenge(request, max_age_minutes=max_age_minutes, now=now):
        clear_mfa_challenge(request)
        return None

    rl_action = _rl.AUTH_RATE_LIMIT_MFA_CHALLENGE
    rl_key = f"user:{user_id}"

    if _rl.is_locked_out(
        rl_action, rl_key,
        max_attempts=MFA_CHALLENGE_MAX_ATTEMPTS,
        window_seconds=MFA_CHALLENGE_WINDOW_SECONDS,
        now=now,
    ):
        from core.auth.audit import safe_log_auth_event
        safe_log_auth_event(
            AUTH_EVENT_MFA_RATE_LIMITED,
            user_id=user_id,
            metadata={"endpoint": "challenge"},
        )
        return None

    ts = now if now is not None else datetime.now(tz=timezone.utc)
    current_step = _replay.step_for_time(ts.timestamp())

    try:
        for raw_factor in factors:
            try:
                factor = raw_factor
                if isinstance(factor, dict):
                    factor = normalize_mfa_factor(factor)
                if not isinstance(factor, AuthMfaFactor):
                    continue
                if factor.factor_type != MFA_FACTOR_TOTP:
                    continue
                if factor.status != MFA_STATUS_ACTIVE:
                    continue
                if factor.user_id != user_id:
                    continue
                if factor.id is not None and _replay.is_replay(factor.id, current_step):
                    continue
                raw_secret = decrypt_totp_secret(factor.totp_secret)
                if verify_totp_code(raw_secret, code, now=now):
                    if factor.id is not None and not _replay.check_and_record(
                        factor.id, current_step
                    ):
                        # Course anti-replay perdue : code déjà consommé par
                        # une requête concurrente sur la même step.
                        continue
                    updated_factor = AuthMfaFactor(
                        id=factor.id,
                        user_id=factor.user_id,
                        factor_type=factor.factor_type,
                        totp_secret=factor.totp_secret,
                        status=factor.status,
                        label=factor.label,
                        confirmed_at=factor.confirmed_at,
                        last_used_at=ts,
                        created_at=factor.created_at,
                        updated_at=ts,
                    )
                    _rl.clear_attempts(rl_action, rl_key)
                    clear_mfa_challenge(request)
                    return MfaChallengeResult(
                        user_id=user_id,
                        method=MFA_FACTOR_TOTP,
                        verified_at=ts,
                        factor=updated_factor,
                    )
            except Exception:
                continue
    except Exception:
        pass

    if recovery_codes is not None:
        try:
            for raw_rc in recovery_codes:
                try:
                    rc = raw_rc
                    if isinstance(rc, dict):
                        rc = normalize_recovery_code_record(rc)
                    if not isinstance(rc, AuthMfaRecoveryCode):
                        continue
                    if rc.user_id != user_id:
                        continue
                    consumed = consume_recovery_code(code, rc, now=now)
                    if consumed is not None:
                        _rl.clear_attempts(rl_action, rl_key)
                        clear_mfa_challenge(request)
                        return MfaChallengeResult(
                            user_id=user_id,
                            method=MFA_FACTOR_RECOVERY,
                            verified_at=ts,
                            recovery_code=consumed,
                        )
                except Exception:
                    continue
        except Exception:
            pass

    _rl.record_attempt(rl_action, rl_key, user_id=user_id, now=now if now is not None else datetime.now(tz=timezone.utc))
    return None


# ---------------------------------------------------------------------------
# MFA Revalidation (AUTH-MFA-005)
# ---------------------------------------------------------------------------


MFA_REVALIDATION_USER_ID_KEY = "_auth_mfa_revalidated_user_id"
MFA_REVALIDATION_AT_KEY = "_auth_mfa_revalidated_at"


@dataclass(frozen=True)
class MfaRevalidationResult:
    """Resultat d'une revalidation MFA pour action sensible.

    method est "totp" ou "recovery".
    factor est renseigne pour TOTP, recovery_code pour un code consomme.
    Aucun code brut ni secret brut n'est contenu dans ce resultat.
    L'application est responsable de persister last_used_at ou used_at.
    """

    user_id: int
    method: str
    verified_at: datetime
    factor: AuthMfaFactor | None = None
    recovery_code: Any = None  # AuthMfaRecoveryCode | None


def mark_mfa_revalidated(
    request: Any,
    user_id: int,
    now: datetime | None = None,
) -> None:
    """Stocke en session une preuve de revalidation MFA recente.

    user_id doit etre un entier strictement positif. Ne connecte pas l'utilisateur.
    Ne modifie pas la base de donnees.
    """
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:  # pyright: ignore[reportUnnecessaryIsInstance]
        raise InvalidMfaFactorError("user_id doit etre un entier strictement positif")

    if not _session_user_matches(request, user_id):
        return

    ts = now if now is not None else datetime.now(tz=timezone.utc)
    _persist_session_changes(request, set_keys={
        MFA_REVALIDATION_USER_ID_KEY: user_id,
        MFA_REVALIDATION_AT_KEY: ts.isoformat(),
    })


def get_mfa_revalidated_user_id(request: Any) -> int | None:
    """Retourne l'id utilisateur de la revalidation MFA en session, ou None.

    Ne charge pas l'utilisateur. N'acced`de pas a la base.
    """
    session = _resolve_mfa_session(request)
    if session is None:
        return None
    user_id = session.get(MFA_REVALIDATION_USER_ID_KEY)
    if isinstance(user_id, int) and not isinstance(user_id, bool) and user_id > 0:
        return user_id
    return None


def has_recent_mfa_revalidation(
    request: Any,
    user_id: int,
    max_age_minutes: int = 10,
    now: datetime | None = None,
) -> bool:
    """Retourne True si une revalidation MFA recente et valide existe pour user_id.

    Verifie que la session contient une revalidation, que user_id correspond et
    que la revalidation n'est pas expiree. Ne modifie pas la session.
    """
    if not isinstance(max_age_minutes, int) or isinstance(max_age_minutes, bool) or max_age_minutes <= 0:  # pyright: ignore[reportUnnecessaryIsInstance]
        return False

    session = _resolve_mfa_session(request)
    if session is None:
        return False

    stored_uid = session.get(MFA_REVALIDATION_USER_ID_KEY)
    if not (isinstance(stored_uid, int) and not isinstance(stored_uid, bool) and stored_uid > 0):
        return False

    if stored_uid != user_id:
        return False

    revalidated_at_raw = session.get(MFA_REVALIDATION_AT_KEY)
    if not isinstance(revalidated_at_raw, str):
        return False

    try:
        revalidated_at = datetime.fromisoformat(revalidated_at_raw)
    except (ValueError, TypeError):
        return False

    current = now if now is not None else datetime.now(tz=timezone.utc)

    if revalidated_at.tzinfo is None and current.tzinfo is not None:
        revalidated_at = revalidated_at.replace(tzinfo=timezone.utc)
    elif revalidated_at.tzinfo is not None and current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    elapsed = (current - revalidated_at).total_seconds()
    return 0 <= elapsed <= max_age_minutes * 60


def clear_mfa_revalidation(request: Any) -> None:
    """Supprime uniquement les cles de revalidation MFA. Idempotent.

    Preserve _auth_user_id, les cles de challenge MFA, flash, CSRF et toutes
    les autres cles de session.
    """
    _persist_session_changes(
        request,
        unset_keys=[MFA_REVALIDATION_USER_ID_KEY, MFA_REVALIDATION_AT_KEY],
    )


def verify_mfa_revalidation(
    request: Any,
    user_id: int,
    code: str,
    factors: Any,
    recovery_codes: Any = None,
    max_age_minutes: int = 10,
    now: datetime | None = None,
) -> MfaRevalidationResult | None:
    """Verifie un code TOTP ou de recuperation pour revalider l'acces a une action sensible.

    Tente d'abord les facteurs TOTP actifs, puis les recovery_codes si fournis.
    Apres succes, appelle mark_mfa_revalidated pour stocker la preuve en session.
    Retourne MfaRevalidationResult en cas de succes, None en cas d'echec.
    Ne connecte pas l'utilisateur. N'ecrit pas en base.
    """
    from core.auth import rate_limit as _rl
    from forge_mvc_mfa import totp_replay as _replay
    from core.auth.audit import AUTH_EVENT_MFA_RATE_LIMITED
    from forge_mvc_mfa.recovery import AuthMfaRecoveryCode, consume_recovery_code, normalize_recovery_code_record

    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:  # pyright: ignore[reportUnnecessaryIsInstance]
        return None

    if not isinstance(code, str) or not code.strip():  # pyright: ignore[reportUnnecessaryIsInstance]
        return None

    if not _session_user_matches(request, user_id):
        from core.auth.audit import AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH, safe_log_auth_event
        safe_log_auth_event(
            AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH,
            user_id=user_id,
            ip_address=getattr(request, "ip", None),
            metadata={"reason": "session_user_does_not_match_revalidation_user_id"},
        )
        return None

    rl_action = _rl.AUTH_RATE_LIMIT_MFA_REVALIDATION
    rl_key = f"user:{user_id}"

    if _rl.is_locked_out(
        rl_action, rl_key,
        max_attempts=MFA_REVALIDATION_MAX_ATTEMPTS,
        window_seconds=MFA_REVALIDATION_WINDOW_SECONDS,
        now=now,
    ):
        from core.auth.audit import safe_log_auth_event
        safe_log_auth_event(
            AUTH_EVENT_MFA_RATE_LIMITED,
            user_id=user_id,
            metadata={"endpoint": "revalidation"},
        )
        return None

    ts = now if now is not None else datetime.now(tz=timezone.utc)
    current_step = _replay.step_for_time(ts.timestamp())

    try:
        for raw_factor in factors:
            try:
                factor = raw_factor
                if isinstance(factor, dict):
                    factor = normalize_mfa_factor(factor)
                if not isinstance(factor, AuthMfaFactor):
                    continue
                if factor.factor_type != MFA_FACTOR_TOTP:
                    continue
                if factor.status != MFA_STATUS_ACTIVE:
                    continue
                if factor.user_id != user_id:
                    continue
                if factor.id is not None and _replay.is_replay(factor.id, current_step):
                    continue
                raw_secret = decrypt_totp_secret(factor.totp_secret)
                if verify_totp_code(raw_secret, code, now=now):
                    if factor.id is not None and not _replay.check_and_record(
                        factor.id, current_step
                    ):
                        # Course anti-replay perdue : code déjà consommé par
                        # une requête concurrente sur la même step.
                        continue
                    updated_factor = AuthMfaFactor(
                        id=factor.id,
                        user_id=factor.user_id,
                        factor_type=factor.factor_type,
                        totp_secret=factor.totp_secret,
                        status=factor.status,
                        label=factor.label,
                        confirmed_at=factor.confirmed_at,
                        last_used_at=ts,
                        created_at=factor.created_at,
                        updated_at=ts,
                    )
                    _rl.clear_attempts(rl_action, rl_key)
                    mark_mfa_revalidated(request, user_id, now=ts)
                    return MfaRevalidationResult(
                        user_id=user_id,
                        method=MFA_FACTOR_TOTP,
                        verified_at=ts,
                        factor=updated_factor,
                    )
            except Exception:
                continue
    except Exception:
        pass

    if recovery_codes is not None:
        try:
            for raw_rc in recovery_codes:
                try:
                    rc = raw_rc
                    if isinstance(rc, dict):
                        rc = normalize_recovery_code_record(rc)
                    if not isinstance(rc, AuthMfaRecoveryCode):
                        continue
                    if rc.user_id != user_id:
                        continue
                    consumed = consume_recovery_code(code, rc, now=now)
                    if consumed is not None:
                        _rl.clear_attempts(rl_action, rl_key)
                        mark_mfa_revalidated(request, user_id, now=ts)
                        return MfaRevalidationResult(
                            user_id=user_id,
                            method=MFA_FACTOR_RECOVERY,
                            verified_at=ts,
                            recovery_code=consumed,
                        )
                except Exception:
                    continue
        except Exception:
            pass

    _rl.record_attempt(rl_action, rl_key, user_id=user_id, now=now if now is not None else datetime.now(tz=timezone.utc))
    return None


def require_recent_mfa(
    func: Callable[..., Any] | None = None, *, max_age_minutes: int = 10
) -> Any:
    """Protege une action sensible en verifiant qu'une revalidation MFA recente existe.

    Extrait user_id depuis la session auth. Retourne 403 si absente ou expiree.
    Ne lance pas de challenge automatique. Ne cree pas de route.
    """
    from core.auth.session import get_authenticated_user_id
    from core.http.response import Response

    def decorator(wrapped: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(wrapped)
        def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            uid = get_authenticated_user_id(request)
            if uid is None or not has_recent_mfa_revalidation(
                request, uid, max_age_minutes=max_age_minutes
            ):
                return Response(
                    403,
                    body=b"MFA revalidation required",
                    content_type="text/plain; charset=utf-8",
                )
            return wrapped(request, *args, **kwargs)

        return wrapper

    if func is None:
        return decorator
    return decorator(func)
