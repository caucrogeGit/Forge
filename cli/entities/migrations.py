# pyright: strict
# pyright: reportPrivateUsage=false
"""Statut des migrations SQL Forge."""

from __future__ import annotations
from typing import Any, cast

import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from cli.entities.canonical_model_normalizer import normalize_canonical_entity_for_model_build
from cli.entities.db_apply import _split_sql_statements
from cli.entities.make_entity import _sql_default_literal, to_snake, validate_entity_name
from cli.entities.validation import validate_entity_definition
from cli.project.project_config import ProjectConfigError, load_project_config

MIGRATIONS_DIR = Path("mvc") / "migrations"
MIGRATION_FILENAME_RE = re.compile(r"^(\d{14})_([A-Za-z0-9_]+)\.sql$")
MIGRATION_NAME_RE = re.compile(r"^[A-Za-z0-9 _-]+$")
SELECT_APPLIED_MIGRATIONS_SQL = (
    "SELECT version, name, filename, checksum "
    "FROM forge_migrations "
    "ORDER BY version"
)
INSERT_APPLIED_MIGRATION_SQL = (
    "INSERT INTO forge_migrations "
    "(version, name, filename, checksum, applied_at, execution_ms) "
    "VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)"
)
SELECT_TABLE_COLUMNS_SQL = (
    "SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, EXTRA "
    "FROM information_schema.COLUMNS "
    "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? "
    "ORDER BY ORDINAL_POSITION"
)


class MigrationError(ValueError):
    """Erreur de lecture des migrations."""


class MigrationNoChange(Exception):
    """Aucune migration ne doit être créée."""


@dataclass(frozen=True)
class MigrationDbConfig:
    host: str
    port: int
    login: str
    password: str
    database: str


@dataclass(frozen=True)
class MigrationFile:
    version: str
    name: str
    filename: str
    checksum: str
    path: Path


@dataclass(frozen=True)
class AppliedMigration:
    version: str
    name: str
    filename: str
    checksum: str


@dataclass(frozen=True)
class MigrationStatus:
    status: str
    version: str
    filename: str


@dataclass(frozen=True)
class MigrationStatusReport:
    statuses: list[MigrationStatus]
    migrations_dir_missing: bool = False


@dataclass(frozen=True)
class ExpectedColumn:
    name: str
    sql_type: str
    nullable: bool
    auto_increment: bool


@dataclass(frozen=True)
class ActualColumn:
    name: str
    sql_type: str
    nullable: bool
    auto_increment: bool


@dataclass(frozen=True)
class SchemaDiffRow:
    status: str
    column: str
    detail: str


@dataclass(frozen=True)
class SchemaDiffReport:
    entity: str
    table: str
    table_status: str
    rows: list[SchemaDiffRow]


