import hashlib
import json
from datetime import datetime
from pathlib import Path

import pytest

from cli.entities import migrations
from cli.entities.migrations import (
    ActualColumn,
    AppliedMigration,
    ExpectedColumn,
    MigrationError,
    MigrationFile,
    MigrationNoChange,
    MigrationStatusReport,
    apply_pending_migrations,
    build_schema_diff_report,
    build_migration_status,
    collect_migration_files,
    diff_entity_schema,
    entity_diff_migration_sql,
    entity_sql_file_path,
    entity_sql_file_paths,
    get_migration_status,
    make_migration_file,
    migration_checksum,
    parse_migration_filename,
    slugify_migration_name,
)


class FakeCursor:
    def __init__(self, rows=None, fail=False, fail_on: str | None = None):
        self.rows = rows or []
        self.fail = fail
        self.fail_on = fail_on
        self.executed: list[tuple[str, tuple | None]] = []

    def execute(self, statement, params=None):
        self.executed.append((statement, params))
        if self.fail or (self.fail_on and self.fail_on in statement):
            raise RuntimeError("table missing")

    def fetchall(self):
        return list(self.rows)

    def close(self):
        pass


class FakeConnection:
    def __init__(self, rows=None, fail=False, fail_on: str | None = None):
        self.cursor_obj = FakeCursor(rows=rows, fail=fail, fail_on=fail_on)
        self.closed = False
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def _write_migration(root: Path, filename: str, content: str = "SELECT 1;") -> Path:
    migrations_dir = root / "mvc" / "migrations"
    migrations_dir.mkdir(parents=True, exist_ok=True)
    path = migrations_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def _write_entity_sql(root: Path, entity: str, sql: str) -> Path:
    entity_dir = root / "mvc" / "entities" / entity
    entity_dir.mkdir(parents=True, exist_ok=True)
    path = entity_dir / f"{entity}.sql"
    path.write_text(sql, encoding="utf-8")
    return path


def _write_entity_json(root: Path, entity: str, data: str) -> Path:
    entity_dir = root / "mvc" / "entities" / entity
    entity_dir.mkdir(parents=True, exist_ok=True)
    path = entity_dir / f"{entity}.json"
    path.write_text(data, encoding="utf-8")
    return path


def _local(version: str, filename: str, checksum: str) -> MigrationFile:
    return MigrationFile(
        version=version,
        name=filename.removeprefix(f"{version}_").removesuffix(".sql"),
        filename=filename,
        checksum=checksum,
        path=Path(filename),
    )


def _applied(version: str, filename: str, checksum: str) -> AppliedMigration:
    return AppliedMigration(
        version=version,
        name=filename.removeprefix(f"{version}_").removesuffix(".sql"),
        filename=filename,
        checksum=checksum,
    )


def test_parse_migration_filename_valid():
    version, name = parse_migration_filename("20260502193000_create_contacts.sql")

    assert version == "20260502193000"
    assert name == "create_contacts"


def test_slugify_migration_name_is_simple_and_parser_compatible():
    slug = slugify_migration_name("Create Contacts List")

    assert slug == "create_contacts_list"
    assert parse_migration_filename(f"20260502214530_{slug}.sql") == (
        "20260502214530",
        "create_contacts_list",
    )


def test_slugify_migration_name_accepts_dashes_and_underscores():
    assert slugify_migration_name("Add-email_to Contacts") == "add_email_to_contacts"


def test_slugify_migration_name_rejects_empty_name():
    with pytest.raises(MigrationError, match="vide"):
        slugify_migration_name("  ")


def test_slugify_migration_name_rejects_invalid_characters():
    with pytest.raises(MigrationError, match="invalide"):
        slugify_migration_name("create/contacts")


@pytest.mark.parametrize(
    "filename",
    [
        "create_contacts.sql",
        "202605021930_create_contacts.sql",
        "20260502193000.sql",
        "20260502193000-create-contacts.sql",
        "20260502193000_create_contacts.txt",
    ],
)
def test_parse_migration_filename_rejects_invalid_names(filename):
    with pytest.raises(MigrationError, match="Format attendu"):
        parse_migration_filename(filename)


def test_migration_checksum_uses_sha256(tmp_path):
    path = tmp_path / "20260502193000_create_contacts.sql"
    path.write_text("SELECT 1;\n", encoding="utf-8")

    assert migration_checksum(path) == hashlib.sha256(b"SELECT 1;\n").hexdigest()


def test_collect_migration_files_reads_local_sql(tmp_path):
    path = _write_migration(tmp_path, "20260502193000_create_contacts.sql", "CREATE TABLE contact;")

    files, missing = collect_migration_files(tmp_path / "mvc" / "migrations")

    assert missing is False
    assert files == [
        MigrationFile(
            version="20260502193000",
            name="create_contacts",
            filename="20260502193000_create_contacts.sql",
            checksum=migration_checksum(path),
            path=path,
        )
    ]


