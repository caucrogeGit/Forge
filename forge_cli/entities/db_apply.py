"""Application SQL du modele d'entites Forge."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from forge_cli.entities.model import ModelValidationError, check_model
from forge_cli.project_config import ProjectConfigError, load_project_config


@dataclass(frozen=True)
class SqlFileToApply:
    path: Path
    required: bool


class DbApplyError(ValueError):
    """Erreur d'application SQL du modele."""


@dataclass(frozen=True)
class DbApplyConfig:
    host: str
    port: int
    login: str
    password: str
    database: str


def apply_model_sql(entities_root: Path) -> list[Path]:
    if not entities_root.exists():
        raise DbApplyError(
            f"Projet Forge introuvable : {entities_root.as_posix()} absent."
        )
    check_model(entities_root)
    sql_files = collect_sql_files(entities_root)
    sql_contents = verify_sql_files(sql_files)
    connection = _connect_db()
    applied: list[Path] = []

    try:
        cursor = connection.cursor()
        try:
            for item in sql_files:
                sql = sql_contents[item.path]
                if not sql.strip():
                    continue
                for statement in _split_sql_statements(sql):
                    try:
                        cursor.execute(statement)
                    except Exception as exc:
                        _rollback_quietly(connection)
                        raise DbApplyError(
                            f"{item.path}: erreur SQL pendant l'execution : {exc}"
                        ) from exc
                applied.append(item.path)
            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()

    return applied


def collect_sql_files(entities_root: Path) -> list[SqlFileToApply]:
    entity_files: list[SqlFileToApply] = []
    for entity_dir in sorted(
        (path for path in entities_root.iterdir() if path.is_dir() and not path.name.startswith("__")),
        key=lambda path: path.name,
    ):
        entity_files.append(SqlFileToApply(path=entity_dir / f"{entity_dir.name}.sql", required=True))
    entity_files.append(SqlFileToApply(path=entities_root / "relations.sql", required=False))
    return entity_files


def verify_sql_files(files: list[SqlFileToApply]) -> dict[Path, str]:
    contents: dict[Path, str] = {}
    issues: list[str] = []

    for item in files:
        if not item.path.exists():
            if item.required:
                issues.append(f"{item.path}: fichier SQL d'entite introuvable")
            else:
                issues.append(f"{item.path}: fichier SQL de relations introuvable")
            continue

        content = item.path.read_text(encoding="utf-8")
        if item.required and not content.strip():
            issues.append(f"{item.path}: fichier SQL d'entite vide")
        contents[item.path] = content

    if issues:
        raise DbApplyError("\n".join(issues))
    return contents


def main(argv: list[str] | None = None) -> None:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] != "db:apply":
        print("Usage : forge db:apply")
        raise SystemExit(1)

    entities_root = Path("mvc") / "entities"
    relations_path = entities_root / "relations.sql"

    try:
        applied = apply_model_sql(entities_root)
        print("[OK] SQL du modele applique.")
        for path in applied:
            print(f"[EXECUTE] {path.as_posix()}")
        if relations_path.exists() and not relations_path.read_text(encoding="utf-8").strip():
            print(f"[NO-OP] {relations_path.as_posix()} est vide.")
    except (ModelValidationError, DbApplyError, ProjectConfigError, ValueError) as exc:
        print(f"[ERREUR] {exc}")
        raise SystemExit(1)


def _connect_db():
    import mariadb

    cfg = load_db_apply_config()
    try:
        return mariadb.connect(
            host=cfg.host,
            port=cfg.port,
            user=cfg.login,
            password=cfg.password,
            database=cfg.database,
        )
    except Exception as exc:
        raise DbApplyError(
            "Connexion MariaDB applicative impossible. "
            "La base du projet n'est peut-être pas préparée. Lancez d'abord `forge db:init` "
            "ou vérifiez DB_APP_* / DB_NAME dans env/dev."
        ) from exc


def load_db_apply_config() -> DbApplyConfig:
    config = load_project_config()

    return DbApplyConfig(
        host=config.DB_APP_HOST,
        port=config.DB_APP_PORT,
        login=config.DB_APP_LOGIN,
        password=config.DB_APP_PWD,
        database=config.DB_NAME,
    )


def _rollback_quietly(connection: Any) -> None:
    try:
        connection.rollback()
    except Exception:
        pass


def _split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single_quote = False

    for char in sql:
        if char == "'":
            in_single_quote = not in_single_quote
        if char == ";" and not in_single_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            continue
        current.append(char)

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements
