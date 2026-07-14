# pyright: strict
"""Commandes CLI Auth/User de Forge.

forge auth:init — crée le SQL optionnel des tables users, auth_tokens, auth_mfa_factors, auth_mfa_recovery_codes, user_roles, auth_audit_log et auth_rate_limit_attempts
forge auth:list-sql — liste les fichiers SQL optionnels Auth/User connus
forge auth:status — affiche l'etat fonctionnel du socle Auth/User
forge auth:doctor — diagnostique le socle Auth/User sans acces base
forge auth:user:create — cree un utilisateur local
forge auth:user:list — liste les utilisateurs locaux sans secret
forge auth:user:show — affiche un utilisateur local sans secret
forge auth:user:disable — desactive un utilisateur local
forge auth:user:enable — reactive un utilisateur local
forge auth:user:password — change le mot de passe d'un utilisateur local
forge auth:user:role:add — attribue un role RBAC existant a un utilisateur
forge auth:user:role:remove — retire un role RBAC existant a un utilisateur
forge auth:user:roles — liste les roles RBAC attribues a un utilisateur
"""

from __future__ import annotations

import argparse
import getpass
from dataclasses import dataclass
import importlib
import importlib.util
import sys
from pathlib import Path
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal

import cli._support.output as out

if TYPE_CHECKING:
    from core.database.backend import Dialect


_SQL_DIR = Path("mvc") / "models" / "sql"


@dataclass(frozen=True)
class AuthSqlFile:
    filename: str
    label: str
    optional: bool = True


@dataclass(frozen=True)
class AuthCliCheck:
    status: Literal["ok", "warn", "fail"]
    label: str
    detail: str = ""


class AuthAdminCliError(RuntimeError):
    """Erreur lisible pour les commandes admin Auth/User."""

    def __init__(self, message: str, conseil: str = "") -> None:
        super().__init__(message)
        self.conseil = conseil


DbFetchOne = Callable[[str, "tuple[Any, ...]"], "dict[str, Any] | None"]
DbFetchAll = Callable[[str, "tuple[Any, ...]"], "list[dict[str, Any]]"]
DbInsert = Callable[[str, "tuple[Any, ...]"], int]
DbExecute = Callable[[str, "tuple[Any, ...]"], int]


AUTH_SQL_FILES = (
    AuthSqlFile("users.sql", "users"),
    AuthSqlFile("auth_tokens.sql", "tokens"),
    AuthSqlFile("auth_mfa_factors.sql", "MFA factors"),
    AuthSqlFile("auth_mfa_recovery_codes.sql", "MFA recovery codes"),
    AuthSqlFile("user_roles.sql", "pont Auth/User -> RBAC"),
    AuthSqlFile("auth_audit_log.sql", "audit Auth/User"),
    AuthSqlFile("auth_rate_limit_attempts.sql", "rate limit Auth/User"),
)


AUTH_MODULES = (
    "core.auth.user",
    "core.auth.session",
    "core.auth.tokens",
    "core.auth.reset",
    "forge_mvc_mfa",
    "forge_mvc_mfa.recovery",
    "forge_mvc_rbac",
    "core.auth.audit",
    "core.auth.rate_limit",
)


AUTH_CONTRACTS = (
    ("core.auth.user", "AuthUser"),
    ("core.auth.session", "login_user"),
    ("core.auth.tokens", "AuthToken"),
    ("core.auth.reset", "PasswordResetRequest"),
    ("forge_mvc_mfa", "AuthMfaFactor"),
    ("forge_mvc_mfa", "AuthMfaRecoveryCode"),
    ("forge_mvc_rbac", "AuthUserRole"),
    ("forge_mvc_rbac", "user_has_permission"),
    ("forge_mvc_rbac", "make_auth_jinja_context"),
    ("core.auth.audit", "AuthAuditEvent"),
    ("core.auth.rate_limit", "AuthRateLimitAttempt"),
)


RBAC_CONTRACTS = (
    ("forge_mvc_rbac", "Role"),
    ("forge_mvc_rbac", "Permission"),
    ("forge_mvc_rbac", "require_permission"),
    ("forge_mvc_rbac", "make_can"),
)


AUTH_FEATURES = (
    ("users", "core.auth.user", "AuthUser", "users.sql"),
    ("sessions", "core.auth.session", "login_user", None),
    ("tokens", "core.auth.tokens", "AuthToken", "auth_tokens.sql"),
    ("reset password", "core.auth.reset", "PasswordResetRequest", None),
    ("MFA", "forge_mvc_mfa", "AuthMfaFactor", "auth_mfa_factors.sql"),
    ("user_roles", "forge_mvc_rbac", "AuthUserRole", "user_roles.sql"),
    ("Jinja helpers", "forge_mvc_rbac", "make_auth_jinja_context", None),
    ("audit Auth/User", "core.auth.audit", "AuthAuditEvent", "auth_audit_log.sql"),
    ("rate limit Auth/User", "core.auth.rate_limit", "AuthRateLimitAttempt", "auth_rate_limit_attempts.sql"),
)

USERS_SQL = """\
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified_at DATETIME NULL,
    last_login_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


def _write_if_new(path: Path, content: str) -> None:
    if path.exists():
        print(out.preserved(path.as_posix(), "← fichier existant, non touché"))
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(out.created(path.as_posix()))


AUTH_TOKENS_SQL = """\
CREATE TABLE IF NOT EXISTS auth_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    purpose VARCHAR(80) NOT NULL,
    token_hash CHAR(64) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    used_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_auth_tokens_user_purpose (user_id, purpose),
    INDEX idx_auth_tokens_expires_at (expires_at),
    CONSTRAINT fk_auth_tokens_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


AUTH_MFA_FACTORS_SQL = """\
CREATE TABLE IF NOT EXISTS auth_mfa_factors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    factor_type VARCHAR(40) NOT NULL,
    totp_secret VARCHAR(255) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'pending',
    label VARCHAR(120) NULL,
    confirmed_at DATETIME NULL,
    last_used_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_auth_mfa_factors_user_id (user_id),
    INDEX idx_auth_mfa_factors_user_status (user_id, status),
    CONSTRAINT fk_auth_mfa_factors_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


AUTH_MFA_RECOVERY_CODES_SQL = """\
CREATE TABLE IF NOT EXISTS auth_mfa_recovery_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    code_hash CHAR(64) NOT NULL UNIQUE,
    used_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_auth_mfa_recovery_codes_user_id (user_id),
    INDEX idx_auth_mfa_recovery_codes_used_at (used_at),
    CONSTRAINT fk_auth_mfa_recovery_codes_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