def test_collect_migration_files_reports_missing_directory(tmp_path):
    files, missing = collect_migration_files(tmp_path / "mvc" / "migrations")

    assert files == []
    assert missing is True


def test_build_status_pending():
    statuses = build_migration_status(
        [_local("20260502193000", "20260502193000_create_contacts.sql", "abc")],
        [],
    )

    assert statuses[0].status == "PENDING"


def test_build_status_applied():
    local = _local("20260502193000", "20260502193000_create_contacts.sql", "abc")
    applied = _applied("20260502193000", "20260502193000_create_contacts.sql", "abc")

    statuses = build_migration_status([local], [applied])

    assert statuses[0].status == "APPLIED"


def test_build_status_changed():
    local = _local("20260502193000", "20260502193000_create_contacts.sql", "abc")
    applied = _applied("20260502193000", "20260502193000_create_contacts.sql", "def")

    statuses = build_migration_status([local], [applied])

    assert statuses[0].status == "CHANGED"


def test_build_status_missing():
    applied = _applied("20260502193000", "20260502193000_create_contacts.sql", "abc")

    statuses = build_migration_status([], [applied])

    assert statuses[0].status == "MISSING"


def test_get_migration_status_combines_local_and_applied(tmp_path):
    path = _write_migration(tmp_path, "20260502193000_create_contacts.sql", "SELECT 1;")
    db = FakeConnection(
        rows=[
            (
                "20260502193000",
                "create_contacts",
                "20260502193000_create_contacts.sql",
                migration_checksum(path),
            )
        ]
    )

    report = get_migration_status(tmp_path / "mvc" / "migrations", db=db)

    assert report.statuses[0].status == "APPLIED"
    assert db.cursor_obj.executed == [(migrations.SELECT_APPLIED_MIGRATIONS_SQL, None)]


def test_get_migration_status_reports_missing_forge_migrations_table(tmp_path):
    _write_migration(tmp_path, "20260502193000_create_contacts.sql", "SELECT 1;")
    db = FakeConnection(fail=True)

    with pytest.raises(MigrationError, match="forge db:init"):
        get_migration_status(tmp_path / "mvc" / "migrations", db=db)


def test_cli_prints_readable_status(monkeypatch, capsys):
    monkeypatch.setattr(
        migrations,
        "get_migration_status",
        lambda: MigrationStatusReport(
            statuses=[
                migrations.MigrationStatus(
                    "PENDING",
                    "20260502193000",
                    "20260502193000_create_contacts.sql",
                )
            ]
        ),
    )

    migrations.main(["migration:status"])

    output = capsys.readouterr().out
    assert "[OK] Statut des migrations." in output
    assert "STATUT" in output
    assert "PENDING" in output
    assert "20260502193000_create_contacts.sql" in output


def test_cli_prints_no_migration_message_for_empty_report(monkeypatch, capsys):
    monkeypatch.setattr(
        migrations,
        "get_migration_status",
        lambda: MigrationStatusReport(statuses=[], migrations_dir_missing=True),
    )

    migrations.main(["migration:status"])

    output = capsys.readouterr().out
    assert "Dossier mvc/migrations absent" in output
    assert "Aucune migration trouvée." in output


def test_apply_with_no_migration_returns_empty_list(tmp_path):
    db = FakeConnection(rows=[])

    applied = apply_pending_migrations(tmp_path / "mvc" / "migrations", db=db)

    assert applied == []
    assert db.commits == 0


def test_apply_one_pending_migration_executes_sql_and_records_row(tmp_path):
    path = _write_migration(tmp_path, "20260502193000_create_contacts.sql", "CREATE TABLE contact;")
    db = FakeConnection(rows=[])

    applied = apply_pending_migrations(tmp_path / "mvc" / "migrations", db=db)

    assert [item.filename for item in applied] == ["20260502193000_create_contacts.sql"]
    assert ("CREATE TABLE contact", None) in db.cursor_obj.executed
    insert_params = next(
        params
        for statement, params in db.cursor_obj.executed
        if statement == migrations.INSERT_APPLIED_MIGRATION_SQL
    )
    assert insert_params[:4] == (
        "20260502193000",
        "create_contacts",
        "20260502193000_create_contacts.sql",
        migration_checksum(path),
    )
    assert isinstance(insert_params[4], int)
    assert db.commits == 1


