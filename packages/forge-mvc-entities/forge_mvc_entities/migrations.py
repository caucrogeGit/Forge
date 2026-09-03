# pyright: strict
"""Statut des migrations SQL Forge."""

from __future__ import annotations
from typing import Any, cast

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from forge_mvc_entities.canonical_model_normalizer import normalize_canonical_entity_for_model_build
from forge_mvc_entities.db_apply import split_sql_statements
from forge_mvc_entities.make_entity import sql_default_literal, to_snake, validate_entity_name
from forge_mvc_entities.validation import validate_entity_definition
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
# Journal de reprise (MIGRATION-RESUME-JOURNAL-001), tenu uniquement sur un
# backend qui ne sait pas annuler la DDL : une ligne par instruction ayant pris
# effet, effacée quand la migration entière aboutit.
SELECT_MIGRATION_STEPS_SQL = (
    "SELECT version, position, statement_checksum "
    "FROM forge_migration_steps "
    "ORDER BY version, position"
)
INSERT_MIGRATION_STEP_SQL = (
    "INSERT INTO forge_migration_steps "
    "(version, position, statement_checksum, applied_at) "
    "VALUES (?, ?, ?, CURRENT_TIMESTAMP)"
)
DELETE_MIGRATION_STEPS_SQL = "DELETE FROM forge_migration_steps WHERE version = ?"
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
    # ADR-060 : identifiants d'administration lus par le backend depuis
    # l'environnement ; seul le nom de la base cible reste porté ici.
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

        # Le journal de reprise est lu une fois : vide sur un backend
        # transactionnel ou sans échec antérieur (MIGRATION-RESUME-JOURNAL-001).
        recorded_steps = (
            {} if _ddl_is_transactional() else load_migration_steps(connection)
        )
        applied: list[MigrationFile] = []
        for migration in pending:
            _apply_one_migration(connection, migration, recorded_steps=recorded_steps)
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
    with_relations: bool = False,
    project_root: Path | None = None,
    db: Any = None,
    database: str | None = None,
) -> Path:
    sources = [from_entity is not None, from_entities, from_diff is not None]
    if sum(1 for enabled in sources if enabled) > 1:
        raise MigrationError(
            "Utilisez une seule source : --from-entity, --from-entities ou --from-diff."
        )
    if with_relations and not (from_entities or from_entity is not None):
        raise MigrationError(
            "--with-relations exige --from-entity <Entite> ou --from-entities."
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
        if with_relations:
            content += _relations_sql_block(root)
    elif from_entity is not None:
        content = _migration_file_template_from_entity(version, slug, from_entity, root)
        if with_relations:
            content += _relations_sql_block(root, from_entity=from_entity)
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
    from core.database.backend import get_backend

    backend = get_backend()
    connection = db or _connect_db()
    should_close = db is None
    # Le nom de base n'est utile qu'aux SGBD serveur (TABLE_SCHEMA) ; un backend
    # fichier (SQLite) l'ignore.
    db_name = ""
    if backend.requires_provisioning:
        db_name = database or load_migration_db_config().database

    try:
        try:
            rows = backend.dialect.introspect_columns(connection, table, db_name)
        except MigrationError:
            raise
        except Exception as exc:
            raise MigrationError(
                "Lecture du schéma impossible. Vérifiez la configuration BDD "
                "(DB_ADMIN_* / DB_NAME pour un SGBD serveur)."
            ) from exc
    finally:
        if should_close:
            connection.close()

    return [
        ActualColumn(
            name=str(row[0]),
            sql_type=str(row[1]),
            nullable=bool(row[2]),
            auto_increment=bool(row[3]),
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
            print("  --with-relations         Ajoute le SQL des relations (FK, index)")
            print("                           après les CREATE TABLE (tables puis contraintes)")
        elif cmd == "migration:status":
            print("Usage : forge migration:status")
            print()
            print("Affiche le statut des migrations (PENDING, APPLIED, CHANGED, MISSING).")
        elif cmd == "migration:apply":
            print("Usage : forge migration:apply")
            print()
            print("Applique les migrations PENDING dans mvc/migrations/.")
            print()
            print("Sur un backend qui ne sait pas annuler la DDL (MariaDB), une")
            print("migration interrompue reprend à la première instruction non")
            print("appliquée, grâce au journal de reprise (forge_migration_steps).")
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
    from forge_mvc_entities.entity_validate import collect_entity_validation_results
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
    # Une migration interrompue est PENDING au tableau (jamais enregistrée au
    # journal des migrations), mais son état réel est ailleurs : le journal de
    # reprise retient ce qui a déjà pris effet (MIGRATION-RESUME-JOURNAL-001).
    # Sur un backend transactionnel, il n'existe pas : rien à lire. Et le
    # statut reste un affichage : une base injoignable ne doit pas le casser.
    try:
        interrupted = {} if _ddl_is_transactional() else load_migration_steps()
    except Exception:  # noqa: BLE001 — statut best-effort, le tableau est déjà là
        interrupted = {}
    filenames = {item.version: item.filename for item in report.statuses}
    for version in sorted(interrupted):
        pas = len(interrupted[version])
        nom = filenames.get(version, version)
        print()
        print(
            f"[ATTENTION] {nom} : interrompue, {pas} instruction(s) déjà en base "
            "(journal de reprise)."
        )
        print(
            "  Corrigez l'instruction fautive puis relancez `forge migration:apply` : "
            f"la reprise continuera à l'instruction {pas + 1}."
        )


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
    # Le nom est obligatoire, et son absence rendait `IndexError: list index out
    # of range` en trace brute (WELCOME-EXECUTION-001, constaté en jouant le
    # parcours du moteur d'entités). Un argument manquant est une erreur
    # d'usage : elle appelle le rappel de l'usage, pas une trace.
    if len(args) < 2 or args[1].startswith("-"):
        print("[ERREUR] Nom de migration manquant.")
        print("Usage : forge migration:make <nom> [--from-entity <Entité>] "
              "[--from-entities] [--from-diff <Entité>] [--with-relations]")
        print("Exemple : forge migration:make ajout_colonne_resume")
        raise SystemExit(1)
    name = args[1]
    from_entity = None
    from_entities = False
    from_diff = None
    with_relations = "--with-relations" in args
    core = [a for a in args[2:] if a != "--with-relations"]
    if len(core) == 2 and core[0] == "--from-entity":
        from_entity = core[1]
    elif len(core) == 2 and core[0] == "--from-diff":
        from_diff = core[1]
    elif core == ["--from-entities"]:
        from_entities = True
    if from_diff is not None:
        _assert_migration_contracts_valid(Path.cwd() / "mvc" / "entities")
    try:
        path = make_migration_file(
            name,
            from_entity=from_entity,
            from_entities=from_entities,
            from_diff=from_diff,
            with_relations=with_relations,
        )
    except MigrationNoChange as exc:
        print(str(exc))
        return
    print(f"[OK] Migration créée : {path.as_posix()}")


#: Statuts qui signalent un écart entre le contrat et la base.
DIFF_DRIFT_STATUSES = frozenset({"COLUMN_MISSING", "COLUMN_CHANGED", "COLUMN_EXTRA"})


def summarize_schema_diff(report: SchemaDiffReport) -> "dict[str, int]":
    """Compte les lignes par statut (`ENTITIES-MIGRATION-DIFF-READABLE-001`).

    La commande rendait un tableau de lignes, sans total. Sur une entité de
    trente colonnes, savoir s'il reste un écart demandait de lire les trente
    lignes et de compter à la main, ce qui se fait mal et se fait faux.
    """
    compte: dict[str, int] = {}
    for row in report.rows:
        compte[row.status] = compte.get(row.status, 0) + 1
    return compte


def has_schema_drift(report: SchemaDiffReport) -> bool:
    """Vrai si le contrat et la base diffèrent.

    La table absente compte comme un écart : c'est même le plus grand.
    """
    if report.table_status != "OK":
        return True
    return any(row.status in DIFF_DRIFT_STATUSES for row in report.rows)


def _print_diff_summary(report: SchemaDiffReport) -> None:
    compte = summarize_schema_diff(report)
    total = sum(compte.values())
    ecarts = sum(nombre for statut, nombre in compte.items() if statut in DIFF_DRIFT_STATUSES)
    detail = ", ".join(f"{statut} {nombre}" for statut, nombre in sorted(compte.items()))
    print()
    print(f"RESUME : {total} colonne(s) examinée(s), {ecarts} écart(s). {detail or '<aucun>'}")
    if not has_schema_drift(report):
        print("Le contrat et la base sont d'accord.")


def _run_diff_command(args: list[str]) -> None:
    """`forge migration:diff <Entite> [--sql] [--check]`.

    `--sql` montre, sans rien écrire, la migration que `migration:make
    --from-diff` produirait. C'est l'essai à blanc du ticket
    `ENTITIES-MIGRATION-DIFF-READABLE-001` : lire le SQL avant de créer un
    fichier évite d'avoir à supprimer une migration qu'on vient d'engendrer.

    `--check` rend un code de sortie non nul quand un écart subsiste, pour une
    intégration continue. Le comportement par défaut reste inchangé : le faire
    échouer d'office aurait cassé les scripts qui appellent la commande
    aujourd'hui.
    """
    _assert_migration_contracts_valid(Path.cwd() / "mvc" / "entities")
    veut_sql = "--sql" in args
    veut_check = "--check" in args

    report = diff_entity_schema(args[2])
    print(f"[OK] Diff de schéma pour l’entité {report.entity}.")
    print()
    print(f"TABLE {report.table} : {report.table_status}")
    print()
    _print_schema_diff_table(report.rows)
    _print_diff_summary(report)

    if veut_sql:
        print()
        if not has_schema_drift(report):
            print("Aucun écart : il n'y a pas de migration à produire.")
        else:
            try:
                sql = entity_diff_migration_sql(args[2])
            except MigrationError as exc:
                # Un diff risqué ne se traduit pas en SQL automatiquement, et
                # le dire ici vaut mieux que de laisser l'exploitant découvrir
                # le refus au moment où il croyait créer sa migration.
                print(f"[ATTENTION] Aucun SQL automatique : {exc}")
            else:
                print("-- SQL qui serait engendré par migration:make --from-diff :")
                print(sql.rstrip())
                print()
                print(
                    "Rien n'a été écrit. Pour créer le fichier : "
                    f"forge migration:make <nom> --from-diff {report.entity}"
                )

    if veut_check and has_schema_drift(report):
        raise MigrationError(
            f"Écart de schéma pour {report.entity} : le contrat et la base "
            "diffèrent. Produisez une migration, ou appliquez celles qui "
            "manquent."
        )


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


_DDL_KEYWORDS = frozenset({"CREATE", "ALTER", "DROP", "RENAME", "TRUNCATE"})


def _contains_ddl(statements: "list[str]") -> bool:
    """Vrai si la migration porte au moins une instruction de définition.

    C'est la DDL, et elle seule, qui brise l'atomicité sur MariaDB : une
    migration purement DML y est annulée normalement par le rollback. Le
    journal de reprise ne s'active donc que lorsqu'il y a de la DDL, pour ne
    pas sacrifier une atomicité qui existe vraiment.
    """
    for statement in statements:
        mots = statement.split(None, 1)
        if mots and mots[0].upper() in _DDL_KEYWORDS:
            return True
    return False


def _statement_checksum(statement: str) -> str:
    """Empreinte d'une instruction, blancs normalisés.

    Le découpeur canonique a déjà ôté les commentaires : reformater ou
    recommenter une instruction déjà appliquée ne doit pas faire refuser la
    reprise, seul son SQL effectif compte.
    """
    return hashlib.sha256(" ".join(statement.split()).encode("utf-8")).hexdigest()


def _steps_table_ddl(dialect: Any) -> str:
    """DDL du journal de reprise, composée des primitives du dialecte actif.

    Seul un backend non transactionnel en a besoin ; parmi les officiels c'est
    MariaDB, mais un backend tiers dans le même cas la recevra dans ses types.
    """
    body = ",\n".join([
        f"    version {dialect.string_type(64)} NOT NULL",
        f"    position {dialect.simple_type('integer')} NOT NULL",
        f"    statement_checksum {dialect.char_type(64)} NOT NULL",
        f"    applied_at {dialect.simple_type('datetime')} NOT NULL "
        f"{dialect.timestamp_default_clause(on_update=False)}",
        "    PRIMARY KEY (version, position)",
    ])
    opening = dialect.create_table_opening("forge_migration_steps")
    return f"{opening} (\n{body}\n){dialect.collated_table_suffix()}"


def _steps_table_ddl_active() -> str:
    """DDL du journal de reprise pour le dialecte du backend actif."""
    from core.database.backend import get_backend

    return _steps_table_ddl(get_backend().dialect)


def load_migration_steps(db: Any = None) -> "dict[str, list[tuple[int, str]]]":
    """Journal de reprise : par version interrompue, ses (position, empreinte).

    Tolérant : table absente (backend transactionnel, ou aucun échec encore)
    vaut journal vide. Les positions sont rendues triées.
    """
    connection = db or _connect_db()
    should_close = db is None
    steps: "dict[str, list[tuple[int, str]]]" = {}
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(SELECT_MIGRATION_STEPS_SQL)
            for version, position, checksum in cursor.fetchall():
                steps.setdefault(str(version), []).append((int(position), str(checksum)))
        finally:
            cursor.close()
    except Exception:  # noqa: BLE001 — table absente = aucun pas journalisé
        _rollback_quietly(connection)
        return {}
    finally:
        if should_close:
            connection.close()
    for positions in steps.values():
        positions.sort()
    return steps


def _verify_recorded_prefix(
    migration: MigrationFile,
    statements: "list[str]",
    steps: "list[tuple[int, str]]",
) -> int:
    """Vérifie que le préfixe journalisé correspond au fichier ; rend sa taille.

    Les instructions déjà en base ne peuvent pas être réécrites depuis le
    fichier : la base les a exécutées telles quelles, et les rejouer autrement
    fabriquerait un état que personne n'a écrit. L'opérateur ne corrige que
    l'instruction fautive et les suivantes.
    """
    for rank, (position, checksum) in enumerate(steps, start=1):
        if position != rank or position > len(statements):
            raise MigrationError(
                f"{migration.filename}: reprise refusée, journal de reprise "
                f"incohérent (position {position} pour {len(statements)} "
                "instruction(s) au fichier). Si l'incohérence est assumée, videz "
                "le journal après avoir défait les effets en base : "
                f"DELETE FROM forge_migration_steps WHERE version = '{migration.version}'."
            )
        if _statement_checksum(statements[position - 1]) != checksum:
            raise MigrationError(
                f"{migration.filename}: reprise refusée, l'instruction {position} "
                "a déjà pris effet en base mais ne correspond plus au fichier.\n"
                "  Ne modifiez que l'instruction fautive et les suivantes ; "
                "restaurez le texte d'origine des instructions déjà appliquées.\n"
                "  Si la réécriture est assumée, défaites ses effets en base puis "
                "videz le journal : DELETE FROM forge_migration_steps WHERE "
                f"version = '{migration.version}'."
            )
    return len(steps)


def _apply_one_migration(
    connection: Any,
    migration: MigrationFile,
    *,
    recorded_steps: "dict[str, list[tuple[int, str]]] | None" = None,
) -> None:
    sql = migration.path.read_text(encoding="utf-8")
    statements = split_sql_statements(sql)
    transactional = _ddl_is_transactional()

    # Reprise (MIGRATION-RESUME-JOURNAL-001). Sur un backend qui ne sait pas
    # annuler la DDL, une migration qui en contient est journalisée : chaque
    # instruction est retenue et validée sitôt exécutée, et le journal dit
    # alors EXACTEMENT ce qui a pris effet, y compris la DML de fin de fichier
    # que l'annulation aurait silencieusement défaite. Une migration
    # interrompue reprend à la première instruction non journalisée, après
    # vérification que le préfixe déjà en base correspond toujours au fichier.
    #
    # Une migration purement DML n'est PAS journalisée, même sur ce backend :
    # sans DDL, le rollback l'annule entièrement, et l'atomicité qui existe
    # vraiment ne se sacrifie pas. Sur un backend transactionnel, l'annulation
    # défait tout : aucun journal, la migration reste atomique.
    skip = 0
    journaled = False
    if not transactional:
        steps = (recorded_steps if recorded_steps is not None
                 else load_migration_steps(connection)).get(migration.version, [])
        journaled = bool(steps) or _contains_ddl(statements)
        if steps:
            skip = _verify_recorded_prefix(migration, statements, steps)
            print(
                f"[REPRISE] {migration.filename} : instructions 1 à {skip} déjà "
                f"en base (journal de reprise), reprise à l'instruction {skip + 1}."
            )

    start = time.perf_counter()
    cursor = connection.cursor()
    executed = skip
    try:
        try:
            if not journaled:
                for statement in statements:
                    cursor.execute(statement)
                    executed += 1
            else:
                cursor.execute(_steps_table_ddl_active())
                for position in range(skip, len(statements)):
                    cursor.execute(statements[position])
                    cursor.execute(
                        INSERT_MIGRATION_STEP_SQL,
                        (
                            migration.version,
                            position + 1,
                            _statement_checksum(statements[position]),
                        ),
                    )
                    # Valider pas à pas : la DDL suivante validerait de toute
                    # façon implicitement, mais entre les deux le journal doit
                    # être aussi durable que l'instruction qu'il enregistre.
                    connection.commit()
                    executed = position + 1
            execution_ms = int((time.perf_counter() - start) * 1000)
            if journaled:
                cursor.execute(DELETE_MIGRATION_STEPS_SQL, (migration.version,))
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
                _failed_migration_report(migration, statements, executed, exc)
            ) from exc
    finally:
        cursor.close()


def _failed_migration_report(
    migration: MigrationFile,
    statements: "list[str]",
    executed: int,
    error: Exception,
) -> str:
    """Rapport d'échec d'une migration, situé dans le fichier et dans le temps.

    Le message ne disait que le nom du fichier et l'erreur du pilote. Sur une
    migration de quarante instructions, cela ne permet ni de savoir laquelle a
    échoué, ni ce qui a déjà pris effet.

    Deux faits manquaient, et le second est le plus lourd. Quand le backend ne
    sait pas annuler la DDL (MariaDB, voir `Dialect.supports_transactional_ddl`),
    les instructions déjà passées **restent en base** alors que le journal
    n'enregistre pas la migration. Relancer `migration:apply` les rejoue et
    échoue sur « already exists ». Taire ce décalage laissait l'opérateur
    devant un projet bloqué sans lui dire pourquoi.
    """
    numero = executed + 1
    fautive = statements[executed] if executed < len(statements) else ""
    if not fautive:
        situation = (
            f"l'enregistrement au journal, après les {len(statements)} instructions"
        )
    else:
        extrait = " ".join(fautive.split())
        if len(extrait) > 120:
            extrait = extrait[:117] + "..."
        situation = f"l'instruction {numero} sur {len(statements)} : {extrait}"

    lignes = [
        f"{migration.filename}: erreur SQL sur {situation}",
        f"  {error}",
    ]

    # L'avertissement de persistance ne vaut que si le journal pas à pas était
    # actif : une migration purement DML est annulée entièrement, même sur un
    # backend qui ne sait pas annuler la DDL.
    if executed and not _ddl_is_transactional() and _contains_ddl(statements):
        lignes += [
            "",
            f"  Les {executed} instructions précédentes ont pris effet et "
            "PERSISTENT : ce backend valide implicitement chaque instruction de "
            "définition, l'annulation ne les a pas défaites.",
            "  Elles sont retenues au journal de reprise "
            "(forge_migration_steps) et ne seront PAS rejouées.",
        ]
        if fautive:
            lignes += [
                f"  Corrigez l'instruction {numero} puis relancez "
                "`forge migration:apply` : la reprise continuera à "
                f"l'instruction {numero}.",
            ]
        else:
            lignes += [
                "  Relancez `forge migration:apply` : rien ne sera rejoué, "
                "seul l'enregistrement au journal des migrations sera retenté.",
            ]

    return "\n".join(lignes)


def _ddl_is_transactional() -> bool:
    """Le backend actif sait-il annuler la DDL ? Dans le doute, on suppose oui.

    Supposer oui est le choix prudent **pour le message** : on n'annonce pas
    des effets persistants sans en être sûr. Un backend tiers qui n'implémente
    pas la capacité reste donc silencieux plutôt que menaçant à tort.
    """
    from core.database.backend import get_backend

    try:
        return bool(get_backend().dialect.supports_transactional_ddl())
    except Exception:
        return True


def _migration_file_template(version: str, name: str) -> str:
    return (
        "-- Migration Forge\n"
        f"-- Version: {version}\n"
        f"-- Name: {name}\n"
        "-- Write your SQL below.\n"
        "\n"
        "-- Example:\n"
        "-- CREATE TABLE example (\n"
        f"--     {_example_identity_column()}\n"
        "-- );\n"
    )


def _relations_sql_block(project_root: Path, *, from_entity: str | None = None) -> str:
    """SQL des relations (ADR-068 : ADD COLUMN + FOREIGN KEY + INDEX) à insérer
    après les CREATE TABLE d'une migration (FORGE-15).

    Régénéré depuis `mvc/entities/relations.json` (source de vérité), filtré sur les
    relations dont l'entité source est `from_entity` quand il est fourni (migration
    d'une seule entité), sinon toutes (migration de toutes les entités). Retourne une
    chaîne vide s'il n'y a pas de relations.
    """
    from forge_mvc_entities.relations import (
        generate_relations_sql,
        validate_relations_definition,
    )

    entities_root = project_root / "mvc" / "entities"
    relations_path = entities_root / "relations.json"
    if not relations_path.exists():
        return ""
    raw = json.loads(relations_path.read_text(encoding="utf-8"))
    validated = validate_relations_definition(
        raw, source=str(relations_path), entities_root=entities_root
    )
    if from_entity is not None:
        validated = [r for r in validated if r.from_entity == from_entity]
    sql = generate_relations_sql(validated).strip()
    if not sql:
        return ""
    return "\n".join([
        "",
        "-- ============================================================",
        "-- Relations : colonnes FK, contraintes, index (mvc/entities/relations.sql)",
        "-- ============================================================",
        "",
        sql,
        "",
    ])


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

    from core.database.backend import get_backend

    fields_by_column = {field["column"]: field for field in definition["fields"]}
    table = _validate_sql_identifier(str(definition["table"]))
    columns = [
        (
            _validate_sql_identifier(column),
            _sql_column_definition(fields_by_column[column]),
        )
        for column in missing_columns
    ]
    return get_backend().dialect.add_columns_sql(table, columns)


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
    rest = args[2:]
    if not rest:
        return True
    with_relations = rest[-1] == "--with-relations"
    core = rest[:-1] if with_relations else rest
    if core == ["--from-entities"]:
        return True
    if len(core) == 2 and core[0] == "--from-entity":
        return True
    if len(core) == 2 and core[0] == "--from-diff":
        # --with-relations n'a pas de sens sur un diff (déjà un delta ciblé).
        return not with_relations
    return False


def _is_valid_diff_args(args: list[str]) -> bool:
    return len(args) == 3 and args[1] == "--entity"


def _normalize_sql_type(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().upper())


def _type_arguments(sql_type: str) -> str:
    """Arguments entre parenthèses d'un type SQL, normalisés (« 10,2 »)."""
    match = re.search(r"\(([^)]*)\)", sql_type)
    return re.sub(r"\s+", "", match.group(1)).upper() if match else ""


def _same_type(expected: str, actual: str) -> bool:
    """Deux types désignent-ils la même chose pour le backend actif ?

    Comparer les chaînes ne marche pas hors MariaDB : l'introspection de
    PostgreSQL rend `character varying(255)` là où le générateur écrit
    `VARCHAR(255)`, et SQL Server `NVARCHAR(255)` en majuscules propres. La
    comparaison porte donc sur la **famille** du type, que le contrat
    `Dialect` expose déjà, puis sur ses arguments.

    Les arguments ne départagent que si les deux côtés en portent : un type
    sans parenthèses n'apprend rien sur la longueur de l'autre, et le signaler
    produirait une différence là où il n'y en a pas.
    """
    from core.database.backend import get_backend

    dialect = get_backend().dialect
    if dialect.sql_families(expected) != dialect.sql_families(actual):
        return False
    expected_args = _type_arguments(expected)
    actual_args = _type_arguments(actual)
    if expected_args and actual_args:
        return expected_args == actual_args
    return True


def _column_changes(expected: ExpectedColumn, actual: ActualColumn) -> list[str]:
    changes: list[str] = []
    expected_type = _normalize_sql_type(expected.sql_type)
    actual_type = _normalize_sql_type(actual.sql_type)
    if not _same_type(expected.sql_type, actual.sql_type):
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


def _validate_sql_identifier(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", identifier):
        raise MigrationError(f"Identifiant SQL invalide : {identifier}")
    return identifier


def _example_identity_column() -> str:
    """Ligne d'exemple d'une cle primaire auto-incrementee, pour le backend actif.

    Le gabarit montrait une colonne au mot-clé d'auto-incrément MariaDB :
    sur un projet PostgreSQL, l'exemple enseignait du SQL invalide
    (OPTIN-DDL-ENTITIES-001).
    """
    from core.database.backend import get_backend

    dialect = get_backend().dialect
    return dialect.auto_increment_column_ddl("id", dialect.identity_type())


def _sql_column_definition(field: dict[str, Any]) -> str:
    parts = [str(field["sql_type"])]
    parts.append("NULL" if field["nullable"] else "NOT NULL")
    if field["auto_increment"]:
        # Le mot-cle depend du dialecte : MariaDB le separe du type, PostgreSQL
        # et SQL Server le portent DANS le type et n'en veulent aucun
        # (OPTIN-DDL-ENTITIES-001).
        from core.database.backend import get_backend

        clause = get_backend().dialect.auto_increment_clause()
        if clause:
            parts.append(clause)
    default_literal = sql_default_literal(field)
    if default_literal is not None:
        parts.append(f"DEFAULT {default_literal}")
    return " ".join(parts)


def _connect_db():
    from core.database.backend import get_backend

    backend = get_backend()
    if not backend.requires_provisioning:
        # Backend sans serveur (SQLite, ADR-054) : pas de comptes admin, mais
        # une migration est de la DDL, donc le rôle d'administration. On prend
        # la même porte que les backends serveur, seule autorisée à créer la
        # base ; celle d'exécution le refuse depuis
        # SQLITE-RUNTIME-NO-CREATE-001.
        from forge_mvc_entities.serverless_db import configure_serverless_db

        configure_serverless_db()
        return backend.get_admin_connection()

    cfg = load_migration_db_config()
    try:
        return backend.get_admin_connection(database=cfg.database)
    except Exception as exc:
        raise MigrationError(
            "Connexion d'administration impossible. "
            "Vérifiez DB_ADMIN_* / DB_NAME dans env/dev.\n"
            f"  Cause : {exc}"
        ) from exc


def load_migration_db_config() -> MigrationDbConfig:
    # load_project_config() charge l'environnement (load_dotenv) : indispensable
    # pour que le backend lise ensuite DB_ADMIN_* et DB_NAME dans os.environ (ADR-060).
    load_project_config()

    # ADR-033 : les migrations sont des changements de structure ; elles
    # empruntent le compte d'administration, lu par le backend depuis DB_ADMIN_*.
    # Seul le nom de la base cible reste fourni ici (DB_NAME, lu dans l'env).
    return MigrationDbConfig(database=os.environ.get("DB_NAME", ""))


def _rollback_quietly(connection: Any) -> None:
    try:
        connection.rollback()
    except Exception:
        pass
