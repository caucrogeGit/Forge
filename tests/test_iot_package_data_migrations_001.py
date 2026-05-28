"""Tests d'empaquetage des migrations IoT — IOT-PACKAGE-DATA-MIGRATIONS-001.

Vérifie que :

- les migrations vivent désormais sous ``forge_mvc_iot/migrations/``
  (sous-package Python) ;
- l'ancien chemin externe ``packages/forge-mvc-iot/migrations/`` a
  bien été supprimé (test d'absence — convention CLAUDE.md) ;
- ``pyproject.toml`` déclare ``migrations/*.sql`` dans
  ``[tool.setuptools.package-data]`` ;
- ``importlib.resources.files("forge_mvc_iot")`` permet d'accéder à
  la migration et d'en lire le contenu — fonctionne identiquement en
  install éditable et en install PyPI ;
- la documentation ne pointe plus vers l'ancien chemin externe ;
- le doctor (``IOT-DOCTOR-001``) trouve toujours la migration.

Aucun ``python -m build`` n'est lancé ici (trop lent pour la suite de
tests) ; la commande est documentée dans la roadmap et reste à
exécuter manuellement avant publication PyPI.
"""

from __future__ import annotations

import tomllib
from importlib import resources
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
IOT_PKG_DIR = PROJECT_ROOT / "packages" / "forge-mvc-iot"
PYPROJECT = IOT_PKG_DIR / "pyproject.toml"

NEW_MIGRATIONS_DIR = IOT_PKG_DIR / "forge_mvc_iot" / "migrations"
LEGACY_MIGRATIONS_DIR = IOT_PKG_DIR / "migrations"
EXPECTED_FILENAME = "20260528120000_create_iot_events.sql"

DOC_STORAGE = PROJECT_ROOT / "docs" / "iot" / "storage-events.md"
DOC_DOCTOR = PROJECT_ROOT / "docs" / "iot" / "doctor.md"


@pytest.fixture(scope="module")
def pyproject_data() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


# ── Nouvelle location ──────────────────────────────────────────────────────


class TestNewLocation:
    def test_migration_at_new_path(self):
        target = NEW_MIGRATIONS_DIR / EXPECTED_FILENAME
        assert target.exists(), (
            f"Migration introuvable à la nouvelle localisation : "
            f"{target.relative_to(PROJECT_ROOT)}"
        )

    def test_migrations_subpackage_has_init(self):
        # __init__.py rend `forge_mvc_iot.migrations` un vrai sous-package
        # Python — pratique pour importlib.resources et la découverte
        # par setuptools.
        init = NEW_MIGRATIONS_DIR / "__init__.py"
        assert init.exists(), (
            f"Le sous-package doit avoir un __init__.py "
            f"({init.relative_to(PROJECT_ROOT)})"
        )

    def test_only_one_iot_events_migration(self):
        candidates = sorted(NEW_MIGRATIONS_DIR.glob("*_create_iot_events.sql"))
        assert len(candidates) == 1, (
            f"Attendu une seule migration create_iot_events, "
            f"trouvé : {[p.name for p in candidates]}"
        )


# ── Ancien chemin supprimé (test d'absence — CLAUDE.md §6) ─────────────────


class TestLegacyLocationRemoved:
    def test_legacy_dir_does_not_exist(self):
        assert not LEGACY_MIGRATIONS_DIR.exists(), (
            f"L'ancien dossier {LEGACY_MIGRATIONS_DIR.relative_to(PROJECT_ROOT)} "
            "doit avoir été supprimé — les migrations sont désormais "
            "sous forge_mvc_iot/migrations/ (ressources du package)."
        )

    def test_legacy_file_does_not_exist(self):
        legacy_file = LEGACY_MIGRATIONS_DIR / EXPECTED_FILENAME
        assert not legacy_file.exists()


# ── Déclaration package-data dans pyproject.toml ───────────────────────────


class TestPyprojectPackageData:
    def test_package_data_section_present(self, pyproject_data):
        package_data = (
            pyproject_data.get("tool", {})
            .get("setuptools", {})
            .get("package-data", {})
        )
        assert "forge_mvc_iot" in package_data, (
            "pyproject.toml doit déclarer [tool.setuptools.package-data] "
            "avec une entrée forge_mvc_iot"
        )

    def test_package_data_includes_migrations_sql(self, pyproject_data):
        entries = (
            pyproject_data["tool"]["setuptools"]["package-data"]["forge_mvc_iot"]
        )
        assert any("migrations" in pattern and "sql" in pattern for pattern in entries), (
            f"package-data doit inclure 'migrations/*.sql' (vu : {entries})"
        )