def slugify_migration_name(name: str) -> str:
    raw_name = name.strip()
    if not raw_name:
        raise MigrationError("Le nom de migration ne peut pas être vide.")
    if not MIGRATION_NAME_RE.fullmatch(raw_name):
        raise MigrationError(
            "Nom de migration invalide. Utilisez uniquement lettres, chiffres, espaces, _ ou -."
        )
    slug = re.sub(r"[\s-]+", "_", raw_name.lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug:
        raise MigrationError("Le nom de migration ne peut pas être vide.")
    return slug


def parse_migration_filename(filename: str) -> tuple[str, str]:
    match = MIGRATION_FILENAME_RE.fullmatch(filename)
    if not match:
        raise MigrationError(
            "Nom de fichier de migration invalide : "
            f"{filename}. Format attendu : YYYYMMDDHHMMSS_nom_de_migration.sql"
        )
    return match.group(1), match.group(2)


def migration_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_migration_files(migrations_dir: Path = MIGRATIONS_DIR) -> tuple[list[MigrationFile], bool]:
    if not migrations_dir.exists():
        return [], True
    if not migrations_dir.is_dir():
        raise MigrationError(f"{migrations_dir.as_posix()} existe mais n'est pas un dossier.")

    migrations: list[MigrationFile] = []
    for path in sorted(migrations_dir.glob("*.sql")):
        version, name = parse_migration_filename(path.name)
        migrations.append(
            MigrationFile(
                version=version,
                name=name,
                filename=path.name,
                checksum=migration_checksum(path),
                path=path,
            )
        )
    return migrations, False


def load_applied_migrations(db: Any = None) -> list[AppliedMigration]:
    connection = db or _connect_db()
    should_close = db is None

    try:
        cursor = connection.cursor()
        try:
            try:
                cursor.execute(SELECT_APPLIED_MIGRATIONS_SQL)
            except Exception as exc:
                raise MigrationError(
                    "Lecture de forge_migrations impossible. "
                    "Lancez d'abord : forge db:init"
                ) from exc
            rows = cursor.fetchall()
        finally:
            cursor.close()
    finally:
        if should_close:
            connection.close()

    return [
        AppliedMigration(
            version=str(row[0]),
            name=str(row[1]),
            filename=str(row[2]),
            checksum=str(row[3]),
        )
        for row in rows
    ]


def build_migration_status(
    local_migrations: list[MigrationFile],
    applied_migrations: list[AppliedMigration],
) -> list[MigrationStatus]:
    local_by_version = {migration.version: migration for migration in local_migrations}
    applied_by_version = {migration.version: migration for migration in applied_migrations}

    statuses: list[MigrationStatus] = []
    for version in sorted(set(local_by_version) | set(applied_by_version)):
        local = local_by_version.get(version)
        applied = applied_by_version.get(version)
        if local and applied:
            status = "APPLIED" if local.checksum == applied.checksum else "CHANGED"
            statuses.append(MigrationStatus(status, version, local.filename))
        elif local:
            statuses.append(MigrationStatus("PENDING", version, local.filename))
        elif applied:
            statuses.append(MigrationStatus("MISSING", version, applied.filename))
    return statuses


def get_migration_status(
    migrations_dir: Path = MIGRATIONS_DIR,
    *,
    db: Any = None,
) -> MigrationStatusReport:
    local_migrations, migrations_dir_missing = collect_migration_files(migrations_dir)
    applied_migrations = load_applied_migrations(db=db)
    return MigrationStatusReport(
        statuses=build_migration_status(local_migrations, applied_migrations),
        migrations_dir_missing=migrations_dir_missing,
    )


def apply_pending_migrations(
    migrations_dir: Path = MIGRATIONS_DIR,
    *,
    db: Any = None,
    dry_run: bool = False,
) -> list[MigrationFile]:
    connection = db or _connect_db()
    should_close = db is None

    try:
        local_migrations, _missing_dir = collect_migration_files(migrations_dir)
        applied_migrations = load_applied_migrations(db=connection)
        statuses = build_migration_status(local_migrations, applied_migrations)
        _ensure_migrations_can_be_applied(statuses)

        pending_versions = {item.version for item in statuses if item.status == "PENDING"}
        pending = [
            migration
            for migration in sorted(local_migrations, key=lambda item: item.version)
            if migration.version in pending_versions
        ]
        # dry-run : on retourne ce qui SERAIT appliqué sans rien exécuter.
        if dry_run:
            return pending

        applied: list[MigrationFile] = []
        for migration in pending:
            _apply_one_migration(connection, migration)
            applied.append(migration)
        return applied
    finally:
        if should_close:
            connection.close()


def make_migration_file(
    name: str,
    migrations_dir: Path = MIGRATIONS_DIR,
    *,
    now: datetime | None = None,
    from_entity: str | None = None,
    from_entities: bool = False,
    from_diff: str | None = None,
    project_root: Path | None = None,
    db: Any = None,
    database: str | None = None,
) -> Path:
    sources = [from_entity is not None, from_entities, from_diff is not None]
    if sum(1 for enabled in sources if enabled) > 1:
        raise MigrationError(
            "Utilisez une seule source : --from-entity, --from-entities ou --from-diff."
        )
    slug = slugify_migration_name(name)
    version = (now or datetime.now()).strftime("%Y%m%d%H%M%S")
    filename = f"{version}_{slug}.sql"
    # Vérifie que le nom généré reste compatible avec status/apply.
    parse_migration_filename(filename)

    path = migrations_dir / filename
    root = project_root or Path.cwd()
    if from_entities:
        content = _migration_file_template_from_entities(version, slug, root)
    elif from_entity is not None:
        content = _migration_file_template_from_entity(version, slug, from_entity, root)
    elif from_diff is not None:
        content = _migration_file_template_from_diff(
            version,
            slug,
            from_diff,
            root,
            db=db,
            database=database,
        )
    else:
        content = _migration_file_template(version, slug)
    migrations_dir.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as file:
            file.write(content)
    except FileExistsError as exc:
        raise MigrationError(f"Migration déjà existante : {path.as_posix()}") from exc
    return path


def diff_entity_schema(
    entity_name: str,
    *,
    project_root: Path | None = None,
    db: Any = None,
    database: str | None = None,
) -> SchemaDiffReport:
    root = project_root or Path.cwd()
    definition = load_entity_definition(entity_name, project_root=root)
    table = definition["table"]
    expected = [
        ExpectedColumn(
            name=field["column"],
            sql_type=field["sql_type"],
            nullable=field["nullable"],
            auto_increment=field["auto_increment"],
        )
        for field in definition["fields"]
    ]
    actual = load_table_columns(table, db=db, database=database)
    return build_schema_diff_report(definition["entity"], table, expected, actual)


def entity_json_file_path(entity_name: str, *, project_root: Path | None = None) -> Path:
    validated = validate_entity_name(entity_name)
    snake = to_snake(validated)
    root = project_root or Path.cwd()
    path = root / "mvc" / "entities" / snake / f"{snake}.json"
    if not path.exists() or not path.is_file():
        raise MigrationError(f"JSON d'entité introuvable : {path.as_posix()}")
    return path


def load_entity_definition(entity_name: str, *, project_root: Path | None = None) -> dict[str, Any]:
    root = project_root or Path.cwd()
    json_path = entity_json_file_path(entity_name, project_root=root)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and cast("dict[str, Any]", data).get("schema_version") == "1.0":
        data = normalize_canonical_entity_for_model_build(cast("dict[str, Any]", data))
    return validate_entity_definition(data, source=str(json_path))


def load_table_columns(
    table: str,
    *,
    db: Any = None,
    database: str | None = None,
) -> list[ActualColumn]:
    connection = db or _connect_db()
    should_close = db is None
    db_name = database or load_migration_db_config().database

    try:
        cursor = connection.cursor()
        try:
            try:
                cursor.execute(SELECT_TABLE_COLUMNS_SQL, (db_name, table))
            except Exception as exc:
                raise MigrationError(
                    "Lecture du schéma MariaDB impossible. Vérifiez DB_ADMIN_* / DB_NAME dans env/dev."
                ) from exc
            rows = cursor.fetchall()
        finally:
            cursor.close()
    finally:
        if should_close:
            connection.close()

    return [
        ActualColumn(
            name=str(row[0]),
            sql_type=str(row[1]),
            nullable=str(row[2]).upper() == "YES",
            auto_increment="auto_increment" in str(row[3]).lower(),
        )
        for row in rows
    ]


def build_schema_diff_report(
    entity: str,
    table: str,
    expected: list[ExpectedColumn],
    actual: list[ActualColumn],
) -> SchemaDiffReport:
    if not actual:
        return SchemaDiffReport(
            entity=entity,
            table=table,
            table_status="TABLE_MISSING",
            rows=[SchemaDiffRow("TABLE_MISSING", "-", "table absente en base")],
        )

    actual_by_name = {column.name: column for column in actual}
    expected_by_name = {column.name: column for column in expected}
    rows: list[SchemaDiffRow] = []

    for column in expected:
        found = actual_by_name.get(column.name)
        if found is None:
            rows.append(
                SchemaDiffRow("COLUMN_MISSING", column.name, "présente dans JSON, absente en base")
            )
            continue
        changes = _column_changes(column, found)
        if changes:
            rows.append(SchemaDiffRow("COLUMN_CHANGED", column.name, "; ".join(changes)))
        else:
            rows.append(SchemaDiffRow("OK", column.name, "identique"))

    for column in sorted(actual, key=lambda item: item.name):
        if column.name not in expected_by_name:
            rows.append(
                SchemaDiffRow("COLUMN_EXTRA", column.name, "présente en base, absente du JSON")
            )

    table_status = "OK" if all(row.status == "OK" for row in rows) else "COLUMN_CHANGED"
    return SchemaDiffReport(entity=entity, table=table, table_status=table_status, rows=rows)


def main(argv: list[str] | None = None) -> None:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in {"migration:status", "migration:apply", "migration:make", "migration:diff"}:
        print("Usage : forge migration:status")
        print("Usage : forge migration:apply")
        print("Usage : forge migration:make <nom>")
        print("Usage : forge migration:make <nom> --from-diff <Entite>")
        print("Usage : forge migration:diff --entity <Entite>")
        raise SystemExit(1)
    if args[0] == "migration:status" and len(args) != 1:
        print(f"Usage : forge {args[0]}")
        raise SystemExit(1)
    if args[0] == "migration:apply" and args[1:] not in ([], ["--dry-run"], ["--help"]):
        print("Usage : forge migration:apply [--dry-run]")
        raise SystemExit(1)
    if args[0] == "migration:make" and not _is_valid_make_args(args):
        print("Usage : forge migration:make <nom>")
        print("Usage : forge migration:make <nom> --from-entity <Entite>")
        print("Usage : forge migration:make <nom> --from-entities")
        print("Usage : forge migration:make <nom> --from-diff <Entite>")
        raise SystemExit(1)
    if args[0] == "migration:diff" and not _is_valid_diff_args(args):
        print("Usage : forge migration:diff --entity <Entite>")
        raise SystemExit(1)

    if "--help" in args:
        cmd = args[0]
        if cmd == "migration:make":
            print("Usage : forge migration:make <nom>")
            print("        forge migration:make <nom> --from-entity <Entite>")
            print("        forge migration:make <nom> --from-entities")
            print("        forge migration:make <nom> --from-diff <Entite>")
            print()
            print("Génère un fichier de migration SQL dans mvc/migrations/.")
            print()
            print("Options :")
            print("  --from-entity <Entite>   SQL depuis le fichier .sql de l'entité")
            print("  --from-entities          SQL depuis toutes les entités")
            print("  --from-diff <Entite>     SQL depuis le diff entité/base")
        elif cmd == "migration:status":
            print("Usage : forge migration:status")
            print()
            print("Affiche le statut des migrations (PENDING, APPLIED, CHANGED, MISSING).")
        elif cmd == "migration:apply":
            print("Usage : forge migration:apply")
            print()
            print("Applique les migrations PENDING dans mvc/migrations/.")
        elif cmd == "migration:diff":
            print("Usage : forge migration:diff --entity <Entite>")
            print()
            print("Affiche le diff entre le schéma JSON d'une entité et la base.")
            print()
            print("Options requises :")
            print("  --entity <Entite>   nom de l'entité à comparer")
        raise SystemExit(0)

    try:
        if args[0] == "migration:status":
            _run_status_command()
        elif args[0] == "migration:apply":
            _run_apply_command(args)
        elif args[0] == "migration:make":
            _run_make_command(args)
        else:
            _run_diff_command(args)
    except (MigrationError, ProjectConfigError, ValueError) as exc:
        print(f"[ERREUR] {exc}")
        raise SystemExit(1)


def _assert_migration_contracts_valid(entities_root: Path) -> None:
    """Vérifie les contrats JSON Schema avant génération/comparaison. Dégradation douce si jsonschema absent."""
    from cli.entities.entity_validate import collect_entity_validation_results
    results = collect_entity_validation_results(entities_root)
    if results is not None and results["errors"]:
        print("[ERREUR] Les entités Forge sont invalides.")
        print("Conseil : lancez forge entity:validate pour obtenir le détail.")
        raise SystemExit(1)


def _run_status_command() -> None:
    report = get_migration_status()
    print("[OK] Statut des migrations.")
    if report.migrations_dir_missing:
        print("[INFO] Dossier mvc/migrations absent : aucune migration locale disponible.")
    if not report.statuses:
        print("Aucune migration trouvée.")
        return
    print()
    _print_status_table(report.statuses)


def _run_apply_command(args: list[str]) -> None:
    dry_run = "--dry-run" in args
    result = apply_pending_migrations(dry_run=dry_run)

    if dry_run:
        if not result:
            print("[DRY-RUN] Aucune migration à appliquer.")
            return
        print(f"[DRY-RUN] {len(result)} migration(s) seraient appliquées (rien n'est écrit) :")
        for migration in result:
            print(f"  • {migration.filename}")
            sql = migration.path.read_text(encoding="utf-8").strip()
            print("      " + sql.replace("\n", "\n      "))
        print("[DRY-RUN] Relance sans --dry-run pour appliquer réellement.")
        return

    print("[OK] Application des migrations.")
    if not result:
        print("Aucune migration à appliquer.")
        return
    for migration in result:
        print(f"[EXECUTE] {migration.filename}")
    print(f"[OK] {len(result)} migration(s) appliquée(s).")


def _run_make_command(args: list[str]) -> None:
    name = args[1]
    from_entity = None
    from_entities = False
    from_diff = None
    if len(args) == 4 and args[2] == "--from-entity":
        from_entity = args[3]
    elif len(args) == 4 and args[2] == "--from-diff":
        from_diff = args[3]
    elif len(args) == 3 and args[2] == "--from-entities":
        from_entities = True
    if from_diff is not None:
        _assert_migration_contracts_valid(Path.cwd() / "mvc" / "entities")
    try:
        path = make_migration_file(
            name,
            from_entity=from_entity,
            from_entities=from_entities,
            from_diff=from_diff,
        )
    except MigrationNoChange as exc:
        print(str(exc))
        return
    print(f"[OK] Migration créée : {path.as_posix()}")


def _run_diff_command(args: list[str]) -> None:
    _assert_migration_contracts_valid(Path.cwd() / "mvc" / "entities")
    report = diff_entity_schema(args[2])
    print(f"[OK] Diff de schéma pour l’entité {report.entity}.")
    print()
    print(f"TABLE {report.table} : {report.table_status}")
    print()
    _print_schema_diff_table(report.rows)


def _print_status_table(statuses: list[MigrationStatus]) -> None:
    headers = ["STATUT", "VERSION", "FICHIER"]
    rows = [[item.status, item.version, item.filename] for item in statuses]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def _print_schema_diff_table(rows: list[SchemaDiffRow]) -> None:
    headers = ["STATUT", "COLONNE", "DETAIL"]
    values = [[row.status, row.column, row.detail] for row in rows]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in values))
        for index in range(len(headers))
    ]
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    for row in values:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def _ensure_migrations_can_be_applied(statuses: list[MigrationStatus]) -> None:
    changed = [item.filename for item in statuses if item.status == "CHANGED"]
    missing = [item.filename for item in statuses if item.status == "MISSING"]
    if changed:
        raise MigrationError(
            "Application refusée : migration locale modifiée après application : "
            + ", ".join(changed)
        )
    if missing:
        raise MigrationError(
            "Application refusée : migration enregistrée absente du dossier local : "
            + ", ".join(missing)
        )


