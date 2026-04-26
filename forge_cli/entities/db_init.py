"""Provisioning MariaDB du projet Forge."""

from __future__ import annotations

from dataclasses import dataclass

from forge_cli.project_config import ProjectConfigError, load_project_config

DEFAULT_APP_PRIVILEGES = (
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "CREATE",
    "ALTER",
    "DROP",
    "INDEX",
    "REFERENCES",
)


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


def load_db_init_config() -> DbInitConfig:
    config = load_project_config()

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
    )


def init_project_database() -> list[str]:
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

            user_hosts = _load_user_hosts(cursor, cfg.app_login)
            target_user = f"{cfg.app_login}@{cfg.app_host}"
            if not user_hosts:
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
                f"GRANT {', '.join(DEFAULT_APP_PRIVILEGES)} ON {_quote_identifier(cfg.db_name)}.* "
                f"TO {_quote_user(cfg.app_login, cfg.app_host)}"
            )
            actions.append(
                f"Privilèges appliqués sur {cfg.db_name} à {target_user} "
                f"({', '.join(DEFAULT_APP_PRIVILEGES)})."
            )

            cursor.execute("FLUSH PRIVILEGES")
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
    import mariadb

    try:
        return mariadb.connect(
            host=cfg.admin_host,
            port=cfg.admin_port,
            user=cfg.admin_login,
            password=cfg.admin_password,
        )
    except Exception as exc:
        raise DbInitError(
            "Connexion MariaDB admin impossible. "
            "Vérifiez DB_ADMIN_* dans env/dev."
        ) from exc


def _quote_identifier(value: str) -> str:
    return "`" + value.replace("`", "``") + "`"


def _quote_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def _quote_user(login: str, host: str) -> str:
    return f"{_quote_string(login)}@{_quote_string(host)}"


def _database_exists(cursor, db_name: str) -> bool:
    cursor.execute(
        "SELECT SCHEMA_NAME "
        "FROM INFORMATION_SCHEMA.SCHEMATA "
        f"WHERE SCHEMA_NAME = {_quote_string(db_name)}"
    )
    return cursor.fetchone() is not None


def _load_user_hosts(cursor, login: str) -> list[str]:
    cursor.execute(
        "SELECT Host "
        "FROM mysql.user "
        f"WHERE User = {_quote_string(login)} "
        "ORDER BY Host"
    )
    rows = cursor.fetchall()
    return [row[0] for row in rows]


def _rollback_quietly(connection) -> None:
    try:
        connection.rollback()
    except Exception:
        pass