USER_ROLES_SQL = """\
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    INDEX idx_user_roles_user_id (user_id),
    INDEX idx_user_roles_role_id (role_id),
    CONSTRAINT fk_user_roles_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_role_id
        FOREIGN KEY (role_id)
        REFERENCES roles(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


AUTH_AUDIT_LOG_SQL = """\
CREATE TABLE IF NOT EXISTS auth_audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(120) NOT NULL,
    user_id INT NULL,
    actor_user_id INT NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(255) NULL,
    metadata_json TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_auth_audit_log_event_type (event_type),
    INDEX idx_auth_audit_log_user_id (user_id),
    INDEX idx_auth_audit_log_actor_user_id (actor_user_id),
    INDEX idx_auth_audit_log_created_at (created_at),
    CONSTRAINT fk_auth_audit_log_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL,
    CONSTRAINT fk_auth_audit_log_actor_user_id
        FOREIGN KEY (actor_user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


AUTH_RATE_LIMIT_ATTEMPTS_SQL = """\
CREATE TABLE IF NOT EXISTS auth_rate_limit_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(120) NOT NULL,
    rate_key VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NULL,
    user_id INT NULL,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_auth_rate_limit_action_key (action, rate_key),
    INDEX idx_auth_rate_limit_created_at (created_at),
    INDEX idx_auth_rate_limit_user_id (user_id),
    CONSTRAINT fk_auth_rate_limit_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


def _auth_init_dialect() -> "Dialect":
    """Dialecte du backend BDD actif, ou refus explicite (ADR-084).

    Le DDL du socle Auth/User est rendu par le dialecte du backend installé :
    sans backend résolu, la commande refuse plutôt que d'émettre du SQL d'un
    autre dialecte.
    """
    from core.database.backend import get_backend

    try:
        return get_backend().dialect
    except RuntimeError as error:
        raise SystemExit(
            "forge auth:init : aucun backend BDD résolu.\n"
            f"Cause : {error}\n"
            "ADR-084 : le SQL du socle Auth/User est rendu dans le dialecte du "
            "backend actif ; installez un backend de niveau plein "
            "(forge-mvc-mariadb ou forge-mvc-sqlite), ou fixez DB_BACKEND."
        ) from error


def cmd_auth_init(args: list[str], root: Path | None = None) -> None:
    if args:
        raise SystemExit("Usage : forge auth:init")

    from cli.security.auth_sql import render_auth_sql

    # ADR-084 : le DDL est rendu par le dialecte du backend BDD actif (MariaDB
    # reproduit les constantes canoniques ci-dessus à l'identique, parité testée).
    dialect = _auth_init_dialect()

    root = root or Path.cwd()
    sql_dir = root / _SQL_DIR
    sql_dir.mkdir(parents=True, exist_ok=True)

    # Socle de base : ne dépend que du cœur (core.auth), toujours applicable seul.
    _write_if_new(sql_dir / "users.sql", render_auth_sql("users", dialect))
    _write_if_new(sql_dir / "auth_tokens.sql", render_auth_sql("auth_tokens", dialect))
    _write_if_new(sql_dir / "auth_audit_log.sql", render_auth_sql("auth_audit_log", dialect))
    _write_if_new(
        sql_dir / "auth_rate_limit_attempts.sql",
        render_auth_sql("auth_rate_limit_attempts", dialect),
    )

    # FORGE-4 : les ponts vers un opt-in ne sont écrits que si l'opt-in est
    # installé. Leur SQL référence des tables de l'opt-in (user_roles -> roles du
    # RBAC, MFA -> forge-mvc-mfa) ; l'émettre sans l'opt-in rend le socle
    # inapplicable d'un bloc (FK vers une table absente).
    skipped: list[str] = []
    if _optin_installed("forge_mvc_mfa"):
        _write_if_new(sql_dir / "auth_mfa_factors.sql", render_auth_sql("auth_mfa_factors", dialect))
        _write_if_new(
            sql_dir / "auth_mfa_recovery_codes.sql",
            render_auth_sql("auth_mfa_recovery_codes", dialect),
        )
    else:
        skipped.append("MFA (forge-mvc-mfa) : auth_mfa_factors.sql, auth_mfa_recovery_codes.sql")
    if _optin_installed("forge_mvc_rbac"):
        _write_if_new(sql_dir / "user_roles.sql", render_auth_sql("user_roles", dialect))
    else:
        skipped.append("RBAC (forge-mvc-rbac) : user_roles.sql")

    print()
    print(out.info("Commande suivante :"))
    print(out.info("  forge db:apply  # pour créer les tables Auth/User"))
    if skipped:
        print()
        print(out.info("Ponts opt-in non écrits (opt-in non installé) :"))
        for item in skipped:
            print(out.info(f"  - {item}"))
        print(out.info("Installez l'opt-in puis relancez `forge auth:init` pour ajouter son pont."))


def _sql_path(root: Path, filename: str) -> Path:
    return root / _SQL_DIR / filename


def _import_has_attr(module_name: str, attr_name: str) -> bool:
    module = importlib.import_module(module_name)
    return hasattr(module, attr_name)


def _optin_installed(module_name: str) -> bool:
    """Vrai si l'opt-in (paquet) est installé, sans l'importer (FORGE-4)."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        return False


def _load_env_and_configure_forge(root: Path) -> None:
    # ADR-060 : load_project_config charge l'environnement (load_dotenv) ; le
    # backend BDD lit ensuite lui-même DB_APP_*/DB_NAME dans os.environ. Le cœur
    # ne porte plus de config de connexion à pousser ici.
    from cli.project.project_config import ProjectConfigError, load_project_config

    try:
        load_project_config(root)
    except ProjectConfigError as exc:
        raise AuthAdminCliError(str(exc)) from exc


def _friendly_db_error(error: Exception) -> AuthAdminCliError:
    message = str(error)
    lowered = message.lower()
    if "users" in lowered and ("doesn't exist" in lowered or "no such table" in lowered):
        return AuthAdminCliError(
            "Table users introuvable.",
            conseil="Lancez d'abord forge auth:init puis forge db:apply.",
        )
    if "duplicate" in lowered or "unique" in lowered:
        return AuthAdminCliError(
            "Un utilisateur avec cet email existe deja.",
            conseil="Utilisez forge auth:user:list pour consulter les comptes existants.",
        )
    return AuthAdminCliError(
        "Base de donnees Auth/User indisponible.",
        conseil="Verifiez env/dev, DB_APP_* et DB_NAME.",
    )


def _default_fetch_one(sql: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
    from core.database import db

    try:
        return db.fetch_one(sql, params)
    except Exception as error:
        raise _friendly_db_error(error) from error


def _default_fetch_all(sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
    from core.database import db

    try:
        rows = db.fetch_all(sql, params)
    except Exception as error:
        raise _friendly_db_error(error) from error
    return list(rows or [])


def _default_insert(sql: str, params: tuple[Any, ...]) -> int:
    from core.database import db

    try:
        return int(db.insert(sql, params))
    except Exception as error:
        raise _friendly_db_error(error) from error


def _default_execute(sql: str, params: tuple[Any, ...]) -> int:
    from core.database import db

    try:
        return int(db.execute(sql, params))
    except Exception as error:
        raise _friendly_db_error(error) from error


def _normalize_email(email: str | None) -> str:
    value = (email or "").strip().lower()
    if not value:
        raise AuthAdminCliError(
            "Email obligatoire.",
            conseil="Exemple : --email utilisateur@domaine.com",
        )
    if "@" not in value:
        raise AuthAdminCliError(
            "Email invalide.",
            conseil="Format attendu : utilisateur@domaine.com",
        )
    return value


def _validate_password_value(password: str | None) -> str:
    if not isinstance(password, str) or not password:
        raise AuthAdminCliError(
            "Mot de passe obligatoire.",
            conseil="Utilisez --password-prompt pour saisir le mot de passe de maniere securisee.",
        )
    return password


def _log_user_not_found(
    *,
    attempted_id: int | None = None,
    attempted_email: str | None = None,
) -> None:
    from core.auth.audit import AUTH_EVENT_USER_NOT_FOUND, safe_log_auth_event
    meta: dict[str, Any] = {}
    if attempted_id is not None:
        meta["attempted_id"] = attempted_id
    if attempted_email is not None:
        meta["attempted_email"] = attempted_email
    safe_log_auth_event(AUTH_EVENT_USER_NOT_FOUND, metadata=meta or None)


def _public_user_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "email": row.get("email"),
        "is_active": row.get("is_active"),
        "created_at": row.get("created_at"),
    }


def _print_user(row: dict[str, Any]) -> None:
    public = _public_user_row(row)
    print(f"  id: {public.get('id')}")
    print(f"  email: {public.get('email')}")
    print(f"  is_active: {public.get('is_active')}")
    print(f"  created_at: {public.get('created_at')}")


def _resolve_user_id(
    *,
    user_id: int | None,
    email: str | None,
    fetch_one: DbFetchOne,
) -> int:
    if user_id is None and email is None:
        raise AuthAdminCliError(
            "Indiquez --id ou --email.",
            conseil="Exemple : forge auth:user:disable --email utilisateur@domaine.com",
        )
    if user_id is not None and email is not None:
        raise AuthAdminCliError(
            "Utilisez --id ou --email, pas les deux.",
            conseil="Choisissez un seul identifiant : --id ou --email.",
        )
    if user_id is not None:
        if user_id <= 0:
            raise AuthAdminCliError(
                "id doit etre un entier strictement positif.",
                conseil="Exemple : --id 42",
            )
        row = fetch_one("SELECT id FROM users WHERE id = ?", (user_id,))
        if not row:
            _log_user_not_found(attempted_id=user_id)
            raise AuthAdminCliError(
                f"Utilisateur id={user_id} introuvable.",
                conseil="Verifiez l'identifiant avec forge auth:user:list",
            )
        return int(row["id"])
    normalized = _normalize_email(email)
    row = fetch_one("SELECT id FROM users WHERE email = ?", (normalized,))
    if not row:
        _log_user_not_found(attempted_email=normalized)
        raise AuthAdminCliError(
            f"Utilisateur {normalized!r} introuvable.",
            conseil="Verifiez l'email avec forge auth:user:list",
        )
    return int(row["id"])


def create_auth_user(
    *,
    email: str,
    password: str,
    fetch_one: DbFetchOne | None = None,
    insert: DbInsert | None = None,
) -> int:
    from core.auth.password import hash_password

    normalized_email = _normalize_email(email)
    password = _validate_password_value(password)
    fetch_one = fetch_one or _default_fetch_one
    insert = insert or _default_insert

    existing = fetch_one("SELECT id FROM users WHERE email = ?", (normalized_email,))
    if existing:
        raise AuthAdminCliError("Un utilisateur avec cet email existe deja.")

    password_hash = hash_password(password)
    return int(
        insert(
            "INSERT INTO users (email, password_hash, is_active) VALUES (?, ?, TRUE)",
            (normalized_email, password_hash),
        )
    )


def list_auth_users(*, fetch_all: DbFetchAll | None = None) -> tuple[dict[str, Any], ...]:
    fetch_all = fetch_all or _default_fetch_all
    rows = fetch_all(
        "SELECT id, email, is_active, created_at FROM users ORDER BY id",
        (),
    )
    return tuple(_public_user_row(dict(row)) for row in rows)


def show_auth_user(
    *,
    user_id: int | None = None,
    email: str | None = None,
    fetch_one: DbFetchOne | None = None,
) -> dict[str, Any] | None:
    fetch_one = fetch_one or _default_fetch_one
    if user_id is None and email is None:
        raise AuthAdminCliError("Indiquez --id ou --email.")
    if user_id is not None and user_id <= 0:
        raise AuthAdminCliError("id doit etre un entier strictement positif.")
    if user_id is not None and email is not None:
        raise AuthAdminCliError("Utilisez --id ou --email, pas les deux.")

    if user_id is not None:
        row = fetch_one(
            "SELECT id, email, is_active, created_at FROM users WHERE id = ?",
            (user_id,),
        )
    else:
        row = fetch_one(
            "SELECT id, email, is_active, created_at FROM users WHERE email = ?",
            (_normalize_email(email),),
        )
    return _public_user_row(dict(row)) if row else None


def disable_auth_user(
    *,
    user_id: int | None = None,
    email: str | None = None,
    fetch_one: DbFetchOne | None = None,
    execute: DbExecute | None = None,
) -> int:
    fetch_one = fetch_one or _default_fetch_one
    execute = execute or _default_execute
    uid = _resolve_user_id(user_id=user_id, email=email, fetch_one=fetch_one)
    execute("UPDATE users SET is_active = FALSE WHERE id = ?", (uid,))
    return uid


def enable_auth_user(
    *,
    user_id: int | None = None,
    email: str | None = None,
    fetch_one: DbFetchOne | None = None,
    execute: DbExecute | None = None,
) -> int:
    fetch_one = fetch_one or _default_fetch_one
    execute = execute or _default_execute
    uid = _resolve_user_id(user_id=user_id, email=email, fetch_one=fetch_one)
    execute("UPDATE users SET is_active = TRUE WHERE id = ?", (uid,))
    return uid


def change_auth_user_password(
    *,
    user_id: int | None = None,
    email: str | None = None,
    password: str,
    fetch_one: DbFetchOne | None = None,
    execute: DbExecute | None = None,
) -> int:
    from core.auth.password import hash_password

    fetch_one = fetch_one or _default_fetch_one
    execute = execute or _default_execute
    _validate_password_value(password)
    uid = _resolve_user_id(user_id=user_id, email=email, fetch_one=fetch_one)
    new_hash = hash_password(password)
    execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, uid))
    return uid