def test_apply_multiple_pending_migrations_in_version_order(tmp_path):
    _write_migration(tmp_path, "20260502194500_add_email.sql", "ALTER TABLE contact ADD Email VARCHAR(120);")
    _write_migration(tmp_path, "20260502193000_create_contacts.sql", "CREATE TABLE contact;")
    db = FakeConnection(rows=[])

    applied = apply_pending_migrations(tmp_path / "mvc" / "migrations", db=db)

    assert [item.filename for item in applied] == [
        "20260502193000_create_contacts.sql",
        "20260502194500_add_email.sql",
    ]
    executed_sql = [statement for statement, _params in db.cursor_obj.executed]
    assert executed_sql.index("CREATE TABLE contact") < executed_sql.index(
        "ALTER TABLE contact ADD Email VARCHAR(120)"
    )
    assert db.commits == 2


def test_apply_refuses_changed_migration(tmp_path):
    _write_migration(tmp_path, "20260502193000_create_contacts.sql", "SELECT 1;")
    db = FakeConnection(
        rows=[
            (
                "20260502193000",
                "create_contacts",
                "20260502193000_create_contacts.sql",
                "different",
            )
        ]
    )

    with pytest.raises(MigrationError, match="modifiée"):
        apply_pending_migrations(tmp_path / "mvc" / "migrations", db=db)

    assert not any(statement == "SELECT 1" for statement, _params in db.cursor_obj.executed)


def test_apply_refuses_missing_migration(tmp_path):
    migrations_dir = tmp_path / "mvc" / "migrations"
    migrations_dir.mkdir(parents=True)
    db = FakeConnection(
        rows=[
            (
                "20260502193000",
                "create_contacts",
                "20260502193000_create_contacts.sql",
                "abc",
            )
        ]
    )

    with pytest.raises(MigrationError, match="absente"):
        apply_pending_migrations(migrations_dir, db=db)


def test_apply_stops_on_sql_error_and_does_not_record_failed_migration(tmp_path):
    _write_migration(tmp_path, "20260502193000_create_contacts.sql", "CREATE TABLE contact;")
    db = FakeConnection(rows=[], fail_on="CREATE TABLE contact")

    with pytest.raises(MigrationError, match="erreur SQL"):
        apply_pending_migrations(tmp_path / "mvc" / "migrations", db=db)

    assert not any(
        statement == migrations.INSERT_APPLIED_MIGRATION_SQL
        for statement, _params in db.cursor_obj.executed
    )
    assert db.commits == 0
    assert db.rollbacks == 1


def test_apply_reports_missing_forge_migrations_table(tmp_path):
    _write_migration(tmp_path, "20260502193000_create_contacts.sql", "SELECT 1;")
    db = FakeConnection(fail=True)

    with pytest.raises(MigrationError, match="forge db:init"):
        apply_pending_migrations(tmp_path / "mvc" / "migrations", db=db)


def test_make_migration_file_creates_missing_directory(tmp_path):
    migrations_dir = tmp_path / "mvc" / "migrations"

    path = make_migration_file(
        "create_contacts",
        migrations_dir,
        now=datetime(2026, 5, 2, 21, 45, 30),
    )

    assert migrations_dir.exists()
    assert path == migrations_dir / "20260502214530_create_contacts.sql"


def test_make_migration_file_creates_parser_compatible_file(tmp_path):
    path = make_migration_file(
        "create contacts",
        tmp_path / "mvc" / "migrations",
        now=datetime(2026, 5, 2, 21, 45, 30),
    )

    assert parse_migration_filename(path.name) == ("20260502214530", "create_contacts")
    content = path.read_text(encoding="utf-8")
    assert "-- Migration Forge" in content
    assert "-- Version: 20260502214530" in content
    assert "-- Name: create_contacts" in content
    assert "-- Write your SQL below." in content


def test_make_migration_file_refuses_empty_name(tmp_path):
    with pytest.raises(MigrationError, match="vide"):
        make_migration_file(" ", tmp_path / "mvc" / "migrations")


def test_make_migration_file_refuses_invalid_name(tmp_path):
    with pytest.raises(MigrationError, match="invalide"):
        make_migration_file("create/contacts", tmp_path / "mvc" / "migrations")


def test_make_migration_file_never_overwrites_existing_file(tmp_path):
    migrations_dir = tmp_path / "mvc" / "migrations"
    existing = migrations_dir / "20260502214530_create_contacts.sql"
    migrations_dir.mkdir(parents=True)
    existing.write_text("-- existing\n", encoding="utf-8")

    with pytest.raises(MigrationError, match="déjà existante"):
        make_migration_file(
            "create_contacts",
            migrations_dir,
            now=datetime(2026, 5, 2, 21, 45, 30),
        )

    assert existing.read_text(encoding="utf-8") == "-- existing\n"


def test_entity_sql_file_path_converts_pascal_case_to_entity_folder(tmp_path):
    sql_path = _write_entity_sql(tmp_path, "contact", "CREATE TABLE contact;")

    assert entity_sql_file_path("Contact", project_root=tmp_path) == sql_path


