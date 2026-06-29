# pyright: strict
"""Provisioning MariaDB du projet Forge."""

from __future__ import annotations
from typing import Any

from dataclasses import dataclass

from cli.project.project_config import ProjectConfigError, load_project_config

# ADR-033 : le compte applicatif (forge_app) est un compte runtime à privilèges
# minimaux (DML). Les migrations (DDL) utilisent DB_ADMIN_*, donc forge_app n'a
# plus besoin de CREATE/ALTER/DROP. Défaut resserré sur le DML.
DEFAULT_APP_PRIVILEGES = (
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
)
# Un override explicite via DB_APP_PRIVILEGES peut encore demander du DDL
# (escape hatch avancé), mais ce n'est plus accordé par défaut.
_ALLOWED_APP_PRIVILEGES = frozenset({
    "SELECT", "INSERT", "UPDATE", "DELETE",
    "CREATE", "ALTER", "DROP", "INDEX", "REFERENCES",
})
FORGE_MIGRATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS forge_migrations (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    version VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    checksum CHAR(64) NOT NULL,
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    execution_ms INT NULL,
    UNIQUE KEY uq_forge_migrations_version (version),
    UNIQUE KEY uq_forge_migrations_filename (filename)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
""".strip()


class DbInitError(ValueError):
    """Erreur de provisioning MariaDB."""


@dataclass(frozen=True)
class DbInitConfig:
    admin_host: str
    admin_port: int
    admin_login: str
    admin_password: str
    db_name: str
    db_charset: str
    db_collation: str
    app_host: str
    app_port: int
    app_login: str
    app_password: str
    app_privileges: tuple[str, ...]


def _parse_app_privileges(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, str):
        raise DbInitError(
            f"DB_APP_PRIVILEGES doit etre une chaine de privileges separes par des virgules "
            f"(ex: SELECT,INSERT,UPDATE). Valeur recue : {raw!r}"
        )
    privileges = tuple(p.strip().upper() for p in raw.split(",") if p.strip())
    if not privileges:
        raise DbInitError("DB_APP_PRIVILEGES ne peut pas etre vide.")
    for priv in privileges:
        if priv not in _ALLOWED_APP_PRIVILEGES:
            allowed_str = ", ".join(sorted(_ALLOWED_APP_PRIVILEGES))
            raise DbInitError(
                f"Privilege MariaDB non supporte dans DB_APP_PRIVILEGES : {priv}\n"
                f"Privileges autorises : {allowed_str}"
            )
    return privileges


def load_db_init_config() -> DbInitConfig:
    config = load_project_config()

    raw_privileges = getattr(config, "DB_APP_PRIVILEGES", None)
    app_privileges = _parse_app_privileges(raw_privileges) if raw_privileges is not None else DEFAULT_APP_PRIVILEGES

    return DbInitConfig(
        admin_host=config.DB_ADMIN_HOST,
        admin_port=config.DB_ADMIN_PORT,
        admin_login=config.DB_ADMIN_LOGIN,
        admin_password=config.DB_ADMIN_PWD,
        db_name=config.DB_NAME,
        db_charset=config.DB_CHARSET,
        db_collation=config.DB_COLLATION,
        app_host=config.DB_APP_HOST,
        app_port=config.DB_APP_PORT,
        app_login=config.DB_APP_LOGIN,
        app_password=config.DB_APP_PWD,
        app_privileges=app_privileges,
    )


def _init_serverless(backend: Any) -> list[str]:
    """Init d'un backend sans serveur (ex. SQLite, ADR-054).

    Aucune base ni aucun compte à provisionner : on garantit la connexion
    (fichier créé au besoin) et la table technique forge_migrations.
    """
    from cli.entities.serverless_db import configure_serverless_db

    config = configure_serverless_db()

    actions: list[str] = []
    connection = backend.get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(backend.dialect.forge_migrations_ddl())
            connection.commit()
            actions.append(f"Base {config.DB_NAME} prête.")
            actions.append("Table forge_migrations prête.")
        finally:
            cursor.close()
    except Exception as exc:
        _rollback_quietly(connection)
        raise DbInitError(f"Initialisation {backend.name} impossible : {exc}") from exc
    finally:
        backend.close_connection(connection)
    return actions


def init_project_database() -> list[str]:
    from core.database.backend import get_backend

    backend = get_backend()
    if not getattr(backend, "requires_provisioning", True):
        # Backend sans serveur (SQLite) : ni base ni comptes à créer.
        return _init_serverless(backend)

    cfg = load_db_init_config()
    connection = _connect_admin(cfg)
    actions: list[str] = []

    try:
        cursor = connection.cursor()
        try:
            if _database_exists(cursor, cfg.db_name):
                actions.append(f"Base {cfg.db_name} déjà présente.")
            else:
                cursor.execute(
                    f"CREATE DATABASE {_quote_identifier(cfg.db_name)} "
                    f"CHARACTER SET {cfg.db_charset} COLLATE {cfg.db_collation}"
                )
                actions.append(f"Base {cfg.db_name} créée.")

            user_hosts = _try_load_user_hosts(cursor, cfg.app_login)
            target_user = f"{cfg.app_login}@{cfg.app_host}"
            if user_hosts is None:
                cursor.execute(
                    f"CREATE USER IF NOT EXISTS {_quote_user(cfg.app_login, cfg.app_host)} "
                    f"IDENTIFIED BY {_quote_string(cfg.app_password)}"
                )
                actions.append(f"Utilisateur applicatif {target_user} créé ou déjà présent.")
                actions.append(
                    "Information : le compte d'administration n'a pas le droit SELECT sur "
                    "mysql.user ; la détection multi-hôte de l'utilisateur applicatif a été "
                    "ignorée (forge db:init n'exige pas ce privilège)."
                )
            elif not user_hosts:
                cursor.execute(
                    f"CREATE USER {_quote_user(cfg.app_login, cfg.app_host)} "
                    f"IDENTIFIED BY {_quote_string(cfg.app_password)}"
                )
                actions.append(f"Utilisateur applicatif {target_user} créé.")
            elif cfg.app_host in user_hosts:
                actions.append(f"Utilisateur applicatif {target_user} déjà présent.")
                if len(user_hosts) > 1:
                    other_hosts = ", ".join(sorted(host for host in user_hosts if host != cfg.app_host))
                    actions.append(
                        "Vérification manuelle nécessaire : "
                        f"l'identifiant {cfg.app_login} existe aussi pour d'autres hôtes ({other_hosts})."
                    )
                actions.append(
                    "Vérification manuelle nécessaire : "
                    f"le mot de passe et l'état de {target_user} ne sont pas modifiés par forge db:init."
                )
            else:
                known_hosts = ", ".join(sorted(user_hosts))
                raise DbInitError(
                    "Vérification manuelle nécessaire : "
                    f"l'utilisateur applicatif {cfg.app_login} existe déjà pour ({known_hosts}) "
                    f"mais pas pour {cfg.app_host}. forge db:init ne crée ni ne modifie "
                    "silencieusement un utilisateur existant dans ce cas."
                )

            cursor.execute(
                f"GRANT {', '.join(cfg.app_privileges)} ON {_quote_identifier(cfg.db_name)}.* "
                f"TO {_quote_user(cfg.app_login, cfg.app_host)}"
            )
            actions.append(
                f"Privilèges appliqués sur {cfg.db_name} à {target_user} "
                f"({', '.join(cfg.app_privileges)})."
            )

            _create_forge_migrations_table(cursor, cfg.db_name)
            actions.append("Table forge_migrations prête.")

            # Pas de FLUSH PRIVILEGES : CREATE USER et GRANT prennent effet
            # immédiatement en MariaDB. FLUSH n'est requis qu'après modification
            # directe des tables mysql.*, ce que db:init ne fait jamais. L'éviter
            # dispense le compte d'administration du projet du privilège RELOAD
            # (moindre privilège, charte principe 7).
            connection.commit()
        finally:
            cursor.close()
    except Exception as exc:
        _rollback_quietly(connection)
        raise DbInitError(f"Provisioning MariaDB impossible : {exc}") from exc
    finally:
        connection.close()

    return actions


def main(argv: list[str] | None = None) -> None:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] != "db:init":
        print("Usage : forge db:init")
        raise SystemExit(1)

    try:
        actions = init_project_database()
        print("[OK] Environnement MariaDB du projet prêt.")
        for action in actions:
            print(f"[FAIT] {action}")
    except (DbInitError, ProjectConfigError, ValueError) as exc:
        print(f"[ERREUR] {exc}")
        raise SystemExit(1)


def _connect_admin(cfg: DbInitConfig):
    from core.database.backend import get_backend

    try:
        return get_backend().get_admin_connection(
            host=cfg.admin_host,
            port=cfg.admin_port,
            login=cfg.admin_login,
            password=cfg.admin_password,
        )
    except Exception as exc:
        raise DbInitError(
            "Connexion d'administration impossible. "
            "Vérifiez DB_ADMIN_* dans env/dev."
        ) from exc


def _quote_identifier(value: str) -> str:
    return "`" + value.replace("`", "``") + "`"


def _quote_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def _quote_user(login: str, host: str) -> str:
    return f"{_quote_string(login)}@{_quote_string(host)}"


def _database_exists(cursor: Any, db_name: str) -> bool:
    cursor.execute(
        "SELECT SCHEMA_NAME "
        "FROM INFORMATION_SCHEMA.SCHEMATA "
        f"WHERE SCHEMA_NAME = {_quote_string(db_name)}"
    )
    return cursor.fetchone() is not None


def _load_user_hosts(cursor: Any, login: str) -> list[str]:
    cursor.execute(
        "SELECT Host "
        "FROM mysql.user "
        f"WHERE User = {_quote_string(login)} "
        "ORDER BY Host"
    )
    rows = cursor.fetchall()
    return [row[0] for row in rows]


# Errnos MariaDB d'un refus d'accès à la lecture de mysql.user
# (1044 DBACCESS_DENIED, 1045 ACCESS_DENIED, 1142 TABLEACCESS_DENIED).
_PERMISSION_DENIED_ERRNOS = frozenset({1044, 1045, 1142})


def _try_load_user_hosts(cursor: Any, login: str) -> list[str] | None:
    """Hôtes connus de ``login``, ou ``None`` si la lecture de ``mysql.user``
    est refusée.

    forge db:init lit mysql.user pour décider entre créer, réutiliser ou
    refuser le compte applicatif. Un compte d'administration minimal (par
    exemple forge_admin sans SELECT sur mysql.user) n'a pas ce droit : on
    bascule alors en mode dégradé (CREATE USER IF NOT EXISTS) plutôt que
    d'exiger un privilège global supplémentaire. Toute autre erreur est
    propagée.
    """
    try:
        return _load_user_hosts(cursor, login)
    except Exception as exc:
        if getattr(exc, "errno", None) in _PERMISSION_DENIED_ERRNOS:
            return None
        raise


def _create_forge_migrations_table(cursor: Any, db_name: str) -> None:
    cursor.execute(f"USE {_quote_identifier(db_name)}")
    cursor.execute(FORGE_MIGRATIONS_TABLE_SQL)


def _rollback_quietly(connection: Any) -> None:
    try:
        connection.rollback()
    except Exception:
        pass
