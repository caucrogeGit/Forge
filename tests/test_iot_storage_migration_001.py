"""Tests de la migration SQL des événements IoT — IOT-STORAGE-MIGRATION-001.

Vérifie que le fichier de migration ``20260528120000_create_iot_events.sql``
existe dans le package ``forge-mvc-iot``, suit le format Forge des
migrations versionnées (timestamp YYYYMMDDHHMMSS + nom + .sql), et
applique le DDL exactement aligné sur le contrat
``forge_mvc_iot.storage.events`` (ticket IOT-STORAGE-EVENTS-001).

Tests entièrement textuels — aucun MariaDB n'est requis. La migration
n'est ni appliquée, ni branchée à une commande à ce stade ; la mise en
place du repository et de l'application réelle est traitée par
``IOT-STORAGE-REPOSITORY-001``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_iot")

from forge_mvc_iot.storage.events import COLUMNS, TABLE_NAME

PROJECT_ROOT = Path(__file__).parent.parent
IOT_PKG_DIR = PROJECT_ROOT / "packages" / "forge-mvc-iot"
# Depuis IOT-PACKAGE-DATA-MIGRATIONS-001, les migrations vivent en tant
# que ressources du package Python pour voyager avec la distribution
# PyPI (cf. [tool.setuptools.package-data] dans pyproject.toml).
MIGRATIONS_DIR = IOT_PKG_DIR / "forge_mvc_iot" / "migrations"
STORAGE_MODULE_FILE = (
    IOT_PKG_DIR / "forge_mvc_iot" / "storage" / "events.py"
)

EXPECTED_FILENAME = "20260528120000_create_iot_events.sql"
MIGRATION_FILE = MIGRATIONS_DIR / EXPECTED_FILENAME


@pytest.fixture(scope="module")
def migration_text() -> str:
    """DDL rendu pour MariaDB, dialecte historique de ces garde-fous.

    Le paquet ne livre plus de .sql fige : il declare sa table et le DDL est
    rendu pour le backend installe (OPTIN-DDL-IOT-001).
    """
    pytest.importorskip("forge_mvc_mariadb")
    from core.database.table_ddl import render_create_table
    from forge_mvc_iot.tables import IOT_EVENTS
    from forge_mvc_mariadb.dialect import MariaDBDialect

    return chr(10).join(render_create_table(IOT_EVENTS, MariaDBDialect()))


# ── Fichier et nommage ──────────────────────────────────────────────────────


class TestMigrationFile:
    def test_migration_declaree_et_plus_de_fichier(self):
        """Le paquet declare sa table au lieu de livrer un .sql fige."""
        from forge_mvc_iot.tables import MIGRATIONS

        assert not MIGRATIONS_DIR.exists(), "plus de .sql fige (OPTIN-DDL-IOT-001)"
        assert MIGRATIONS[0][0] == EXPECTED_FILENAME

    def test_iot_events_est_declaree_une_fois(self):
        """Le test exigeait `len(MIGRATIONS) == 1`, ce qui figeait un compte.

        `IOT-DEVICE-AUTH-001` a ajouté `iot_api_tokens`. Ce qui compte est que
        chaque table soit décrite une fois et une seule : deux migrations pour
        la même table s'appliqueraient deux fois.
        """
        from forge_mvc_iot.tables import IOT_EVENTS, MIGRATIONS

        noms = [table.name for _, table in MIGRATIONS]

        assert noms.count(IOT_EVENTS.name) == 1
        assert len(noms) == len(set(noms))
        assert len({fichier for fichier, _ in MIGRATIONS}) == len(MIGRATIONS)


# ── DDL — squelette ────────────────────────────────────────────────────────


class TestDdlSkeleton:
    def test_creates_iot_events_table(self, migration_text):
        assert "iot_events" in migration_text
        assert TABLE_NAME == "iot_events"

    def test_uses_create_table_if_not_exists(self, migration_text):
        # Idempotence — rejouable sans erreur si la table existe déjà.
        assert re.search(
            r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+iot_events",
            migration_text,
            flags=re.IGNORECASE,
        ), "La migration doit utiliser CREATE TABLE IF NOT EXISTS"

    def test_uses_innodb_utf8mb4(self, migration_text):
        # Charset/engine cohérents avec le reste de Forge (utf8mb4).
        # Rendu par Dialect.table_suffix() : present sur MariaDB, absent
        # ailleurs (c'est tout l'objet du chantier OPTIN-DDL-DIALECTAL).
        assert "ENGINE=InnoDB" in migration_text
        assert "utf8mb4" in migration_text


# ── DDL — colonnes ──────────────────────────────────────────────────────────


class TestColumns:
    """Chaque colonne déclarée par le contrat doit figurer dans le DDL."""

    @pytest.mark.parametrize("column", COLUMNS)
    def test_column_present(self, migration_text, column):
        # On cherche le nom de colonne suivi d'un type (espace puis
        # majuscule), pas seulement le mot dans un commentaire.
        pattern = rf"\b{re.escape(column)}\s+[A-Z]"
        assert re.search(pattern, migration_text), (
            f"Colonne {column!r} absente ou non typée dans la migration"
        )

    def test_id_column_present(self, migration_text):
        # `id` est exclu de COLUMNS (généré par la base) mais doit
        # apparaître dans le DDL comme clé primaire auto-incrémentée.
        assert re.search(
            r"\bid\s+BIGINT\s+UNSIGNED\s+NOT\s+NULL\s+AUTO_INCREMENT",
            migration_text,
            flags=re.IGNORECASE,
        ), "La colonne id doit être BIGINT UNSIGNED NOT NULL AUTO_INCREMENT"

    def test_primary_key_on_id(self, migration_text):
        assert re.search(
            r"PRIMARY\s+KEY\s*\(\s*id\s*\)",
            migration_text,
            flags=re.IGNORECASE,
        ), "PRIMARY KEY (id) attendu"


class TestColumnTypes:
    """Les types SQL spécifiques au contrat doivent être respectés."""

    def test_site_varchar64_not_null(self, migration_text):
        assert re.search(
            r"\bsite\s+VARCHAR\(64\)\s+NOT\s+NULL",
            migration_text,
            flags=re.IGNORECASE,
        )

    def test_device_id_varchar64_not_null(self, migration_text):
        assert re.search(
            r"\bdevice_id\s+VARCHAR\(64\)\s+NOT\s+NULL",
            migration_text,
            flags=re.IGNORECASE,
        )

    def test_kind_varchar64_not_null(self, migration_text):
        assert re.search(
            r"\bkind\s+VARCHAR\(64\)\s+NOT\s+NULL",
            migration_text,
            flags=re.IGNORECASE,
        )

    def test_value_double_not_null(self, migration_text):
        assert re.search(
            r"\bvalue\s+DOUBLE\s+NOT\s+NULL",
            migration_text,
            flags=re.IGNORECASE,
        )

    def test_unit_varchar32_not_null(self, migration_text):
        assert re.search(
            r"\bunit\s+VARCHAR\(32\)\s+NOT\s+NULL",
            migration_text,
            flags=re.IGNORECASE,
        )

    def test_timestamp_varchar40_not_null(self, migration_text):
        # ISO 8601 UTC en VARCHAR — préserve la chaîne du payload.
        assert re.search(
            r"\btimestamp\s+VARCHAR\(40\)\s+NOT\s+NULL",
            migration_text,
            flags=re.IGNORECASE,
        )

    def test_metadata_json_text_nullable(self, migration_text):
        assert re.search(
            r"\bmetadata_json\s+TEXT\s+NULL\b",
            migration_text,
            flags=re.IGNORECASE,
        ), "metadata_json doit être TEXT NULL"

    def test_received_at_datetime_not_null(self, migration_text):
        # OPTIN-DDL-IOT-001 : le rendu emploie le type datetime du dialecte.
        # Sur MariaDB, DATETIME au lieu de DATETIME(6) : la microseconde est
        # perdue sur ce seul backend, PostgreSQL et SQL Server la conservent.
        # L'ordre des evenements d'une meme seconde reste departage par la PK.
        assert re.search(
            r"\breceived_at\s+DATETIME\s+NOT\s+NULL",
            migration_text,
            flags=re.IGNORECASE,
        ), "received_at doit être un datetime NOT NULL"


# ── DDL — index ─────────────────────────────────────────────────────────────


class TestIndexes:
    def test_site_device_index_present(self, migration_text):
        assert re.search(
            r"INDEX\s+idx_iot_events_site_device\s*\(\s*site\s*,\s*device_id\s*\)",
            migration_text,
            flags=re.IGNORECASE,
        ), "Index (site, device_id) attendu"

    def test_received_at_index_present(self, migration_text):
        assert re.search(
            r"INDEX\s+idx_iot_events_received_at\s*\(\s*received_at\s*\)",
            migration_text,
            flags=re.IGNORECASE,
        ), "Index (received_at) attendu"


# ── Garde-fous périmètre ───────────────────────────────────────────────────


class TestNoUniqueOrDedupConstraint:
    """Pas de contrainte d'unicité à ce ticket (hors périmètre)."""

    def test_no_unique_constraint(self, migration_text):
        assert "UNIQUE" not in migration_text.upper(), (
            "Aucune contrainte UNIQUE à ce ticket — déduplication "
            "potentielle reportée"
        )