def test_make_migration_file_from_entity_copies_entity_sql(tmp_path):
    entity_sql = "CREATE TABLE IF NOT EXISTS contact (\n    id INT NOT NULL\n);\n"
    _write_entity_sql(tmp_path, "contact", entity_sql)

    path = make_migration_file(
        "create_contacts",
        tmp_path / "mvc" / "migrations",
        now=datetime(2026, 5, 2, 22, 15, 30),
        from_entity="Contact",
        project_root=tmp_path,
    )

    content = path.read_text(encoding="utf-8")
    assert "-- Source: entity Contact" in content
    assert "-- Generated from: " in content
    assert "mvc/entities/contact/contact.sql" in content
    assert "-- Review this SQL before running:" in content
    assert entity_sql in content


def test_make_migration_file_from_entity_reports_missing_sql(tmp_path):
    with pytest.raises(MigrationError, match="SQL d'entité introuvable"):
        make_migration_file(
            "create_contacts",
            tmp_path / "mvc" / "migrations",
            now=datetime(2026, 5, 2, 22, 15, 30),
            from_entity="Contact",
            project_root=tmp_path,
        )


def test_make_migration_file_from_entity_reuses_invalid_migration_name_validation(tmp_path):
    _write_entity_sql(tmp_path, "contact", "CREATE TABLE contact;")

    with pytest.raises(MigrationError, match="invalide"):
        make_migration_file(
            "create/contacts",
            tmp_path / "mvc" / "migrations",
            now=datetime(2026, 5, 2, 22, 15, 30),
            from_entity="Contact",
            project_root=tmp_path,
        )


def test_make_migration_file_from_entity_never_overwrites_existing_file(tmp_path):
    _write_entity_sql(tmp_path, "contact", "CREATE TABLE contact;")
    migrations_dir = tmp_path / "mvc" / "migrations"
    migrations_dir.mkdir(parents=True)
    existing = migrations_dir / "20260502221530_create_contacts.sql"
    existing.write_text("-- existing\n", encoding="utf-8")

    with pytest.raises(MigrationError, match="déjà existante"):
        make_migration_file(
            "create_contacts",
            migrations_dir,
            now=datetime(2026, 5, 2, 22, 15, 30),
            from_entity="Contact",
            project_root=tmp_path,
        )

    assert existing.read_text(encoding="utf-8") == "-- existing\n"


def test_entity_sql_file_paths_returns_sorted_entity_sql_files(tmp_path):
    ville = _write_entity_sql(tmp_path, "ville", "CREATE TABLE ville;")
    contact = _write_entity_sql(tmp_path, "contact", "CREATE TABLE contact;")

    assert entity_sql_file_paths(project_root=tmp_path) == [contact, ville]


def test_entity_sql_file_paths_reports_no_entity_sql(tmp_path):
    with pytest.raises(MigrationError, match="Aucun SQL d'entité"):
        entity_sql_file_paths(project_root=tmp_path)


def test_make_migration_file_from_entities_concatenates_all_entity_sql(tmp_path):
    _write_entity_sql(tmp_path, "ville", "CREATE TABLE ville;\n")
    _write_entity_sql(tmp_path, "contact", "CREATE TABLE contact;\n")

    path = make_migration_file(
        "initial_schema",
        tmp_path / "mvc" / "migrations",
        now=datetime(2026, 5, 2, 23, 0, 0),
        from_entities=True,
        project_root=tmp_path,
    )

    content = path.read_text(encoding="utf-8")
    assert "-- Source: all entities" in content
    assert "-- Generated from: mvc/entities/*/*.sql" in content
    assert "-- Entity SQL: mvc/entities/contact/contact.sql" in content
    assert "-- Entity SQL: mvc/entities/ville/ville.sql" in content
    assert content.index("CREATE TABLE contact;") < content.index("CREATE TABLE ville;")


def test_make_migration_file_from_entities_adds_readable_separators(tmp_path):
    _write_entity_sql(tmp_path, "contact", "CREATE TABLE contact;")

    path = make_migration_file(
        "initial_schema",
        tmp_path / "mvc" / "migrations",
        now=datetime(2026, 5, 2, 23, 0, 0),
        from_entities=True,
        project_root=tmp_path,
    )

    content = path.read_text(encoding="utf-8")
    assert "-- ============================================================" in content
    assert "-- Entity SQL: mvc/entities/contact/contact.sql" in content


def test_make_migration_file_from_entities_reports_no_entity_sql(tmp_path):
    with pytest.raises(MigrationError, match="Aucun SQL d'entité"):
        make_migration_file(
            "initial_schema",
            tmp_path / "mvc" / "migrations",
            now=datetime(2026, 5, 2, 23, 0, 0),
            from_entities=True,
            project_root=tmp_path,
        )