def _apply_one_migration(connection: Any, migration: MigrationFile) -> None:
    sql = migration.path.read_text(encoding="utf-8")
    statements = _split_sql_statements(sql)
    start = time.perf_counter()
    cursor = connection.cursor()
    try:
        try:
            for statement in statements:
                cursor.execute(statement)
            execution_ms = int((time.perf_counter() - start) * 1000)
            cursor.execute(
                INSERT_APPLIED_MIGRATION_SQL,
                (
                    migration.version,
                    migration.name,
                    migration.filename,
                    migration.checksum,
                    execution_ms,
                ),
            )
            connection.commit()
        except Exception as exc:
            _rollback_quietly(connection)
            raise MigrationError(
                f"{migration.filename}: erreur SQL pendant l'application : {exc}"
            ) from exc
    finally:
        cursor.close()


def _migration_file_template(version: str, name: str) -> str:
    return (
        "-- Migration Forge\n"
        f"-- Version: {version}\n"
        f"-- Name: {name}\n"
        "-- Write your SQL below.\n"
        "\n"
        "-- Example:\n"
        "-- CREATE TABLE example (\n"
        "--     id INT NOT NULL AUTO_INCREMENT PRIMARY KEY\n"
        "-- );\n"
    )


def _migration_file_template_from_entity(
    version: str,
    name: str,
    entity_name: str,
    project_root: Path,
) -> str:
    entity_sql_path = entity_sql_file_path(entity_name, project_root=project_root)
    sql = entity_sql_path.read_text(encoding="utf-8")
    if not sql.endswith("\n"):
        sql += "\n"
    return (
        "-- Migration Forge\n"
        f"-- Version: {version}\n"
        f"-- Name: {name}\n"
        f"-- Source: entity {validate_entity_name(entity_name)}\n"
        f"-- Generated from: {entity_sql_path.as_posix()}\n"
        "--\n"
        "-- Review this SQL before running:\n"
        "-- forge migration:apply\n"
        "\n"
        f"{sql}"
    )