def _normalize_role_value(role: str | None) -> str:
    value = (role or "").strip()
    if not value:
        raise AuthAdminCliError("Role obligatoire.")
    return value


def _resolve_role_id(*, role: str | None, fetch_one: DbFetchOne) -> int:
    value = _normalize_role_value(role)
    if value.isdigit():
        role_id = int(value)
        if role_id <= 0:
            raise AuthAdminCliError("role doit etre un id positif, un slug ou un nom.")
        row = fetch_one("SELECT id FROM roles WHERE id = ?", (role_id,))
    else:
        row = fetch_one(
            "SELECT id FROM roles WHERE slug = ? OR name = ? OR LOWER(name) = ?",
            (value.lower(), value, value.lower()),
        )

    if not row:
        raise AuthAdminCliError(f"Role {value!r} introuvable.")
    return int(row["id"])


def add_auth_user_role(
    *,
    user_id: int | None = None,
    email: str | None = None,
    role: str,
    fetch_one: DbFetchOne | None = None,
    execute: DbExecute | None = None,
) -> dict[str, Any]:
    fetch_one = fetch_one or _default_fetch_one
    execute = execute or _default_execute
    uid = _resolve_user_id(user_id=user_id, email=email, fetch_one=fetch_one)
    role_id = _resolve_role_id(role=role, fetch_one=fetch_one)

    existing = fetch_one(
        "SELECT user_id, role_id FROM user_roles WHERE user_id = ? AND role_id = ?",
        (uid, role_id),
    )
    if existing:
        return {"user_id": uid, "role_id": role_id, "created": False}

    execute(
        "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
        (uid, role_id),
    )
    return {"user_id": uid, "role_id": role_id, "created": True}


