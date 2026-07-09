# pyright: strict
"""Provisioning MariaDB du projet Forge."""

from __future__ import annotations
from typing import Any

import os
from dataclasses import dataclass
from pathlib import Path

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
    # ADR-060 : les identifiants d'administration (connexion) sont lus par le
    # backend depuis l'environnement (DB_ADMIN_*). Ne restent ici que les
    # paramètres de provisionnement : base à créer et compte applicatif à poser.
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
    # ADR-060 : load_project_config charge l'environnement (load_dotenv) ; les
    # paramètres de provisionnement sont ensuite lus dans os.environ, plus dans
    # les attributs de config.py (qui ne porte plus de bloc BDD).
    load_project_config()

    raw_privileges = os.environ.get("DB_APP_PRIVILEGES")
    app_privileges = _parse_app_privileges(raw_privileges) if raw_privileges is not None else DEFAULT_APP_PRIVILEGES

    return DbInitConfig(
        db_name=os.environ.get("DB_NAME", ""),
        db_charset=os.environ.get("DB_CHARSET", "utf8mb4"),
        db_collation=os.environ.get("DB_COLLATION", "utf8mb4_unicode_ci"),
        # ADR-066 : l'origine du grant applicatif suit DB_HOST (serveur partagé),
        # ce qui garantit que l'hôte du grant coïncide avec l'hôte de connexion.
        app_host=os.environ.get("DB_HOST", "localhost"),
        app_port=int(os.environ.get("DB_PORT", "3306")),
        app_login=os.environ.get("DB_APP_LOGIN", ""),
        app_password=os.environ.get("DB_APP_PWD", ""),
        app_privileges=app_privileges,
    )


@dataclass(frozen=True)
class ProvisioningEnv:
    """Valeurs d'environnement pour générer le SQL de provisioning (ADR-067).

    Regroupe base, serveur (hôte du grant) et les DEUX comptes (administration de
    la base + applicatif), tels que lus dans `env/`, sans jamais exiger le root du
    serveur.
    """
    db_name: str
    db_charset: str
    db_collation: str
    host: str
    admin_login: str
    admin_password: str
    app_login: str
    app_password: str
    app_privileges: tuple[str, ...]


def load_provisioning_env() -> ProvisioningEnv:
    """Lit dans l'environnement tout ce qu'il faut pour le script de provisioning."""
    load_project_config()
    raw_privileges = os.environ.get("DB_APP_PRIVILEGES")
    app_privileges = _parse_app_privileges(raw_privileges) if raw_privileges is not None else DEFAULT_APP_PRIVILEGES
    return ProvisioningEnv(
        db_name=os.environ.get("DB_NAME", ""),
        db_charset=os.environ.get("DB_CHARSET", "utf8mb4"),
        db_collation=os.environ.get("DB_COLLATION", "utf8mb4_unicode_ci"),
        # ADR-066 : l'hôte du grant suit DB_HOST (serveur partagé).
        host=os.environ.get("DB_HOST", "localhost"),
        admin_login=os.environ.get("DB_ADMIN_LOGIN", ""),
        admin_password=os.environ.get("DB_ADMIN_PWD", ""),
        app_login=os.environ.get("DB_APP_LOGIN", ""),
        app_password=os.environ.get("DB_APP_PWD", ""),
        app_privileges=app_privileges,
    )


# Variables requises pour provisionner MariaDB (ADR-067). DB_HOST/DB_PORT/
# DB_CHARSET/DB_COLLATION ont des valeurs par défaut et ne sont pas exigées.
_REQUIRED_PROVISIONING_ENV = (
    "DB_NAME",
    "DB_ADMIN_LOGIN",
    "DB_ADMIN_PWD",
    "DB_APP_LOGIN",
    "DB_APP_PWD",
)

# Caractères interdits par MariaDB dans un nom de base (ils correspondent à des
# séparateurs de chemin ou à des extensions de fichier côté serveur).
_DB_NAME_FORBIDDEN = ("/", "\\", ".")