def _migration_file_template_from_entities(
    version: str,
    name: str,
    project_root: Path,
) -> str:
    paths = entity_sql_file_paths(project_root=project_root)
    parts = [
        "-- Migration Forge",
        f"-- Version: {version}",
        f"-- Name: {name}",
        "-- Source: all entities",
        "-- Generated from: mvc/entities/*/*.sql",
        "--",
        "-- Review this SQL before running:",
        "-- forge migration:apply",
        "",
    ]
    for path in paths:
        relative_path = path.relative_to(project_root).as_posix()
        sql = path.read_text(encoding="utf-8")
        if not sql.endswith("\n"):
            sql += "\n"
        parts.extend(
            [
                "-- ============================================================",
                f"-- Entity SQL: {relative_path}",
                "-- ============================================================",
                "",
                sql.rstrip("\n"),
                "",
            ]
        )
    return "\n".join(parts).rstrip() + "\n"


def _migration_file_template_from_diff(
    version: str,
    name: str,
    entity_name: str,
    project_root: Path,
    *,
    db: Any = None,
    database: str | None = None,
) -> str:
    sql = entity_diff_migration_sql(
        entity_name,
        project_root=project_root,
        db=db,
        database=database,
    )
    entity_json_path = entity_json_file_path(entity_name, project_root=project_root)
    return (
        "-- Migration Forge\n"
        f"-- Version: {version}\n"
        f"-- Name: {name}\n"
        f"-- Source: diff entity {validate_entity_name(entity_name)}\n"
        f"-- Generated from: {entity_json_path.relative_to(project_root).as_posix()}\n"
        "--\n"
        "-- Review this SQL before running:\n"
        "-- forge migration:apply\n"
        "\n"
        f"{sql.rstrip()}\n"
    )