def remove_auth_user_role(
    *,
    user_id: int | None = None,
    email: str | None = None,
    role: str,
    fetch_one: DbFetchOne | None = None,
    execute: DbExecute | None = None,
) -> dict[str, Any]:
    fetch_one = fetch_one or _default_fetch_one
    execute = execute or _default_execute
    uid = _resolve_user_id(user_id=user_id, email=email, fetch_one=fetch_one)
    role_id = _resolve_role_id(role=role, fetch_one=fetch_one)

    existing = fetch_one(
        "SELECT user_id, role_id FROM user_roles WHERE user_id = ? AND role_id = ?",
        (uid, role_id),
    )
    if not existing:
        return {"user_id": uid, "role_id": role_id, "removed": False}

    execute(
        "DELETE FROM user_roles WHERE user_id = ? AND role_id = ?",
        (uid, role_id),
    )
    return {"user_id": uid, "role_id": role_id, "removed": True}


def list_auth_user_roles(
    *,
    user_id: int | None = None,
    email: str | None = None,
    fetch_one: DbFetchOne | None = None,
    fetch_all: DbFetchAll | None = None,
) -> tuple[dict[str, Any], ...]:
    fetch_one = fetch_one or _default_fetch_one
    fetch_all = fetch_all or _default_fetch_all
    uid = _resolve_user_id(user_id=user_id, email=email, fetch_one=fetch_one)

    rows = fetch_all(
        """
        SELECT roles.id AS role_id, roles.slug, roles.name
        FROM user_roles
        JOIN roles ON roles.id = user_roles.role_id
        WHERE user_roles.user_id = ?
        ORDER BY roles.slug, roles.id
        """,
        (uid,),
    )
    return tuple(
        {
            "role_id": row.get("role_id", row.get("id")),
            "slug": row.get("slug"),
            "name": row.get("name"),
        }
        for row in rows
    )


def list_auth_sql_files(root: Path | None = None) -> tuple[AuthCliCheck, ...]:
    root = root or Path.cwd()
    checks: list[AuthCliCheck] = []
    for item in AUTH_SQL_FILES:
        path = _sql_path(root, item.filename)
        if path.exists():
            checks.append(AuthCliCheck("ok", item.label, path.as_posix()))
        else:
            detail = f"{path.as_posix()} absent — SQL optionnel, non applique automatiquement"
            checks.append(AuthCliCheck("warn", item.label, detail))
    return tuple(checks)