def _validate_db_name(name: str) -> None:
    """Vérifie que `name` est un nom de base MariaDB valide (ADR-067)."""
    if not name or len(name) > 64:
        raise DbInitError(
            f"Nom de base invalide : {name!r}. Un nom de base doit faire de 1 à 64 "
            "caractères. Renseignez DB_NAME dans env/dev."
        )
    if name != name.strip():
        raise DbInitError(
            f"Nom de base invalide : {name!r}. Pas d'espace en tête ni en fin de nom."
        )
    for char in name:
        if char in _DB_NAME_FORBIDDEN or ord(char) < 32:
            raise DbInitError(
                f"Nom de base invalide : {name!r}. Les caractères '/', '\\', '.' et "
                "les caractères de contrôle sont interdits dans un nom de base MariaDB "
                "(le trait d'union et le tiret bas restent admis)."
            )


def _check_required_env() -> None:
    """Vérifie que la configuration de provisioning est renseignée (ADR-067).

    Chargée dans les deux modes de `db:init` avant toute génération ou exécution :
    variables requises présentes et non vides, et `DB_NAME` valide. Sinon, arrêt
    avec un message explicite, sans rien produire.
    """
    load_project_config()
    missing = [
        key for key in _REQUIRED_PROVISIONING_ENV
        if not os.environ.get(key, "").strip()
    ]
    if missing:
        raise DbInitError(
            "Configuration de la base incomplète. "
            f"Renseignez ces variables dans env/dev : {', '.join(missing)}.\n"
            "  Amorcez-les au besoin avec : forge db:config"
        )
    _validate_db_name(os.environ.get("DB_NAME", ""))


def generate_provisioning_sql(cfg: ProvisioningEnv) -> str:
    """Rend le script SQL de provisioning MariaDB dérivé de `env/` (ADR-067).

    À exécuter par l'opérateur dans une session d'administration (ex. `sudo
    mariadb`). Forge ne se connecte pas et n'exige aucun droit serveur : les deux
    comptes créés sont scellés à `DB_NAME`, jamais accordés sur `*.*`.
    """
    database = _quote_identifier(cfg.db_name)
    admin_user = _quote_user(cfg.admin_login, cfg.host)
    app_user = _quote_user(cfg.app_login, cfg.host)
    app_privileges = ", ".join(cfg.app_privileges)
    return (
        "-- Généré par `forge db:init`. À exécuter dans une session\n"
        "-- d'administration MariaDB (ex. `sudo mariadb`).\n"
        "-- Forge ne demande jamais le root du serveur.\n"
        "\n"
        f"CREATE DATABASE IF NOT EXISTS {database}\n"
        f"  CHARACTER SET {cfg.db_charset} COLLATE {cfg.db_collation};\n"
        "\n"
        "-- Registre technique des migrations (ne requiert que CREATE sur la base).\n"
        f"USE {database};\n"
        f"{FORGE_MIGRATIONS_TABLE_SQL};\n"
        "\n"
        "-- Compte d'administration de la base : DDL du schéma (db:apply, migrations).\n"
        f"CREATE OR REPLACE USER {admin_user} IDENTIFIED BY {_quote_string(cfg.admin_password)};\n"
        f"GRANT ALL PRIVILEGES ON {database}.* TO {admin_user};\n"
        "\n"
        "-- Compte applicatif : runtime, DML uniquement.\n"
        f"CREATE OR REPLACE USER {app_user} IDENTIFIED BY {_quote_string(cfg.app_password)};\n"
        f"GRANT {app_privileges} ON {database}.* TO {app_user};\n"
        "\n"
        "FLUSH PRIVILEGES;\n"
    )


def _init_serverless(backend: Any) -> list[str]:
    """Init d'un backend sans serveur (ex. SQLite, ADR-054).

    Aucune base ni aucun compte à provisionner : on garantit la connexion
    (fichier créé au besoin) et la table technique forge_migrations.
    """
    from forge_mvc_entities.serverless_db import configure_serverless_db

    configure_serverless_db()

    actions: list[str] = []
    connection = backend.get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(backend.dialect.forge_migrations_ddl())
            connection.commit()
            actions.append(f"Base {os.environ.get('DB_NAME', '')} prête.")
            actions.append("Table forge_migrations prête.")
        finally:
            cursor.close()
    except Exception as exc:
        _rollback_quietly(connection)
        raise DbInitError(f"Initialisation {backend.name} impossible : {exc}") from exc
    finally:
        backend.close_connection(connection)
    return actions