def entity_diff_migration_sql(
    entity_name: str,
    *,
    project_root: Path | None = None,
    db: Any = None,
    database: str | None = None,
) -> str:
    root = project_root or Path.cwd()
    definition = load_entity_definition(entity_name, project_root=root)
    report = diff_entity_schema(entity_name, project_root=root, db=db, database=database)

    risky = [row.status for row in report.rows if row.status in {"COLUMN_CHANGED", "COLUMN_EXTRA"}]
    if risky:
        raise MigrationError(
            f"Diff risqué détecté : {risky[0]}. Créez une migration manuelle."
        )

    if report.table_status == "TABLE_MISSING":
        entity_sql_path = entity_sql_file_path(entity_name, project_root=root)
        sql = entity_sql_path.read_text(encoding="utf-8")
        return sql if sql.endswith("\n") else f"{sql}\n"

    missing_columns = [row.column for row in report.rows if row.status == "COLUMN_MISSING"]
    if not missing_columns:
        raise MigrationNoChange(f"Aucun changement détecté pour l’entité {report.entity}.")

    fields_by_column = {field["column"]: field for field in definition["fields"]}
    add_lines = [
        f"    ADD COLUMN {_quote_sql_identifier(column)} {_sql_column_definition(fields_by_column[column])}"
        for column in missing_columns
    ]
    return (
        f"ALTER TABLE {_quote_sql_identifier(definition['table'])}\n"
        + ",\n".join(add_lines)
        + ";\n"
    )