def build_auth_status(root: Path | None = None) -> tuple[AuthCliCheck, ...]:
    root = root or Path.cwd()
    checks: list[AuthCliCheck] = []
    for label, module_name, attr_name, sql_filename in AUTH_FEATURES:
        try:
            available = _import_has_attr(module_name, attr_name)
        except Exception as error:
            checks.append(AuthCliCheck("fail", label, f"{module_name} non importable : {error}"))
            continue

        if not available:
            checks.append(AuthCliCheck("fail", label, f"{attr_name} introuvable dans {module_name}"))
            continue

        if sql_filename is not None:
            path = _sql_path(root, sql_filename)
            if path.exists():
                checks.append(AuthCliCheck("ok", label, f"{attr_name} disponible, SQL present"))
            else:
                checks.append(AuthCliCheck("warn", label, f"{attr_name} disponible, {sql_filename} absent optionnel"))
        else:
            checks.append(AuthCliCheck("ok", label, f"{attr_name} disponible"))
    return tuple(checks)


def run_auth_doctor(root: Path | None = None) -> tuple[AuthCliCheck, ...]:
    root = root or Path.cwd()
    checks: list[AuthCliCheck] = []

    for module_name in AUTH_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as error:
            checks.append(AuthCliCheck("fail", module_name, f"non importable : {error}"))
        else:
            checks.append(AuthCliCheck("ok", module_name, "importable"))

    mfa_importable = any(c.label == "forge_mvc_mfa" and c.status == "ok" for c in checks)
    if mfa_importable:
        checks.append(AuthCliCheck(
            "warn",
            "forge_mvc_mfa",
            "Opt-in MFA (Beta) : secret TOTP chiffré au repos (Fernet), "
            "FORGE_MFA_SECRET_KEY obligatoire au démarrage. "
            "Voir packages/forge-mvc-mfa/docs/reference.md",
        ))
    else:
        checks.append(AuthCliCheck(
            "warn",
            "forge_mvc_mfa",
            "Opt-in MFA non installé (Beta) : si activé, FORGE_MFA_SECRET_KEY est "
            "obligatoire (secret TOTP chiffré au repos). "
            "Voir packages/forge-mvc-mfa/docs/reference.md",
        ))

    for module_name, attr_name in AUTH_CONTRACTS:
        try:
            has_attr = _import_has_attr(module_name, attr_name)
        except Exception as error:
            checks.append(AuthCliCheck("fail", f"{module_name}.{attr_name}", f"non verifiable : {error}"))
        else:
            status = "ok" if has_attr else "fail"
            detail = "present" if has_attr else "absent"
            checks.append(AuthCliCheck(status, f"{module_name}.{attr_name}", detail))

    for module_name, attr_name in RBAC_CONTRACTS:
        try:
            has_attr = _import_has_attr(module_name, attr_name)
        except Exception as error:
            checks.append(AuthCliCheck("warn", f"{module_name}.{attr_name}", f"RBAC optionnel non disponible : {error}"))
        else:
            status = "ok" if has_attr else "warn"
            detail = "RBAC disponible" if has_attr else "RBAC optionnel incomplet"
            checks.append(AuthCliCheck(status, f"{module_name}.{attr_name}", detail))

    checks.extend(list_auth_sql_files(root))
    return tuple(checks)


def _print_checks(title: str, checks: tuple[AuthCliCheck, ...]) -> None:
    print(f"\n{title}\n")
    for check in checks:
        status_tag = f"[{check.status.upper()}]".ljust(7)
        detail = f" — {check.detail}" if check.detail else ""
        print(f"  {status_tag} {check.label}{detail}")

    warns = sum(1 for check in checks if check.status == "warn")
    fails = sum(1 for check in checks if check.status == "fail")
    print(f"\n{warns} avertissement(s), {fails} erreur(s).")
    print("Aucun secret, token ou hash utilisateur n'est affiche.")

    if fails:
        raise SystemExit(1)


def cmd_auth_list_sql(args: list[str], root: Path | None = None) -> None:
    if args:
        raise SystemExit("Usage : forge auth:list-sql")

    checks = list_auth_sql_files(root)
    _print_checks("Forge auth:list-sql — SQL optionnels Auth/User", checks)


def cmd_auth_status(args: list[str], root: Path | None = None) -> None:
    if args:
        raise SystemExit("Usage : forge auth:status")

    checks = build_auth_status(root)
    _print_checks("Forge auth:status — socle Auth/User", checks)


def cmd_auth_doctor(args: list[str], root: Path | None = None) -> None:
    if args:
        raise SystemExit("Usage : forge auth:doctor")

    checks = run_auth_doctor(root)
    _print_checks("Forge auth:doctor — diagnostic Auth/User", checks)


def _run_admin_command(action: "Callable[[], None]", *, root: Path | None = None) -> None:
    try:
        _load_env_and_configure_forge(root or Path.cwd())
        action()
    except AuthAdminCliError as error:
        lines = [f"Erreur : {error}"]
        if error.conseil:
            lines.append(f"Conseil : {error.conseil}")
        raise SystemExit("\n".join(lines)) from error