# ── Accès via importlib.resources ─────────────────────────────────────────


class TestImportlibResourcesAccess:
    """Le test critique du ticket : la migration doit être atteignable
    via importlib.resources, indépendamment du mode d'installation."""

    def test_migrations_anchor_is_dir(self):
        anchor = resources.files("forge_mvc_iot") / "migrations"
        assert anchor.is_dir(), (
            "resources.files('forge_mvc_iot') / 'migrations' doit pointer "
            "vers un dossier (sous-package Python ou ressource embarquée)"
        )

    def test_migration_file_is_readable(self):
        migration = (
            resources.files("forge_mvc_iot")
            / "migrations"
            / EXPECTED_FILENAME
        )
        assert migration.is_file(), (
            f"La migration {EXPECTED_FILENAME} doit être accessible "
            "via importlib.resources"
        )

    def test_migration_content_contains_ddl(self):
        migration = (
            resources.files("forge_mvc_iot")
            / "migrations"
            / EXPECTED_FILENAME
        )
        content = migration.read_text(encoding="utf-8")
        assert "CREATE TABLE IF NOT EXISTS iot_events" in content


# ── Doctor mis à jour ──────────────────────────────────────────────────────


class TestDoctorStillFindsMigration:
    """Le check du doctor (IOT-DOCTOR-001) doit retourner OK après le
    déplacement — il utilise désormais importlib.resources."""

    def test_doctor_migration_check_ok(self):
        from forge_mvc_iot.cli.doctor import check_migration_present

        result = check_migration_present()
        assert result.status == "ok", (
            f"Le doctor doit trouver la migration ; détail : {result.detail}"
        )
        assert EXPECTED_FILENAME in result.detail

    def test_doctor_no_longer_walks_filesystem_parent(self):
        # Le doctor a abandonné le path-traversal `__file__.parent.parent`
        # au profit de importlib.resources — garde-fou textuel pour
        # éviter une régression accidentelle.
        from forge_mvc_iot.cli import doctor as doctor_module
        src = Path(doctor_module.__file__).read_text(encoding="utf-8")
        assert "_find_iot_package_root" not in src, (
            "L'ancien helper de traversée filesystem doit avoir été "
            "supprimé au profit d'importlib.resources"
        )
        assert "importlib" in src or "resources" in src, (
            "Le doctor doit utiliser importlib.resources pour localiser "
            "la migration"
        )


# ── Documentation à jour ───────────────────────────────────────────────────


class TestDocumentationUpdated:
    """Les pages de doc ne doivent plus pointer vers le chemin externe."""

    def test_storage_doc_does_not_reference_legacy_path(self):
        text = DOC_STORAGE.read_text(encoding="utf-8")
        # On cherche la chaîne exacte de l'ancien chemin.
        legacy = "packages/forge-mvc-iot/migrations/"
        assert legacy not in text, (
            f"docs/iot/storage-events.md référence encore l'ancien chemin "
            f"{legacy!r}"
        )

    def test_doctor_doc_does_not_reference_legacy_path(self):
        text = DOC_DOCTOR.read_text(encoding="utf-8")
        legacy = "packages/forge-mvc-iot/migrations/"
        assert legacy not in text

    def test_storage_doc_mentions_new_path_or_resource(self):
        text = DOC_STORAGE.read_text(encoding="utf-8")
        # Au moins une forme du nouveau chemin doit apparaître.
        markers = (
            "forge_mvc_iot/migrations/",
            "importlib.resources",
            "package-data",
            "ressource",
        )
        assert any(m in text for m in markers), (
            "La page storage doit décrire la nouvelle localisation "
            "des migrations (chemin package, importlib.resources, ou "
            "package-data)"
        )


# ── Sanity : insertion repository toujours alignée ─────────────────────────


class TestRepositoryStillAligned:
    """La constante COLUMNS et le SQL INSERT n'ont pas changé."""

    def test_columns_unchanged(self):
        from forge_mvc_iot.storage.events import COLUMNS, TABLE_NAME

        assert TABLE_NAME == "iot_events"
        assert COLUMNS == (
            "site",
            "device_id",
            "kind",
            "value",
            "unit",
            "timestamp",
            "metadata_json",
            "received_at",
        )