def _record_backend_in_registry(project_root: Path, name: str) -> None:
    """Inscrit le backend actif dans optins/registry.py (ADR-061, best-effort).

    Silencieux si le registre est absent ou illisible : la commande db:init ne
    doit pas échouer à cause d'un fichier de registre (le squelette le porte
    toujours, mais un projet ancien peut ne pas l'avoir).
    """
    registry_path = project_root / "optins" / "registry.py"
    if not name or not registry_path.exists():
        return
    try:
        from cli.optins.registry_format import set_backend

        content = registry_path.read_text(encoding="utf-8")
        new_content = set_backend(content, name)
        if new_content != content:
            registry_path.write_text(new_content, encoding="utf-8")
    except OSError:
        return


def init_project_database() -> list[str]:
    from core.database.backend import get_backend

    backend = get_backend()
    _record_backend_in_registry(Path.cwd(), getattr(backend, "name", ""))
    if not getattr(backend, "requires_provisioning", True):
        # Backend sans serveur (SQLite) : ni base ni comptes à créer.
        return _init_serverless(backend)

    # Le provisioning ci-dessous (CREATE DATABASE / CREATE USER / GRANT) est
    # spécifique à MariaDB. Pour les autres SGBD serveur (PostgreSQL, SQL
    # Server), le provisioning automatique n'est pas encore implémenté : on
    # révèle clairement la limite plutôt que d'exécuter du SQL MariaDB qui
    # échouerait avec une erreur cryptique (charte, règle B).
    backend_name = getattr(backend, "name", "")
    if backend_name != "mariadb":
        raise DbInitError(
            f"`forge db:init` ne provisionne pas encore le backend "
            f"« {backend_name} ». Créez la base et le compte applicatif à la "
            f"main (voir le README du paquet forge-mvc-{backend_name}), puis "
            f"lancez `forge db:apply` pour créer les tables."
        )

    cfg = load_db_init_config()
    connection = _connect_admin()
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


def _print_actions(actions: list[str]) -> None:
    print("[OK] Base de données du projet prête.")
    for action in actions:
        print(f"[FAIT] {action}")


def _dispatch_db_init(*, run: bool) -> None:
    """Aiguille `db:init` (ADR-067).

    - défaut : **génère et affiche** le SQL de provisioning (MariaDB) ;
    - `--run` : **exécute** le provisioning ;
    - backend sans serveur (SQLite) : initialisation locale, sans identifiants ;
    - autre backend serveur non pris en charge : erreur explicite.
    """
    from core.database.backend import get_backend

    backend = get_backend()
    if not getattr(backend, "requires_provisioning", True):
        # SQLite : rien à générer, provisioning sans identifiants (les deux modes
        # exécutent l'initialisation locale).
        _print_actions(init_project_database())
        return

    name = getattr(backend, "name", "")
    if name != "mariadb":
        verb = "exécute" if run else "génère le SQL de"
        raise DbInitError(
            f"`forge db:init` ne {verb} pas encore le provisioning pour le backend "
            f"« {name} ». Créez la base et les comptes à la main (voir le README du "
            f"paquet forge-mvc-{name}), puis `forge db:apply`."
        )

    # MariaDB : vérification préalable dans les deux modes (ADR-067).
    _check_required_env()
    if run:
        _print_actions(init_project_database())
    else:
        print(generate_provisioning_sql(load_provisioning_env()))


def main(argv: list[str] | None = None) -> None:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    run = "--run" in args
    positional = [a for a in args if a != "--run"]
    if positional != ["db:init"]:
        print("Usage : forge db:init [--run]")
        raise SystemExit(1)

    try:
        _dispatch_db_init(run=run)
    except (DbInitError, ProjectConfigError, ValueError) as exc:
        print(f"[ERREUR] {exc}")
        raise SystemExit(1)


def _connect_admin():
    from core.database.backend import get_backend

    try:
        # ADR-060 : le backend lit DB_ADMIN_* dans l'environnement ; database=None
        # cible la base de maintenance du serveur pour créer la base du projet.
        return get_backend().get_admin_connection()
    except Exception as exc:
        raise DbInitError(
            "Connexion d'administration impossible. "
            "Vérifiez DB_ADMIN_* dans env/dev.\n"
            f"  Cause : {exc}"
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