class TestStorageModuleStaysPure:
    """Le ticket migration ne doit pas relancer un branchement DB
    dans le module storage."""

    def test_storage_module_does_not_import_db(self):
        text = STORAGE_MODULE_FILE.read_text(encoding="utf-8")
        import_lines = [
            line for line in text.splitlines()
            if line.lstrip().startswith(("import ", "from "))
        ]
        # `core.database.timestamps` est écarté : il n'importe que la
        # bibliothèque standard, et ne porte donc aucun couplage à la base.
        # L'exemption est bornée par
        # `test_l_exemption_timestamps_ne_peut_pas_s_elargir`, qui vérifie que
        # ce module reste sans dépendance.
        offenders = [
            line for line in import_lines
            if ("core.database" in line and "core.database.timestamps" not in line)
            or "mariadb" in line
        ]
        assert not offenders, (
            "storage/events.py ne doit pas importer de connecteur DB "
            f"à ce ticket : {offenders}"
        )


# ── Cohérence migration ↔ contrat Python ────────────────────────────────────


class TestMigrationMirrorsPythonContract:
    """Les colonnes du DDL doivent exactement matcher COLUMNS de events.py."""

    def test_columns_match_python_contract(self, migration_text):
        # Extrait la liste des colonnes du DDL (entre CREATE TABLE et
        # le premier ')') puis filtre les lignes qui commencent par un
        # nom de colonne minuscule.
        body_match = re.search(
            r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+iot_events\s*\((.*?)\)\s*ENGINE",
            migration_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        assert body_match is not None, "Corps du CREATE TABLE introuvable"
        body = body_match.group(1)

        declared: list[str] = []
        for line in body.splitlines():
            stripped = line.strip().rstrip(",")
            # Ignorer les lignes vides, les PRIMARY KEY et les INDEX.
            if not stripped:
                continue
            head = stripped.split()[0]
            if head.upper() in {"PRIMARY", "INDEX", "KEY", "UNIQUE", "CONSTRAINT"}:
                continue
            declared.append(head)

        # On exige : id en premier, puis exactement COLUMNS dans l'ordre.
        assert declared[0] == "id", (
            f"Première colonne attendue : id (vu : {declared[0]!r})"
        )
        assert tuple(declared[1:]) == COLUMNS, (
            f"Colonnes hors id attendues : {COLUMNS}, "
            f"vues : {tuple(declared[1:])}"
        )