def cmd_auth_user_create(
    args: list[str],
    root: Path | None = None,
    *,
    fetch_one: DbFetchOne | None = None,
    insert: DbInsert | None = None,
) -> None:
    parser = argparse.ArgumentParser(prog="forge auth:user:create")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password")
    parser.add_argument("--password-prompt", action="store_true")
    parsed = parser.parse_args(args)

    def action() -> None:
        password = parsed.password
        if password is None or parsed.password_prompt:
            password = getpass.getpass("Mot de passe : ")
        user_id = create_auth_user(
            email=parsed.email,
            password=password,
            fetch_one=fetch_one,
            insert=insert,
        )
        print(out.created(f"Utilisateur cree : id={user_id}, email={_normalize_email(parsed.email)}"))

    _run_admin_command(action, root=root)


def cmd_auth_user_list(
    args: list[str],
    root: Path | None = None,
    *,
    fetch_all: DbFetchAll | None = None,
) -> None:
    if args:
        raise SystemExit("Usage : forge auth:user:list")

    def action() -> None:
        users = list_auth_users(fetch_all=fetch_all)
        print("\nForge auth:user:list\n")
        if not users:
            print("  Aucun utilisateur local.")
            return
        print("  id  email                         actif  created_at")
        for user in users:
            print(
                f"  {str(user.get('id')):<3} "
                f"{str(user.get('email')):<29} "
                f"{str(user.get('is_active')):<5} "
                f"{user.get('created_at')}"
            )

    _run_admin_command(action, root=root)


def cmd_auth_user_show(
    args: list[str],
    root: Path | None = None,
    *,
    fetch_one: DbFetchOne | None = None,
) -> None:
    parser = argparse.ArgumentParser(prog="forge auth:user:show")
    parser.add_argument("--id", type=int)
    parser.add_argument("--email")
    parsed = parser.parse_args(args)

    def action() -> None:
        user = show_auth_user(
            user_id=parsed.id,
            email=parsed.email,
            fetch_one=fetch_one,
        )
        print("\nForge auth:user:show\n")
        if user is None:
            print("  Utilisateur introuvable.")
            return
        _print_user(user)

    _run_admin_command(action, root=root)


def cmd_auth_user_disable(
    args: list[str],
    root: Path | None = None,
    *,
    fetch_one: DbFetchOne | None = None,
    execute: DbExecute | None = None,
) -> None:
    parser = argparse.ArgumentParser(prog="forge auth:user:disable")
    parser.add_argument("--id", type=int)
    parser.add_argument("--email")
    parsed = parser.parse_args(args)

    def action() -> None:
        uid = disable_auth_user(
            user_id=parsed.id,
            email=parsed.email,
            fetch_one=fetch_one,
            execute=execute,
        )
        print(out.info(f"Utilisateur id={uid} desactive."))
        from core.auth.audit import AUTH_EVENT_USER_DISABLED, safe_log_auth_event
        safe_log_auth_event(AUTH_EVENT_USER_DISABLED, user_id=uid)

    _run_admin_command(action, root=root)


def cmd_auth_user_enable(
    args: list[str],
    root: Path | None = None,
    *,
    fetch_one: DbFetchOne | None = None,
    execute: DbExecute | None = None,
) -> None:
    parser = argparse.ArgumentParser(prog="forge auth:user:enable")
    parser.add_argument("--id", type=int)
    parser.add_argument("--email")
    parsed = parser.parse_args(args)

    def action() -> None:
        uid = enable_auth_user(
            user_id=parsed.id,
            email=parsed.email,
            fetch_one=fetch_one,
            execute=execute,
        )
        print(out.info(f"Utilisateur id={uid} reactive."))
        from core.auth.audit import AUTH_EVENT_USER_ENABLED, safe_log_auth_event
        safe_log_auth_event(AUTH_EVENT_USER_ENABLED, user_id=uid)

    _run_admin_command(action, root=root)


def cmd_auth_user_password(
    args: list[str],
    root: Path | None = None,
    *,
    fetch_one: DbFetchOne | None = None,
    execute: DbExecute | None = None,
) -> None:
    parser = argparse.ArgumentParser(prog="forge auth:user:password")
    parser.add_argument("--id", type=int)
    parser.add_argument("--email")
    parser.add_argument("--password")
    parser.add_argument("--password-prompt", action="store_true")
    parsed = parser.parse_args(args)

    def action() -> None:
        password = parsed.password
        if password is None or parsed.password_prompt:
            password = getpass.getpass("Nouveau mot de passe : ")
        uid = change_auth_user_password(
            user_id=parsed.id,
            email=parsed.email,
            password=password,
            fetch_one=fetch_one,
            execute=execute,
        )
        print(out.info(f"Mot de passe de id={uid} modifie."))
        from core.auth.audit import AUTH_EVENT_USER_PASSWORD_CHANGED, safe_log_auth_event
        safe_log_auth_event(AUTH_EVENT_USER_PASSWORD_CHANGED, user_id=uid)

    _run_admin_command(action, root=root)


def _add_user_lookup_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--id", type=int)
    parser.add_argument("--email")