def test_make_migration_file_from_entities_never_overwrites_existing_file(tmp_path):
    _write_entity_sql(tmp_path, "contact", "CREATE TABLE contact;")
    migrations_dir = tmp_path / "mvc" / "migrations"
    migrations_dir.mkdir(parents=True)
    existing = migrations_dir / "20260502230000_initial_schema.sql"
    existing.write_text("-- existing\n", encoding="utf-8")

    with pytest.raises(MigrationError, match="déjà existante"):
        make_migration_file(
            "initial_schema",
            migrations_dir,
            now=datetime(2026, 5, 2, 23, 0, 0),
            from_entities=True,
            project_root=tmp_path,
        )

    assert existing.read_text(encoding="utf-8") == "-- existing\n"


def test_cli_apply_prints_executed_files(monkeypatch, capsys):
    monkeypatch.setattr(
        migrations,
        "apply_pending_migrations",
        lambda *a, **k: [
            MigrationFile(
                version="20260502193000",
                name="create_contacts",
                filename="20260502193000_create_contacts.sql",
                checksum="abc",
                path=Path("20260502193000_create_contacts.sql"),
            )
        ],
    )

    migrations.main(["migration:apply"])

    output = capsys.readouterr().out
    assert "[OK] Application des migrations." in output
    assert "[EXECUTE] 20260502193000_create_contacts.sql" in output
    assert "[OK] 1 migration(s) appliquée(s)." in output


def test_cli_apply_prints_no_migration_message(monkeypatch, capsys):
    monkeypatch.setattr(migrations, "apply_pending_migrations", lambda *a, **k: [])

    migrations.main(["migration:apply"])

    output = capsys.readouterr().out
    assert "Aucune migration à appliquer." in output


def test_cli_make_prints_created_file(monkeypatch, capsys, tmp_path):
    created = tmp_path / "mvc" / "migrations" / "20260502214530_create_contacts.sql"
    monkeypatch.setattr(migrations, "make_migration_file", lambda name, **kwargs: created)

    migrations.main(["migration:make", "create_contacts"])

    output = capsys.readouterr().out
    assert "[OK] Migration créée : " in output
    assert "20260502214530_create_contacts.sql" in output


def test_cli_make_from_entity_passes_entity_to_creator(monkeypatch, capsys, tmp_path):
    captured = {}
    created = tmp_path / "mvc" / "migrations" / "20260502221530_create_contacts.sql"

    def fake_make_migration_file(name, *, from_entity=None, from_entities=False, from_diff=None, with_relations=False):
        captured["name"] = name
        captured["from_entity"] = from_entity
        captured["from_entities"] = from_entities
        captured["from_diff"] = from_diff
        return created

    monkeypatch.setattr(migrations, "make_migration_file", fake_make_migration_file)

    migrations.main(["migration:make", "create_contacts", "--from-entity", "Contact"])

    output = capsys.readouterr().out
    assert "[OK] Migration créée : " in output
    assert captured == {
        "name": "create_contacts",
        "from_entity": "Contact",
        "from_entities": False,
        "from_diff": None,
    }


def test_cli_make_from_entities_passes_flag_to_creator(monkeypatch, capsys, tmp_path):
    captured = {}
    created = tmp_path / "mvc" / "migrations" / "20260502230000_initial_schema.sql"

    def fake_make_migration_file(name, *, from_entity=None, from_entities=False, from_diff=None, with_relations=False):
        captured["name"] = name
        captured["from_entity"] = from_entity
        captured["from_entities"] = from_entities
        captured["from_diff"] = from_diff
        return created

    monkeypatch.setattr(migrations, "make_migration_file", fake_make_migration_file)

    migrations.main(["migration:make", "initial_schema", "--from-entities"])

    output = capsys.readouterr().out
    assert "[OK] Migration créée : " in output
    assert captured == {
        "name": "initial_schema",
        "from_entity": None,
        "from_entities": True,
        "from_diff": None,
    }


def test_cli_make_from_diff_passes_entity_to_creator(monkeypatch, capsys, tmp_path):
    captured = {}
    created = tmp_path / "mvc" / "migrations" / "20260503101500_add_contact_fields.sql"

    def fake_make_migration_file(name, *, from_entity=None, from_entities=False, from_diff=None, with_relations=False):
        captured["name"] = name
        captured["from_entity"] = from_entity
        captured["from_entities"] = from_entities
        captured["from_diff"] = from_diff
        return created

    monkeypatch.setattr(migrations, "make_migration_file", fake_make_migration_file)

    migrations.main(["migration:make", "add_contact_fields", "--from-diff", "Contact"])

    output = capsys.readouterr().out
    assert "[OK] Migration créée : " in output
    assert captured == {
        "name": "add_contact_fields",
        "from_entity": None,
        "from_entities": False,
        "from_diff": "Contact",
    }