def entity_sql_file_path(entity_name: str, *, project_root: Path | None = None) -> Path:
    validated = validate_entity_name(entity_name)
    snake = to_snake(validated)
    root = project_root or Path.cwd()
    path = root / "mvc" / "entities" / snake / f"{snake}.sql"
    if not path.exists() or not path.is_file():
        raise MigrationError(
            "SQL d'entité introuvable. "
            f"Lancez d'abord forge sync:entity {validated} ou forge build:model."
        )
    return path


def entity_sql_file_paths(*, project_root: Path | None = None) -> list[Path]:
    root = project_root or Path.cwd()
    entities_root = root / "mvc" / "entities"
    paths = sorted(path for path in entities_root.glob("*/*.sql") if path.is_file())
    if not paths:
        raise MigrationError("Aucun SQL d'entité trouvé dans mvc/entities/*/*.sql.")
    return paths


def _is_valid_make_args(args: list[str]) -> bool:
    if len(args) == 2:
        return True
    if len(args) == 3:
        return args[2] == "--from-entities"
    return len(args) == 4 and args[2] in {"--from-entity", "--from-diff"}


def _is_valid_diff_args(args: list[str]) -> bool:
    return len(args) == 3 and args[1] == "--entity"


def _normalize_sql_type(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().upper())