def cmd_auth_user_role_add(
    args: list[str],
    root: Path | None = None,
    *,
    fetch_one: DbFetchOne | None = None,
    execute: DbExecute | None = None,
) -> None:
    parser = argparse.ArgumentParser(prog="forge auth:user:role:add")
    _add_user_lookup_args(parser)
    parser.add_argument("--role", required=True)
    parsed = parser.parse_args(args)

    def action() -> None:
        result = add_auth_user_role(
            user_id=parsed.id,
            email=parsed.email,
            role=parsed.role,
            fetch_one=fetch_one,
            execute=execute,
        )
        if result["created"]:
            print(out.created(
                f"Role id={result['role_id']} attribue a utilisateur id={result['user_id']}."
            ))
            from core.auth.audit import AUTH_EVENT_USER_ROLE_ADDED, safe_log_auth_event
            safe_log_auth_event(
                AUTH_EVENT_USER_ROLE_ADDED,
                user_id=result["user_id"],
                metadata={"role_id": result["role_id"]},
            )
        else:
            print(out.info(
                f"Role id={result['role_id']} deja attribue a utilisateur id={result['user_id']}."
            ))

    _run_admin_command(action, root=root)


def cmd_auth_user_role_remove(
    args: list[str],
    root: Path | None = None,
    *,
    fetch_one: DbFetchOne | None = None,
    execute: DbExecute | None = None,
) -> None:
    parser = argparse.ArgumentParser(prog="forge auth:user:role:remove")
    _add_user_lookup_args(parser)
    parser.add_argument("--role", required=True)
    parsed = parser.parse_args(args)

    def action() -> None:
        result = remove_auth_user_role(
            user_id=parsed.id,
            email=parsed.email,
            role=parsed.role,
            fetch_one=fetch_one,
            execute=execute,
        )
        if result["removed"]:
            print(out.info(
                f"Role id={result['role_id']} retire de utilisateur id={result['user_id']}."
            ))
            from core.auth.audit import AUTH_EVENT_USER_ROLE_REMOVED, safe_log_auth_event
            safe_log_auth_event(
                AUTH_EVENT_USER_ROLE_REMOVED,
                user_id=result["user_id"],
                metadata={"role_id": result["role_id"]},
            )
        else:
            print(out.info(
                f"Role id={result['role_id']} absent pour utilisateur id={result['user_id']}."
            ))

    _run_admin_command(action, root=root)


def cmd_auth_user_roles(
    args: list[str],
    root: Path | None = None,
    *,
    fetch_one: DbFetchOne | None = None,
    fetch_all: DbFetchAll | None = None,
) -> None:
    parser = argparse.ArgumentParser(prog="forge auth:user:roles")
    _add_user_lookup_args(parser)
    parsed = parser.parse_args(args)

    def action() -> None:
        roles = list_auth_user_roles(
            user_id=parsed.id,
            email=parsed.email,
            fetch_one=fetch_one,
            fetch_all=fetch_all,
        )
        print("\nForge auth:user:roles\n")
        if not roles:
            print("  Aucun role attribue.")
            return
        print("  role_id  slug                         name")
        for role in roles:
            print(
                f"  {str(role.get('role_id')):<7} "
                f"{str(role.get('slug') or '-'):<28} "
                f"{role.get('name') or '-'}"
            )

    _run_admin_command(action, root=root)


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)

    if not args:
        raise SystemExit(
            "Usage : forge auth:init | auth:doctor | auth:status | auth:list-sql | "
            "auth:user:create | auth:user:list | auth:user:show | "
            "auth:user:disable | auth:user:enable | auth:user:password | "
            "auth:user:role:add | auth:user:role:remove | auth:user:roles"
        )

    command = args[0]
    if command == "auth:init":
        cmd_auth_init(args[1:])
        return
    if command == "auth:doctor":
        cmd_auth_doctor(args[1:])
        return
    if command == "auth:status":
        cmd_auth_status(args[1:])
        return
    if command == "auth:list-sql":
        cmd_auth_list_sql(args[1:])
        return
    if command == "auth:user:create":
        cmd_auth_user_create(args[1:])
        return
    if command == "auth:user:list":
        cmd_auth_user_list(args[1:])
        return
    if command == "auth:user:show":
        cmd_auth_user_show(args[1:])
        return
    if command == "auth:user:disable":
        cmd_auth_user_disable(args[1:])
        return
    if command == "auth:user:enable":
        cmd_auth_user_enable(args[1:])
        return
    if command == "auth:user:password":
        cmd_auth_user_password(args[1:])
        return
    if command == "auth:user:role:add":
        cmd_auth_user_role_add(args[1:])
        return
    if command == "auth:user:role:remove":
        cmd_auth_user_role_remove(args[1:])
        return
    if command == "auth:user:roles":
        cmd_auth_user_roles(args[1:])
        return

    raise SystemExit(
        "Usage : forge auth:init | auth:doctor | auth:status | auth:list-sql | "
        "auth:user:create | auth:user:list | auth:user:show | "
        "auth:user:disable | auth:user:enable | auth:user:password | "
        "auth:user:role:add | auth:user:role:remove | auth:user:roles"
    )