# ── FORGE-15 : migration:make --with-relations ───────────────────────────────

def _setup_classe_with_relation(tmp_path: Path) -> None:
    _write_entity_json(tmp_path, "annee_scolaire", json.dumps({
        "schema_version": "1.0", "name": "AnneeScolaire", "table": "annee_scolaire",
        "fields": [{"name": "libelle", "type": "string", "max_length": 50, "required": True}],
    }))
    _write_entity_json(tmp_path, "classe", json.dumps({
        "schema_version": "1.0", "name": "Classe", "table": "classe",
        "fields": [{"name": "code", "type": "string", "max_length": 30, "required": True}],
    }))
    _write_entity_sql(tmp_path, "classe",
                      "CREATE TABLE classe (\n    Id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,\n"
                      "    Code VARCHAR(30) NOT NULL,\n    PRIMARY KEY (Id)\n);\n")
    (tmp_path / "mvc" / "entities" / "relations.json").write_text(json.dumps({
        "schema_version": "1.0", "relations": [{
            "type": "many_to_one", "from": "Classe", "to": "AnneeScolaire", "name": "annee_scolaire",
            "foreign_key": "annee_scolaire_id", "on_delete": "restrict", "nullable": False, "index": True,
        }],
    }), encoding="utf-8")


def test_migration_from_entity_with_relations_inclut_fk(tmp_path):
    _setup_classe_with_relation(tmp_path)
    path = make_migration_file(
        "create_classe", migrations_dir=tmp_path / "mvc" / "migrations",
        from_entity="Classe", with_relations=True, project_root=tmp_path,
    )
    content = path.read_text(encoding="utf-8")
    assert "CREATE TABLE classe" in content
    assert "ADD COLUMN annee_scolaire_id BIGINT UNSIGNED" in content
    assert "FOREIGN KEY (annee_scolaire_id)" in content
    # Ordre : la table avant la contrainte.
    assert content.index("CREATE TABLE classe") < content.index("ADD CONSTRAINT")


def test_migration_from_entity_sans_relations_omet_fk(tmp_path):
    _setup_classe_with_relation(tmp_path)
    path = make_migration_file(
        "create_classe", migrations_dir=tmp_path / "mvc" / "migrations",
        from_entity="Classe", project_root=tmp_path,
    )
    assert "ADD CONSTRAINT" not in path.read_text(encoding="utf-8")


def test_migration_with_relations_exige_une_source(tmp_path):
    with pytest.raises(MigrationError, match="with-relations"):
        make_migration_file(
            "x", migrations_dir=tmp_path / "mvc" / "migrations",
            with_relations=True, project_root=tmp_path,
        )


def test_schema_diff_reports_table_missing():
    report = build_schema_diff_report(
        "Contact",
        "contact",
        [ExpectedColumn("id", "INT", False, True)],
        [],
    )

    assert report.table_status == "TABLE_MISSING"
    assert report.rows == [migrations.SchemaDiffRow("TABLE_MISSING", "-", "table absente en base")]


def test_schema_diff_reports_missing_column():
    report = build_schema_diff_report(
        "Contact",
        "contact",
        [
            ExpectedColumn("id", "INT", False, True),
            ExpectedColumn("email", "VARCHAR(120)", False, False),
        ],
        [ActualColumn("id", "int", False, True)],
    )

    assert report.rows[1].status == "COLUMN_MISSING"
    assert report.rows[1].column == "email"


def test_schema_diff_reports_extra_column():
    report = build_schema_diff_report(
        "Contact",
        "contact",
        [ExpectedColumn("id", "INT", False, True)],
        [
            ActualColumn("id", "INT", False, True),
            ActualColumn("old_field", "VARCHAR(20)", True, False),
        ],
    )

    assert report.rows[-1].status == "COLUMN_EXTRA"
    assert report.rows[-1].column == "old_field"


def test_schema_diff_reports_type_change_case_insensitive():
    report = build_schema_diff_report(
        "Contact",
        "contact",
        [ExpectedColumn("telephone", "VARCHAR(20)", True, False)],
        [ActualColumn("telephone", "varchar(50)", True, False)],
    )

    assert report.rows[0].status == "COLUMN_CHANGED"
    assert "type attendu VARCHAR(20), trouvé VARCHAR(50)" in report.rows[0].detail


def test_schema_diff_reports_nullable_change():
    report = build_schema_diff_report(
        "Contact",
        "contact",
        [ExpectedColumn("email", "VARCHAR(120)", False, False)],
        [ActualColumn("email", "VARCHAR(120)", True, False)],
    )

    assert report.rows[0].status == "COLUMN_CHANGED"
    assert "nullable attendu NO, trouvé YES" in report.rows[0].detail