def _column_changes(expected: ExpectedColumn, actual: ActualColumn) -> list[str]:
    changes: list[str] = []
    expected_type = _normalize_sql_type(expected.sql_type)
    actual_type = _normalize_sql_type(actual.sql_type)
    if expected_type != actual_type:
        changes.append(f"type attendu {expected_type}, trouvé {actual_type}")
    if expected.nullable != actual.nullable:
        changes.append(
            "nullable attendu "
            f"{'YES' if expected.nullable else 'NO'}, trouvé {'YES' if actual.nullable else 'NO'}"
        )
    if expected.auto_increment != actual.auto_increment:
        changes.append(
            "auto_increment attendu "
            f"{'oui' if expected.auto_increment else 'non'}, trouvé {'oui' if actual.auto_increment else 'non'}"
        )
    return changes


def _quote_sql_identifier(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", identifier):
        raise MigrationError(f"Identifiant SQL invalide : {identifier}")
    return f"`{identifier}`"


def _sql_column_definition(field: dict[str, Any]) -> str:
    parts = [str(field["sql_type"])]
    parts.append("NULL" if field["nullable"] else "NOT NULL")
    if field["auto_increment"]:
        parts.append("AUTO_INCREMENT")
    default_literal = _sql_default_literal(field)
    if default_literal is not None:
        parts.append(f"DEFAULT {default_literal}")
    return " ".join(parts)


def _connect_db():
    import mariadb  # pyright: ignore[reportMissingTypeStubs]

    cfg = load_migration_db_config()
    try:
        return cast("Any", mariadb).connect(
            host=cfg.host,
            port=cfg.port,
            user=cfg.login,
            password=cfg.password,
            database=cfg.database,
        )
    except Exception as exc:
        raise MigrationError(
            "Connexion MariaDB admin impossible. "
            "Vérifiez DB_ADMIN_* / DB_NAME dans env/dev."
        ) from exc


def load_migration_db_config() -> MigrationDbConfig:
    config = load_project_config()

    # ADR-033 : les migrations sont des changements de structure ; elles
    # utilisent le compte d'administration du projet (DB_ADMIN_*), pas le compte
    # runtime DB_APP_* qui reste en DML strict.
    return MigrationDbConfig(
        host=config.DB_ADMIN_HOST,
        port=config.DB_ADMIN_PORT,
        login=config.DB_ADMIN_LOGIN,
        password=config.DB_ADMIN_PWD,
        database=config.DB_NAME,
    )


def _rollback_quietly(connection: Any) -> None:
    try:
        connection.rollback()
    except Exception:
        pass