def test_schema_diff_reports_identical_columns():
    report = build_schema_diff_report(
        "Contact",
        "contact",
        [ExpectedColumn("id", "INT", False, True)],
        [ActualColumn("id", "int", False, True)],
    )

    assert report.table_status == "OK"
    assert report.rows[0].status == "OK"
    assert report.rows[0].detail == "identique"


def test_diff_entity_schema_reads_json_and_information_schema(tmp_path):
    _write_entity_json(
        tmp_path,
        "contact",
        """
{
  "entity": "Contact",
  "table": "contact",
  "fields": [
    {"name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true},
    {"name": "email", "sql_type": "VARCHAR(120)"}
  ]
}
""",
    )
    db = FakeConnection(
        rows=[
            ("Id", "int", "NO", "auto_increment"),
            ("Email", "varchar(120)", "NO", ""),
        ]
    )

    report = diff_entity_schema("Contact", project_root=tmp_path, db=db, database="forge_test")

    assert report.table_status == "OK"
    assert db.cursor_obj.executed == [
        (migrations.SELECT_TABLE_COLUMNS_SQL, ("forge_test", "contact"))
    ]


def test_diff_entity_schema_reports_missing_entity_json(tmp_path):
    with pytest.raises(MigrationError, match="JSON d'entité introuvable"):
        diff_entity_schema("Contact", project_root=tmp_path, db=FakeConnection(), database="forge_test")


def test_entity_diff_migration_sql_uses_full_entity_sql_when_table_missing(tmp_path):
    entity_sql = "CREATE TABLE IF NOT EXISTS contact (\n    Id INT NOT NULL\n);\n"
    _write_entity_sql(tmp_path, "contact", entity_sql)
    _write_entity_json(
        tmp_path,
        "contact",
        """
{
  "entity": "Contact",
  "table": "contact",
  "fields": [
    {"name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true}
  ]
}
""",
    )

    sql = entity_diff_migration_sql(
        "Contact",
        project_root=tmp_path,
        db=FakeConnection(rows=[]),
        database="forge_test",
    )

    assert sql == entity_sql


def test_make_migration_file_from_diff_reports_missing_entity_sql_for_missing_table(tmp_path):
    _write_entity_json(
        tmp_path,
        "contact",
        """
{
  "entity": "Contact",
  "table": "contact",
  "fields": [
    {"name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true}
  ]
}
""",
    )

    with pytest.raises(MigrationError, match="SQL d'entité introuvable"):
        make_migration_file(
            "create_contacts",
            tmp_path / "mvc" / "migrations",
            now=datetime(2026, 5, 3, 10, 15, 0),
            from_diff="Contact",
            project_root=tmp_path,
            db=FakeConnection(rows=[]),
            database="forge_test",
        )


def test_make_migration_file_from_diff_adds_missing_column(tmp_path):
    _write_entity_json(
        tmp_path,
        "contact",
        """
{
  "entity": "Contact",
  "table": "contact",
  "fields": [
    {"name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true},
    {"name": "email", "sql_type": "VARCHAR(120)", "nullable": true}
  ]
}
""",
    )
    db = FakeConnection(rows=[("Id", "INT", "NO", "auto_increment")])

    path = make_migration_file(
        "add_contact_fields",
        tmp_path / "mvc" / "migrations",
        now=datetime(2026, 5, 3, 10, 15, 0),
        from_diff="Contact",
        project_root=tmp_path,
        db=db,
        database="forge_test",
    )

    content = path.read_text(encoding="utf-8")
    assert "-- Source: diff entity Contact" in content
    assert "-- Generated from: mvc/entities/contact/contact.json" in content
    assert "ALTER TABLE `contact`" in content
    assert "ADD COLUMN `Email` VARCHAR(120) NULL;" in content


def test_make_migration_file_from_diff_adds_multiple_columns_in_json_order(tmp_path):
    _write_entity_json(
        tmp_path,
        "contact",
        """
{
  "entity": "Contact",
  "table": "contact",
  "fields": [
    {"name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true},
    {"name": "email", "sql_type": "VARCHAR(120)", "nullable": true},
    {"name": "telephone", "sql_type": "VARCHAR(20)", "nullable": true}
  ]
}
""",
    )
    db = FakeConnection(rows=[("Id", "INT", "NO", "auto_increment")])

    path = make_migration_file(
        "add_contact_fields",
        tmp_path / "mvc" / "migrations",
        now=datetime(2026, 5, 3, 10, 15, 0),
        from_diff="Contact",
        project_root=tmp_path,
        db=db,
        database="forge_test",
    )

    content = path.read_text(encoding="utf-8")
    assert content.index("ADD COLUMN `Email`") < content.index("ADD COLUMN `Telephone`")
    assert "ADD COLUMN `Email` VARCHAR(120) NULL,\n" in content
    assert "ADD COLUMN `Telephone` VARCHAR(20) NULL;" in content


def test_make_migration_file_from_diff_creates_no_file_without_changes(tmp_path):
    _write_entity_json(
        tmp_path,
        "contact",
        """
{
  "entity": "Contact",
  "table": "contact",
  "fields": [
    {"name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true},
    {"name": "email", "sql_type": "VARCHAR(120)"}
  ]
}
""",
    )
    db = FakeConnection(
        rows=[
            ("Id", "INT", "NO", "auto_increment"),
            ("Email", "VARCHAR(120)", "NO", ""),
        ]
    )

    with pytest.raises(MigrationNoChange, match="Aucun changement"):
        make_migration_file(
            "add_contact_fields",
            tmp_path / "mvc" / "migrations",
            now=datetime(2026, 5, 3, 10, 15, 0),
            from_diff="Contact",
            project_root=tmp_path,
            db=db,
            database="forge_test",
        )

    assert not (tmp_path / "mvc" / "migrations").exists()


def test_make_migration_file_from_diff_refuses_changed_column(tmp_path):
    _write_entity_json(
        tmp_path,
        "contact",
        """
{
  "entity": "Contact",
  "table": "contact",
  "fields": [
    {"name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true},
    {"name": "email", "sql_type": "VARCHAR(120)"}
  ]
}
""",
    )
    db = FakeConnection(
        rows=[
            ("Id", "INT", "NO", "auto_increment"),
            ("Email", "VARCHAR(50)", "NO", ""),
        ]
    )

    with pytest.raises(MigrationError, match="COLUMN_CHANGED"):
        make_migration_file(
            "add_contact_fields",
            tmp_path / "mvc" / "migrations",
            now=datetime(2026, 5, 3, 10, 15, 0),
            from_diff="Contact",
            project_root=tmp_path,
            db=db,
            database="forge_test",
        )

    assert not (tmp_path / "mvc" / "migrations").exists()


def test_make_migration_file_from_diff_refuses_extra_column(tmp_path):
    _write_entity_json(
        tmp_path,
        "contact",
        """
{
  "entity": "Contact",
  "table": "contact",
  "fields": [
    {"name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true}
  ]
}
""",
    )
    db = FakeConnection(
        rows=[
            ("Id", "INT", "NO", "auto_increment"),
            ("OldField", "VARCHAR(50)", "YES", ""),
        ]
    )

    with pytest.raises(MigrationError, match="COLUMN_EXTRA"):
        make_migration_file(
            "add_contact_fields",
            tmp_path / "mvc" / "migrations",
            now=datetime(2026, 5, 3, 10, 15, 0),
            from_diff="Contact",
            project_root=tmp_path,
            db=db,
            database="forge_test",
        )

    assert not (tmp_path / "mvc" / "migrations").exists()


def test_make_migration_file_from_diff_never_overwrites_existing_file(tmp_path):
    _write_entity_json(
        tmp_path,
        "contact",
        """
{
  "entity": "Contact",
  "table": "contact",
  "fields": [
    {"name": "id", "sql_type": "INT", "primary_key": true, "auto_increment": true},
    {"name": "email", "sql_type": "VARCHAR(120)", "nullable": true}
  ]
}
""",
    )
    migrations_dir = tmp_path / "mvc" / "migrations"
    migrations_dir.mkdir(parents=True)
    existing = migrations_dir / "20260503101500_add_contact_fields.sql"
    existing.write_text("-- existing\n", encoding="utf-8")

    with pytest.raises(MigrationError, match="déjà existante"):
        make_migration_file(
            "add_contact_fields",
            migrations_dir,
            now=datetime(2026, 5, 3, 10, 15, 0),
            from_diff="Contact",
            project_root=tmp_path,
            db=FakeConnection(rows=[("Id", "INT", "NO", "auto_increment")]),
            database="forge_test",
        )

    assert existing.read_text(encoding="utf-8") == "-- existing\n"


def test_cli_diff_prints_readable_report(monkeypatch, capsys):
    monkeypatch.setattr(
        migrations,
        "diff_entity_schema",
        lambda entity: migrations.SchemaDiffReport(
            entity=entity,
            table="contact",
            table_status="OK",
            rows=[migrations.SchemaDiffRow("OK", "id", "identique")],
        ),
    )

    migrations.main(["migration:diff", "--entity", "Contact"])

    output = capsys.readouterr().out
    assert "[OK] Diff de schéma pour l’entité Contact." in output
    assert "TABLE contact : OK" in output
    assert "STATUT" in output
    assert "identique" in output
